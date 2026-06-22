# A2 School — DB Spec 06: `enrollments`

## Dependencies
- `users` (02) must exist first
- `sections` (05) must exist first
- `academic_years` (03) must exist first

## Purpose
The central linking table. Ties a user (student OR teacher) to a section
for a specific academic year. This is the backbone of the history model —
attendance, results, and fee periods all reference an enrollment_id, not
the user directly. This means past records stay pinned to the exact
year+class+section they belong to, even after a student is promoted.

Single combined table for both relationships:
- Student in a section for a year (enrollment_type = 'student')
- Teacher as class-teacher of a section for a year (enrollment_type = 'class_teacher')

## Table: `enrollments`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `user_id` | UUID | NO | FK → users.id |
| `section_id` | UUID | NO | FK → sections.id |
| `academic_year_id` | UUID | NO | FK → academic_years.id |
| `enrollment_type` | enum(`student`,`class_teacher`) | NO | |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(user_id, academic_year_id, enrollment_type)` — one enrollment
  of each type per user per year. Allows same user to have a new
  enrollment next year (different academic_year_id) without conflict.
- Partial unique index: `UNIQUE(section_id, academic_year_id)` WHERE
  `enrollment_type = 'class_teacher'` — only one class-teacher per
  section per year. Does NOT apply to student rows (many students per
  section is expected).

## App-layer rules (not DB constraints)
- A user with role='student' can only get enrollment_type='student'
- A user with role='teacher' can only get enrollment_type='class_teacher'
- enrollment_type must match the user's role at creation time

## How promotion works
Promotion = create a NEW enrollments row:
- Same user_id
- Same enrollment_type
- New academic_year_id (the new year)
- New section_id (admin manually picks which section in the new class)
Old row is NEVER modified — it becomes permanent history, queryable by
filtering academic_year_id.

## Visibility via this table
- Student's full history: SELECT * FROM enrollments WHERE user_id = <student>
- Teacher's current students: find teacher's class_teacher enrollment for
  current year → get section_id → find all student enrollments with same
  section_id + academic_year_id
- Teacher's historical students: same but across ALL the teacher's
  class_teacher enrollments (all years)
- Admin: no enrollment filter, scoped only by school_id via the
  section → class → school join chain
