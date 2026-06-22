# Plan: API Spec 01 — Auth Endpoints

## Context
First API implementation (Phase 2). The database schema is fully migrated (0013).
This plan implements 7 auth endpoints under `/api/v1/auth` using the existing
`users`, `otp_requests`, and `schools` models. Everything in `app/` beyond
`models/` and `database.py` is new — no routers, schemas, or entry point exist yet.

Installed packages already available: `fastapi`, `pydantic v2`, `sqlalchemy 2.0 async`,
`python-jose`, `passlib[bcrypt]`, `uvicorn`, `pydantic-settings`.

---

## New directory structure to create

```
backend/
├── main.py                          ← FastAPI app entry point
└── app/
    ├── core/
    │   ├── __init__.py
    │   ├── config.py                ← Settings via pydantic-settings
    │   └── security.py             ← hash_password, verify_password, create_token, decode_token
    ├── services/
    │   ├── __init__.py
    │   └── sms.py                  ← SMSService ABC + ConsoleSMSService + MSG91SMSService stub
    ├── schemas/
    │   ├── __init__.py
    │   └── auth.py                 ← Pydantic v2 request/response schemas
    ├── dependencies/
    │   ├── __init__.py
    │   └── auth.py                 ← get_current_user, get_sms_service
    └── routers/
        ├── __init__.py
        └── auth.py                 ← all 7 endpoints
```

Also save the final plan file to `backend/.claude/plans/api/01-api-auth-plan.md`.

---

## Migration 0014 — add `attempt_count` to `otp_requests`

The spec requires "max 3 OTP attempts before invalidation" (app-layer). The existing
`otp_requests` table has no attempt counter. Add one:

```python
# 0014_add_attempt_count_to_otp_requests.py
# revision = "0014", down_revision = "0013"

def upgrade():
    op.add_column("otp_requests",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0")
    )

def downgrade():
    op.drop_column("otp_requests", "attempt_count")
```

Also add `attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))`
to `backend/app/models/otp_request.py`.

---

## .env additions needed

```
# Replace existing SECRET_KEY / ACCESS_TOKEN_EXPIRE_MINUTES with:
JWT_SECRET_KEY=<long-random-string>
JWT_EXPIRE_HOURS=24

# SMS
SMS_MODE=console          # dev; change to msg91 for prod
MSG91_API_KEY=
MSG91_SENDER_ID=
MSG91_DLT_TEMPLATE_ID=
```

---

## 1. `app/core/config.py` — Settings

Use `pydantic-settings` `BaseSettings` to read from `.env`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    SMS_MODE: str = "console"
    MSG91_API_KEY: str = ""
    MSG91_SENDER_ID: str = ""
    MSG91_DLT_TEMPLATE_ID: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 2. `app/core/security.py` — Password + JWT

```python
# passlib for password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...

# python-jose for JWT
from jose import jwt, JWTError
from app.core.config import settings

def create_access_token(user_id, school_id, role, subdomain) -> str:
    # payload: sub=user_id, school_id, role, subdomain, exp=now+JWT_EXPIRE_HOURS
    ...

def decode_access_token(token: str) -> dict:
    # raises HTTPException 401 on failure
    ...
```

Password validation (used in activate + reset-password):
```python
def validate_password_strength(password: str) -> None:
    # min 8 chars, at least one letter, at least one digit
    # raises ValueError if invalid
```

---

## 3. `app/services/sms.py` — SMS abstraction

```python
from abc import ABC, abstractmethod

class SMSService(ABC):
    @abstractmethod
    async def send_otp(self, phone_number: str, otp_code: str) -> bool: ...

class ConsoleSMSService(SMSService):
    async def send_otp(self, phone_number, otp_code):
        print(f"[DEV OTP] Phone: {phone_number} | OTP: {otp_code}")
        return True

class MSG91SMSService(SMSService):
    async def send_otp(self, phone_number, otp_code):
        # TODO: implement when DLT approved
        raise NotImplementedError
```

---

## 4. `app/schemas/auth.py` — Pydantic v2 schemas

Request schemas (all use `model_config = ConfigDict(str_strip_whitespace=True)`):
- `SendOtpRequest`: `subdomain`, `phone_number`, `purpose: OtpPurpose`
- `ActivateRequest`: `subdomain`, `phone_number`, `otp_code`, `new_password`
- `LoginRequest`: `subdomain`, `phone_number`, `password`
- `ResetPasswordRequest`: `subdomain`, `phone_number`, `otp_code`, `new_password`
- `ChangePasswordRequest`: `current_password`, `new_password`
- `SuperAdminLoginRequest`: `phone_number`, `password`

Response schemas:
- `MessageResponse`: `message: str`
- `UserInfo`: `id`, `full_name`, `role`, `school_id | None`, `subdomain | None`
- `TokenResponse`: `access_token`, `token_type="bearer"`, `user: UserInfo`
- `MeResponse`: all UserInfo fields + `phone_number`, `status`, `school_name`, `school_logo_url`, `school_primary_color`, `school_secondary_color`

---

## 5. `app/dependencies/auth.py` — Reusable dependencies

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)   # raises 401 if invalid
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(401)
    return user

def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403)
        return user
    return checker

async def get_sms_service() -> SMSService:
    if settings.SMS_MODE == "msg91":
        return MSG91SMSService()
    return ConsoleSMSService()
```

---

## 6. `app/routers/auth.py` — 7 endpoints

All under `router = APIRouter(prefix="/api/v1/auth", tags=["auth"])`.

### Shared helper functions (inside the router module)

```python
async def _get_active_school(subdomain: str, db) -> School:
    # SELECT * FROM schools WHERE subdomain=subdomain AND status='active'
    # raises 404 if not found or suspended

async def _get_user_by_phone(school_id, phone_number, db) -> User:
    # SELECT * FROM users WHERE school_id=school_id AND phone_number=phone_number
    # raises 404 if not found

async def _generate_and_store_otp(school_id, phone_number, purpose, db) -> str:
    # 1. Mark prior unused OTPs as used (same school_id, phone_number, purpose)
    # 2. Generate 6-digit OTP string
    # 3. Hash with bcrypt (use pwd_context)
    # 4. Insert new OtpRequest(school_id, phone_number, code_hash, purpose,
    #    expires_at=now+10min, used=False, attempt_count=0)
    # return plain OTP string

async def _verify_otp(school_id, phone_number, purpose, otp_code, db) -> OtpRequest:
    # 1. Find latest unused, unexpired OTP for (school_id, phone_number, purpose)
    #    ORDER BY created_at DESC, LIMIT 1
    # 2. If not found: raise 400 "OTP expired or not found"
    # 3. verify_password(otp_code, otp_record.code_hash)
    # 4. If wrong: increment attempt_count; if attempt_count >= 3: mark used=True; raise 400
    # 5. If correct: return otp_record (caller marks used=True)
```

### Endpoints summary

| Method | Path | Auth | Logic |
|--------|------|------|-------|
| POST | `/send-otp` | None | get school → get user → status check → invalidate old OTPs → generate+store → SMS |
| POST | `/activate` | None | get school → pending user → verify OTP → hash password → set active → return JWT |
| POST | `/login` | None | get school → active user → verify password → return JWT |
| POST | `/reset-password` | None | get school → active user → verify OTP → hash new password → return message |
| POST | `/change-password` | JWT | verify current password → hash new → update |
| GET | `/me` | JWT | return user + school branding joined |
| POST | `/super-admin/login` | None | find user by phone only (no subdomain) → verify role=super_admin → return JWT |

### `/me` query
Needs a join to get school branding:
```python
result = await db.execute(
    select(User, School)
    .join(School, User.school_id == School.id)
    .where(User.id == current_user.id)
)
```

---

## 7. `main.py` — FastAPI entry point

```python
from fastapi import FastAPI
from app.routers.auth import router as auth_router

app = FastAPI(title="A2 School API")
app.include_router(auth_router)
```

---

## Verification

```bash
cd backend
uvicorn main:app --reload
```

Then test each endpoint:
```bash
# Check docs
open http://localhost:8000/docs

# Send OTP (console mode — OTP printed to terminal)
curl -X POST http://localhost:8000/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"subdomain":"test","phone_number":"9999999999","purpose":"activation"}'

# Activate account (use OTP from terminal)
curl -X POST http://localhost:8000/api/v1/auth/activate \
  -d '{"subdomain":"test","phone_number":"9999999999","otp_code":"123456","new_password":"Test1234"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"subdomain":"test","phone_number":"9999999999","password":"Test1234"}'

# Me (use token from login)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```
