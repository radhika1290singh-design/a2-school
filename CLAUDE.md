# A2 School — Project Reference

## What this is
A2 School is a multi-tenant school management SaaS. One platform, distributed
to many different schools, each with their own branding (school name, logo,
colors) shown in both the web admin dashboard and the mobile app. Includes
a chatbot that answers questions using each school's own data.

The system has three parts, built in this fixed order:
1. `backend/` — FastAPI API + PostgreSQL database (build first)
2. `website/` — Admin dashboard (school admins manage students/teachers/branding)
3. `mobile/` — Flutter app for iOS + Android (single codebase, single app
   listing, re-themed at runtime per school after login)

Do not jump ahead to a later phase's concerns while working on an earlier one.

---

## Tech stack (confirmed, do not substitute without asking)
- **Backend language/framework**: Python, FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Database**: PostgreSQL 16 (local dev), pgvector extension for chatbot
  embeddings. Supabase planned as hosted DB later (Phase 6), not yet set up.
- **Local dev DB name**: `a2school_dev`
- **Auth**: JWT-based, role-based: `super_admin`, `school_admin`, `teacher`,
  `student`. (No `parent` role in v1 — explicitly deferred, see Feature Scope.)
- **Chatbot**: Anthropic Claude API + pgvector for RAG (retrieval-augmented
  generation) over each school's own info. Built in Phase 4, after core API.
- **Website/admin**: Next.js or React — framework choice not yet finalized,
  decide when Phase 3 starts.
- **Mobile**: Flutter (Dart), single codebase for iOS + Android.
- **Mobile distribution**: ONE app, ONE App Store / Play Store listing.
  No per-school app builds in v1.
- **Hosting (planned, not yet provisioned)**: Railway or Render for API,
  Supabase for DB, Cloudflare R2 for file storage, Codemagic for mobile CI/CD.

---

## Multi-tenancy approach
Shared database, shared schema. Every tenant-owned table has a `school_id`
foreign key. Tenant isolation is enforced via Postgres Row-Level Security
(RLS) plus a FastAPI dependency that resolves `school_id` from the JWT and
scopes every query automatically. This is the standard, cost-effective
pattern for SaaS at this scale — not schema-per-tenant or DB-per-tenant.

**Every tenant-owned table/query must be scoped by `school_id`.** Flag any
endpoint or query that touches tenant data without this scoping.

---

## Branding / white-labeling
Each school has: name, subdomain, logo_url, primary_color, secondary_color.
- Website: resolved by subdomain/custom domain.
- Mobile: user selects/enters their school at login; the app fetches that
  school's branding config from the API and re-themes itself at runtime.
  No per-school app builds unless a school explicitly requires their own
  home-screen icon later — that would be a deliberate scope change, not
  a default.

---

## Feature scope — v1 (confirmed)

### Roles
- `super_admin` — platform owner (you), manages schools onboarding
- `school_admin` — manages their school's students, teachers, classes,
  branding, posts events/holidays
- `teacher` — views their classes, marks attendance, enters term-end grades,
  views student leave applications
- `student` — views own attendance, report cards, events/holidays, submits
  leave applications, uses chatbot
- **No `parent` role in v1** — explicitly deferred to a later version.

### Core entities
- **Schools** (tenants) — name, subdomain, logo, colors, contact info
- **Users** — shared table, role-based, linked to `school_id`
- **Students** — profile, linked to a class/section
- **Teachers** — profile, linked to subjects/classes
- **Classes / Sections** — e.g. "Grade 5 - A"
- **Enrollments** — student ↔ class mapping

### Attendance
- **Daily attendance only** — one present/absent mark per student per day.
  Not per-period/per-subject. Keep this simple for v1; do not add period-level
  granularity unless explicitly requested.

### Results
- **Report cards (term-end grades) only** — not individual exam/test-level
  marks tracking in v1. Results are entered class-wise, per term, per subject,
  and viewed by the student they belong to.

### Leave / absence applications
- Student submits a leave application (reason, date range).
- Visible to the relevant teacher/admin.
- **No approval/reject workflow in v1.** No status field. This is a
  submit-and-log feature only — do not add a status/approval system unless
  explicitly requested later.

### Events & holidays
- `school_admin` posts events/announcements — visible to everyone in that
  school (students + teachers).
- A **fixed holiday list** per school (calendar of non-working days).
- No RSVP, no attendance tracking on events in v1. Simple post + list view.

### Chatbot
- Per-school scoped — answers questions using that school's own data only
  (policies, events, holidays, general info), never cross-tenant.
- Built via RAG: school info is embedded and stored in `pgvector`, retrieved
  per query, sent to Claude API along with the question.
- Built in Phase 4, after core API and data model are stable.

### Explicitly out of scope for v1 (do not build unless asked)
- Parent accounts/logins
- Leave approval/rejection workflow
- Per-period/per-subject attendance
- Individual exam/test marks (only term-end report cards)
- Event RSVP/attendance tracking
- Fees/payments, library, transport modules
- Per-school app builds (custom bundle ID/icon per school)

---

## Folder structure
```
a2school/
├── backend/      FastAPI app, SQLAlchemy models, Alembic migrations
├── website/      Admin dashboard frontend
├── mobile/       Flutter app
└── docs/         Schema notes, ER diagrams, decisions log
```

---

## Working conventions (important — follow these)
- **Prefer minimal, surgical changes.** Do not restructure or refactor
  beyond what is explicitly requested.
- **No unrequested scope expansion.** If something seems missing or you
  think a feature should be added, point it out and ask — don't silently
  add it. The "Explicitly out of scope" list above is intentional, not an
  oversight.
- When code or a document has been pasted directly into the conversation,
  treat that pasted content as the source of truth over any same-named file
  already on disk, unless told otherwise.
- If a request conflicts with something locked in this file (tech stack,
  scope, multi-tenancy pattern), flag the conflict before proceeding instead
  of silently following the newer instruction.

---

## Status
Currently in: **Phase 1 — database schema design.**
Not yet started: backend implementation, website, mobile, chatbot ingestion,
deployment, hosting provisioning.
