# A2 School — Database Spec: `schools` table (v1)

## Purpose
This is the tenant root. Every other tenant-owned table (`users`, `classes`,
`enrollments`, `attendance`, `results`, `fee_periods`, etc.) traces back to a
row here via `school_id`. Created by `super_admin` (you) when onboarding a
new school client — this is literally "distributing the platform to a
school," per the original request.

## Table: `schools`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID, primary key | |
| `name` | text | Display name, e.g. "Oakwood International School" |
| `subdomain` | text, unique | e.g. `oakwood` → used in login identifier and (later) website routing. Lowercase, URL-safe, enforced at app layer (regex: alphanumeric + hyphens only) |
| `custom_domain` | text, unique, nullable | Optional — for schools wanting `app.oakwoodschool.com` instead of `oakwood.a2school.com`. Not needed for v1 launch, but cheap to include the column now |
| `logo_url` | text, nullable | Points to file in object storage (Cloudflare R2, per earlier plan). Nullable because a brand-new school may not have uploaded one yet |
| `primary_color` | text, nullable | Hex code, e.g. `#1A73E8`. Nullable → app falls back to a sensible default theme until admin sets it |
| `secondary_color` | text, nullable | Same reasoning as above |
| `fee_billing_cycle` | enum: `monthly`, `quarterly`, `yearly`, nullable | Per academic-structure-spec.md. Nullable until admin configures it — fee periods can't be generated until this is set |
| `status` | enum: `active`, `suspended` | Lets you (super_admin) disable a school's access — e.g. non-payment — without deleting their data |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

## Relationship to `users`
- `super_admin` creates the `schools` row first, THEN creates the
  `school_admin` user with `school_id` pointing here — matches the
  provisioning chain from auth-spec.md exactly (school must exist before
  its first admin can).

## Relationship to academic structure (forward reference)
- `academic_years`, `classes`, `sections` (next specs) will all reference
  `schools.id` directly — these are configured by `school_admin` AFTER the
  school and admin account both exist.

## Constraints & rules to enforce
- `subdomain` globally unique across the entire platform (not per-school —
  there's only one of these, it IS the tenant boundary).
- `subdomain` immutable after creation in v1 — changing it would break
  existing users' login identifier and any bookmarked URLs. (Open question
  below on whether this needs to be changeable later.)
- Only `super_admin` can create/suspend a `schools` row. `school_admin` can
  only edit their OWN school's branding fields (name, logo, colors) — not
  subdomain, not status.

## What this table does NOT contain
- Academic years → separate `academic_years` table (next in sequence)
- Fee AMOUNT per class → lives on `classes`, not here (this table only
  holds the billing CYCLE setting, which is school-wide)
- Admin contact info, address, etc. — not yet specified as a requirement;
  flagging as a possible future addition, not building speculatively now

## Subdomain mutability (confirmed)
`subdomain` is immutable via the application — no edit endpoint/UI for it,
not even for `super_admin` through normal app flows. In the rare case of a
typo or required correction, `super_admin` fixes it via direct database
access. No subdomain-change feature is built in v1.

