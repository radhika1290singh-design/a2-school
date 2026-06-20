# Plan: `schools` table — from 01-schools-spec.md

## Context
`schools` is the tenant root. Every other tenant-owned table references `schools.id`
via `school_id`. Created by `super_admin` when onboarding a new school client.

## Status: DONE ✓

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/database.py` | `Base`, async engine, `get_db` |
| `backend/app/models/school.py` | `School` ORM model + `FeeBillingCycle` / `SchoolStatus` enums |
| `backend/alembic/versions/0001_create_schools_table.py` | Migration — creates `schools` table |
| `backend/alembic/env.py` | Updated — async migration support, wired to `Base.metadata` |

---

## Schema

```
schools
├── id                UUID, PK
├── name              text, NOT NULL
├── subdomain         text, NOT NULL, UNIQUE
├── custom_domain     text, nullable, UNIQUE
├── logo_url          text, nullable
├── primary_color     text, nullable
├── secondary_color   text, nullable
├── fee_billing_cycle enum(monthly, quarterly, yearly), nullable
├── status            enum(active, suspended), NOT NULL, default 'active'
├── created_at        timestamptz, default now()
└── updated_at        timestamptz, default now()
```

## Constraints
- `uq_schools_subdomain` — platform-wide tenant boundary, immutable after creation
- `uq_schools_custom_domain`
- No FK from `schools` to any other table — it is the root

## PG Types Created
- `fee_billing_cycle` — monthly, quarterly, yearly
- `school_status` — active, suspended
