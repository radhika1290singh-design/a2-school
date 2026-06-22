# API Code Flow — How a Request Travels Through the Codebase

Traced end-to-end using `POST /api/v1/auth/login` as the example.
The same layered pattern applies to every endpoint.

---

## File roles at a glance

```
main.py                  ← HTTP server entry point, registers all routers
│
app/routers/auth.py      ← Endpoint functions (what URL does what)
│
app/schemas/auth.py      ← Shape of request body and response (Pydantic)
│
app/core/security.py     ← Password check, JWT create/decode
app/services/sms.py      ← Send OTP (console print in dev, MSG91 in prod)
│
app/dependencies/auth.py ← Reusable FastAPI Depends() helpers
│                           (get_current_user, get_sms_service)
│
app/database.py          ← DB session (get_db)
app/models/user.py       ← User ORM model (maps to `users` table)
app/models/school.py     ← School ORM model (maps to `schools` table)
app/models/otp_request.py← OtpRequest ORM model
│
app/core/config.py       ← Reads .env (JWT secret, SMS mode, DB URL)
```

---

## Step-by-step: `POST /api/v1/auth/login`

```
Client
  │
  │  POST /api/v1/auth/login
  │  Body: { subdomain, phone_number, password }
  ▼
main.py
  app = FastAPI()
  app.include_router(auth_router)   ← registers all /api/v1/auth/* routes
  │
  ▼
app/routers/auth.py  →  async def login(body: LoginRequest, db: AsyncSession)
  │
  │  1. FastAPI reads the request body
  │     validates it against LoginRequest (app/schemas/auth.py)
  │     → if missing field or wrong type → 422 auto-returned before login() runs
  │
  │  2. FastAPI calls Depends(get_db)  (app/database.py)
  │     → opens an async SQLAlchemy session, yields it as `db`
  │
  │  3. login() calls _get_active_school(body.subdomain, db)
  │     → SELECT * FROM schools WHERE subdomain = ? AND status = 'active'
  │     → 404 if not found or suspended
  │
  │  4. login() calls _get_user_by_phone(school.id, body.phone_number, db)
  │     → SELECT * FROM users WHERE school_id = ? AND phone_number = ?
  │     → 404 if not found
  │
  │  5. login() checks user.status == pending
  │     → 403 if not yet activated
  │
  │  6. login() calls verify_password(body.password, user.password_hash)
  │                              ↑
  │                    app/core/security.py
  │                    (uses passlib bcrypt)
  │     → 401 if wrong (generic error, no detail on which field failed)
  │
  │  7. login() calls create_access_token(user.id, school.id, role, subdomain)
  │                              ↑
  │                    app/core/security.py
  │                    reads JWT_SECRET_KEY from app/core/config.py
  │                    which reads it from .env
  │
  │  8. login() builds TokenResponse (app/schemas/auth.py)
  │     → { access_token, token_type: "bearer", user: { id, full_name, role, ... } }
  │
  ▼
Client receives 200 + JSON
```

---

## How a protected endpoint works: `GET /api/v1/auth/me`

```
Client
  │  GET /api/v1/auth/me
  │  Header: Authorization: Bearer <token>
  ▼
app/routers/auth.py  →  async def me(current_user: User = Depends(get_current_user), ...)
  │
  │  FastAPI sees Depends(get_current_user)
  │  → calls app/dependencies/auth.py → get_current_user()
  │       │
  │       │  1. Extracts token from Authorization header
  │       │     (via OAuth2PasswordBearer, also in app/dependencies/auth.py)
  │       │
  │       │  2. Calls decode_access_token(token)
  │       │            ↑
  │       │     app/core/security.py
  │       │     decodes JWT with JWT_SECRET_KEY from app/core/config.py
  │       │     → 401 if invalid or expired
  │       │
  │       │  3. Loads User from DB using user_id from token payload
  │       │     → 401 if user deleted since token was issued
  │       │
  │       └─ returns User object
  │
  │  me() receives current_user: User already fetched and verified
  │  me() does: await db.get(School, current_user.school_id)
  │  me() builds MeResponse (app/schemas/auth.py)
  │     → user fields + school branding fields
  │
  ▼
Client receives 200 + JSON
```

---

## How an OTP endpoint works: `POST /api/v1/auth/send-otp`

```
app/routers/auth.py  →  async def send_otp(body, db, sms: SMSService = Depends(get_sms_service))
  │
  │  FastAPI sees Depends(get_sms_service)
  │  → calls app/dependencies/auth.py → get_sms_service()
  │       reads settings.SMS_MODE from app/core/config.py (.env)
  │       → returns ConsoleSMSService()  if SMS_MODE=console
  │       → returns MSG91SMSService()    if SMS_MODE=msg91
  │
  │  send_otp() validates school + user + status checks
  │
  │  send_otp() calls _generate_and_store_otp(school.id, phone, purpose, db)
  │       1. UPDATE otp_requests SET used=true WHERE ... (invalidates old OTPs)
  │       2. generates random 6-digit string
  │       3. hashes it via hash_password()  ← app/core/security.py
  │       4. INSERT new OtpRequest row       ← app/models/otp_request.py
  │       5. returns the plain OTP string
  │
  │  await db.commit()   ← persists to DB
  │
  │  await sms.send_otp(phone_number, otp_code)
  │       ConsoleSMSService → print("[DEV OTP] Phone: ... | OTP: ...")
  │       MSG91SMSService   → HTTP call to MSG91 API (not yet implemented)
  │
  ▼
Client receives 200 { "message": "OTP sent successfully" }
OTP visible in server terminal (dev mode)
```

---

## Dependency injection map

FastAPI resolves `Depends()` automatically before calling the endpoint function.

```
Endpoint function parameter          Resolved by
─────────────────────────────────────────────────────────────
db: AsyncSession = Depends(get_db)   app/database.py → get_db()
                                     opens async SQLAlchemy session

sms: SMSService = Depends(get_sms_service)
                                     app/dependencies/auth.py → get_sms_service()
                                     reads SMS_MODE from config

current_user: User = Depends(get_current_user)
                                     app/dependencies/auth.py → get_current_user()
                                     extracts + validates JWT, loads User from DB
```

---

## Config / .env read order

```
.env file
  └─ read by app/core/config.py (pydantic-settings BaseSettings)
       └─ imported as `settings` singleton
            ├─ app/core/security.py   uses settings.JWT_SECRET_KEY
            ├─ app/dependencies/auth.py  uses settings.SMS_MODE
            └─ app/database.py        uses settings.DATABASE_URL (via os.environ)
```

---

## File responsibility summary

| File | Owns |
|------|------|
| `main.py` | Boot the app, plug in routers |
| `app/routers/auth.py` | Endpoint logic, HTTP status codes, orchestration |
| `app/schemas/auth.py` | What goes in / what comes out (Pydantic validation) |
| `app/core/security.py` | Crypto — bcrypt hashing, JWT sign/verify, password rules |
| `app/services/sms.py` | External side-effect — sending OTP via SMS |
| `app/dependencies/auth.py` | Reusable `Depends()` — auth guard, SMS factory |
| `app/core/config.py` | Single source for all env vars |
| `app/database.py` | DB engine, session factory, `get_db` dependency |
| `app/models/*.py` | ORM table definitions — used in SELECT/INSERT/UPDATE |
