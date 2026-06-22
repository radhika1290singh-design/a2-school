# A2 School — API Spec 01: Auth Endpoints

## Base URL
All endpoints prefixed with `/api/v1/auth`

## SMS Provider
**Chosen provider: MSG91** (for production)
**Development: terminal/console placeholder** — OTP is printed to the
terminal log, no real SMS sent. This lets development and testing work
fully without DLT registration or wallet balance.

Abstract behind a `SMSService` interface so swapping dev→production
requires changing only the service implementation, not any endpoint logic.

### SMSService interface
```python
class SMSService:
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        raise NotImplementedError
```

### Dev implementation (use this now)
```python
class ConsoleSMSService(SMSService):
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        print(f"[DEV OTP] Phone: {phone_number} | OTP: {otp_code}")
        return True
```

### MSG91 implementation (build stub, fill in when DLT approved)
```python
class MSG91SMSService(SMSService):
    # Uses MSG91 API key + approved DLT sender ID + template ID
    # Reads from .env: MSG91_API_KEY, MSG91_SENDER_ID, MSG91_DLT_TEMPLATE_ID
    # Implement when DLT registration is complete
    pass
```

### Switching between dev and production
Controlled by a single `.env` variable:
```
SMS_MODE=console        # development — prints to terminal
SMS_MODE=msg91          # production — sends real SMS via MSG91
```
FastAPI startup reads `SMS_MODE` and injects the right implementation
via dependency injection. No endpoint code changes needed when switching.

## OTP Rules (applies to all flows)
- OTP is 6 digits, randomly generated
- Expires in 10 minutes
- Stored hashed (bcrypt) in `otp_requests` table
- A new OTP request for the same (school_id, phone_number, purpose)
  invalidates all prior unused OTPs for that combination
- Max 3 OTP attempts before the code is invalidated (app-layer,
  prevents brute force)

## JWT Rules
- Access token: expires in 24 hours
- Payload contains: user_id, school_id, role, subdomain
- All protected endpoints validate JWT and extract school_id from it
  for tenant scoping — never trust school_id from request body

---

## Endpoints

---

### POST `/api/v1/auth/send-otp`
Sends an OTP to a pre-registered phone number.
Works for both activation (pending users) and password reset (active users).

**Request body**
```json
{
  "subdomain": "oakwood",
  "phone_number": "9876543210",
  "purpose": "activation" | "password_reset"
}
```

**Logic**
1. Look up school by `subdomain` — return 404 if not found or suspended
2. Look up user by `(school_id, phone_number)` — return 404 if not found
3. For `purpose = "activation"`: user must be `status = "pending"` —
   return 400 if already active
4. For `purpose = "password_reset"`: user must be `status = "active"` —
   return 400 if still pending
5. Invalidate any prior unused OTPs for same (school_id, phone_number, purpose)
6. Generate 6-digit OTP, hash it, store in `otp_requests` with 10 min expiry
7. Send OTP via SMSService
8. Return success (never reveal whether phone exists — same response
   either way for security)

**Response 200**
```json
{
  "message": "OTP sent successfully"
}
```

**Errors**
- 404: school not found or suspended
- 400: wrong status for the requested purpose
- 500: SMS delivery failed

---

### POST `/api/v1/auth/activate`
Verifies OTP and sets password for a pending user (first-time activation).

**Request body**
```json
{
  "subdomain": "oakwood",
  "phone_number": "9876543210",
  "otp_code": "123456",
  "new_password": "SecurePass123"
}
```

**Logic**
1. Look up school by `subdomain`
2. Look up user by `(school_id, phone_number)` — must be `status = "pending"`
3. Find latest unused, unexpired OTP for (school_id, phone_number, "activation")
4. Verify `otp_code` against stored `code_hash`
5. If invalid: increment attempt count, return 400. If 3 failed attempts,
   mark OTP as used/invalidated.
6. If valid:
   - Hash `new_password`, set on user
   - Set `user.status = "active"`
   - Mark OTP `used = true`
   - Return JWT access token (user is now logged in immediately)

**Password rules** (app-layer validation)
- Minimum 8 characters
- At least one number
- At least one letter

**Response 200**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "full_name": "John Doe",
    "role": "teacher",
    "school_id": "<uuid>",
    "subdomain": "oakwood"
  }
}
```

**Errors**
- 404: school or user not found
- 400: user already active, OTP invalid/expired, password too weak

---

### POST `/api/v1/auth/login`
Standard login for active users.

**Request body**
```json
{
  "subdomain": "oakwood",
  "phone_number": "9876543210",
  "password": "SecurePass123"
}
```

**Logic**
1. Look up school by `subdomain` — 404 if not found or suspended
2. Look up user by `(school_id, phone_number)` — 404 if not found
3. Check `user.status = "active"` — 403 if pending (not yet activated)
4. Verify password against `password_hash`
5. If valid: return JWT
6. If invalid: return 401 (do NOT reveal whether phone or password
   was wrong — same generic error for both)

**Response 200**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "full_name": "John Doe",
    "role": "school_admin" | "teacher" | "student",
    "school_id": "<uuid>",
    "subdomain": "oakwood"
  }
}
```

**Errors**
- 404: school not found or suspended
- 403: account not yet activated
- 401: invalid credentials (generic, no specifics)

---

### POST `/api/v1/auth/reset-password`
Verifies OTP and sets a new password for an active user.
Same flow as activation but for already-active accounts.

**Request body**
```json
{
  "subdomain": "oakwood",
  "phone_number": "9876543210",
  "otp_code": "123456",
  "new_password": "NewSecurePass123"
}
```

**Logic**
1. Look up school by `subdomain`
2. Look up user by `(school_id, phone_number)` — must be `status = "active"`
3. Find latest unused, unexpired OTP for (school_id, phone_number, "password_reset")
4. Verify OTP (same 3-attempt rule as activation)
5. If valid:
   - Hash `new_password`, update `user.password_hash`
   - Mark OTP `used = true`
   - Return success (do NOT auto-login after reset — user must log in fresh)

**Response 200**
```json
{
  "message": "Password reset successfully. Please log in."
}
```

**Errors**
- 404: school or user not found
- 400: user not active, OTP invalid/expired, password too weak

---

### POST `/api/v1/auth/change-password`
For logged-in users changing their own password from account settings.
Requires current password (not OTP).

**Headers**: `Authorization: Bearer <token>`

**Request body**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Logic**
1. Validate JWT, extract user_id
2. Verify `current_password` against stored hash
3. Hash `new_password`, update `user.password_hash`

**Response 200**
```json
{
  "message": "Password changed successfully"
}
```

**Errors**
- 401: invalid/expired token
- 400: current password wrong, new password too weak

---

### GET `/api/v1/auth/me`
Returns the current logged-in user's profile.
Used by both web and app to verify token and get user context.

**Headers**: `Authorization: Bearer <token>`

**Response 200**
```json
{
  "id": "<uuid>",
  "full_name": "John Doe",
  "phone_number": "9876543210",
  "role": "teacher",
  "status": "active",
  "school_id": "<uuid>",
  "subdomain": "oakwood",
  "school_name": "Oakwood International School",
  "school_logo_url": "https://...",
  "school_primary_color": "#1A73E8",
  "school_secondary_color": "#FBBC04"
}
```

Note: includes school branding fields — this is the single endpoint
the web/app calls after login to get everything needed to render the
themed UI. No separate branding endpoint needed.

**Errors**
- 401: invalid/expired token

---

## Super admin endpoint (platform owner only)

### POST `/api/v1/auth/super-admin/login`
Separate login for super_admin (you). Not school-scoped.

**Request body**
```json
{
  "phone_number": "9876543210",
  "password": "SuperAdminPass"
}
```

**Logic**
Same as `/login` but looks up user by phone_number globally
(no subdomain/school_id filter) and verifies `role = "super_admin"`.

**Response 200**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "<uuid>",
    "full_name": "Platform Admin",
    "role": "super_admin"
  }
}
```

---

## FastAPI implementation notes
- Use `Depends()` for a reusable `get_current_user` dependency that
  validates JWT and returns the current user object
- Use `Depends()` for role-based guards:
  `require_role("school_admin")`, `require_role("teacher")` etc.
- All school-scoped queries must filter by `school_id` extracted from
  the JWT — never from request body
- Password hashing: use `passlib` with `bcrypt` scheme
- JWT: use `python-jose` with `HS256`
- Store JWT secret in `.env` as `JWT_SECRET_KEY`
- SMS provider: inject via dependency, reads from `.env`

## .env variables needed for this spec
```
# JWT
JWT_SECRET_KEY=<long-random-string>
JWT_EXPIRE_HOURS=24

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/a2school_dev

# SMS
SMS_MODE=console                          # dev: prints OTP to terminal
                                          # prod: change to msg91
MSG91_API_KEY=<add-when-dlt-approved>
MSG91_SENDER_ID=<6-letter-code-e.g-A2SCHL>
MSG91_DLT_TEMPLATE_ID=<add-when-dlt-approved>
```
