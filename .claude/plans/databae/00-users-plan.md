# Plan: `users` + `otp_requests` tables — from 00-users-spec.md

## Context
Single shared table for all account types (super_admin, school_admin, teacher, student),
differentiated by `role`. Phone-based auth with OTP activation flow. The old `users` table
(integer PK, email-based) was dropped and rebuilt from scratch. `otp_requests` is new.

## Status: DONE ✓

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/models/user.py` | `User` ORM model + `UserRole` / `UserStatus` enums |
| `backend/app/models/otp_request.py` | `OtpRequest` ORM model + `OtpPurpose` enum |
| `backend/alembic/versions/0002_recreate_users_add_otp_requests.py` | Migration — drops old users, recreates per spec, creates otp_requests |
| `backend/alembic/env.py` | Updated — imports user + otp_request models |

---

## Schema

```
users
├── id                    UUID, PK
├── school_id             UUID, FK → schools.id ON DELETE CASCADE, nullable (super_admin only)
├── role                  enum(super_admin, school_admin, teacher, student), NOT NULL
├── phone_number          text, NOT NULL
├── password_hash         text, nullable (null while status = pending)
├── status                enum(pending, active), NOT NULL, default 'pending'
├── created_by_user_id    UUID, FK → users.id, nullable (self-referential, no cascade)
├── full_name             text, NOT NULL
├── created_at            timestamptz, default now()
└── updated_at            timestamptz, default now()

otp_requests
├── id            UUID, PK
├── school_id     UUID, FK → schools.id ON DELETE CASCADE, nullable
├── phone_number  text, NOT NULL
├── code_hash     text, NOT NULL (hashed, never plaintext)
├── purpose       enum(activation, password_reset), NOT NULL
├── expires_at    timestamptz, NOT NULL
├── used          boolean, NOT NULL, default false
└── created_at    timestamptz, default now()
```

## Constraints
- `uq_users_school_phone` — UNIQUE(school_id, phone_number) — tenant-scoped uniqueness
- `ck_super_admin_no_school` — super_admin must have school_id IS NULL
- `ck_non_super_admin_has_school` — all other roles must have school_id NOT NULL
- `password_hash` nullable — allows pending state before OTP activation

## PG Types Created
- `user_status` — pending, active
- `otp_purpose` — activation, password_reset
- `role` — reused (already existed): super_admin, school_admin, teacher, student

## Notes
- OTP invalidation (most-recent-only rule) enforced at app layer, not DB
- RLS policies deferred until FastAPI layer is built
