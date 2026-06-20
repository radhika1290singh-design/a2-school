# A2 School — Database Spec: `users` table (v1)

## Purpose
Single shared table for all account types: super_admin, school_admin,
teacher, student. One table, differentiated by `role`, rather than separate
tables per role — this is the standard pattern for shared auth fields
(phone, password, status) while role-specific data (which class a teacher
teaches, which section a student is in) lives in separate tables that
reference `users.id`.

## Table: `users`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, primary key | Use UUID not auto-increment int — safer for multi-tenant systems, avoids exposing sequential IDs across schools, fine for Postgres performance at this scale |
| `school_id` | UUID, foreign key → `schools.id`, **nullable** | Nullable ONLY for `super_admin` (platform owner, not tied to one school). Every other role MUST have this set. |
| `role` | enum: `super_admin`, `school_admin`, `teacher`, `student` | Determines permissions; enforced at app layer, not just DB |
| `phone_number` | text, **not globally unique** — unique only within `(school_id, phone_number)` | Two different schools could have overlapping phone numbers; uniqueness is tenant-scoped, not global. `super_admin` rows (no school_id) must be globally unique among themselves. |
| `password_hash` | text, **nullable** | Null while status = `pending` (no password set yet, per auth-spec). Always hashed (bcrypt/argon2), never plaintext. |
| `status` | enum: `pending`, `active` | `pending` = phone registered but not yet OTP-activated. `active` = password set, can log in. |
| `created_by_user_id` | UUID, foreign key → `users.id`, nullable | Records who provisioned this account (admin who added a teacher, teacher who added a student). Null only for the very first `super_admin`-created `school_admin`, or super_admin itself. This is what gives us the provisioning chain from auth-spec. |
| `full_name` | text | Display name |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

## Why NOT separate tables per role
We could have `admins`, `teachers`, `students` as entirely separate tables,
each with their own auth fields. Rejected because:
- Login logic would need to check three tables to find a matching phone —
  more complex, more error-prone.
- Shared fields (phone, password, status, activation flow) are identical
  across all roles per auth-spec — duplicating them three times invites
  drift/bugs.
- Role-specific data (teacher's section, student's enrollment) still gets
  its OWN table either way — that part isn't avoided by merging auth, it's
  just kept separate from auth concerns, which is the cleaner split.

## Constraints & rules to enforce
- `UNIQUE (school_id, phone_number)` — composite uniqueness, not on
  `phone_number` alone.
- `super_admin` rows: `school_id` must be NULL (enforced via app logic or a
  DB check constraint).
- All non-`super_admin` rows: `school_id` must NOT be NULL.
- `password_hash` is NULL only when `status = 'pending'`. Once `active`, it
  must always be set (enforced at app layer during the activation flow).
- Row-Level Security (RLS) policy: a request scoped to `school_id = X` can
  only see/modify users where `users.school_id = X` (or the requester is
  `super_admin`). This is the core multi-tenant isolation mechanism from
  CLAUDE.md.

## What this table does NOT contain (lives elsewhere, references this table)
- Which class/section a teacher teaches → separate `teachers` or
  `class_assignments` table, references `users.id`
- Which class/section/year a student is enrolled in → `enrollments` table
  (per academic-structure-spec.md), references `users.id`
- OTP codes themselves (temporary, expiring) → likely a separate
  `otp_requests` table or even just an in-memory/cache store (Redis) since
  OTPs are short-lived and don't need permanent history — open question,
  see below.

## OTP storage (confirmed)
OTP codes are stored in a dedicated `otp_requests` table — not Redis/cache.
Simplest option, zero new infrastructure, fully adequate at pilot scale.
Revisit only if OTP volume becomes a genuine bottleneck later.

### Table: `otp_requests`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, primary key | |
| `school_id` | UUID, foreign key → `schools.id`, nullable | Nullable only for super_admin activation flows |
| `phone_number` | text | Matches the phone being activated/reset |
| `code_hash` | text | OTP code, hashed — never store plaintext |
| `purpose` | enum: `activation`, `password_reset` | Distinguishes the two flows from auth-spec.md |
| `expires_at` | timestamp | Short-lived, e.g. 5-10 minutes from creation |
| `used` | boolean, default false | Set true once successfully verified — prevents replay |
| `created_at` | timestamp | |

A new OTP request invalidates any prior unused OTP for the same
`(school_id, phone_number, purpose)` — only the most recent code is valid at
any time.

