# A2 School — DB Spec 07: `attendance`

## Dependencies
- `enrollments` (06) must exist first
- `users` (02) must exist first

## Purpose
Daily attendance per student. One record per student per day.
Not per-period/per-subject — daily only.

## Table: `attendance`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `enrollment_id` | UUID | NO | FK → enrollments.id. Must be a student-type enrollment |
| `date` | date | NO | |
| `status` | enum(`present`,`absent`) | NO | Binary only — no late/excused in v1 |
| `marked_by_user_id` | UUID | NO | FK → users.id. The teacher who marked it |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(enrollment_id, date)` — one attendance mark per student per day,
  no double-marking

## Rules
- Teacher can only mark attendance for students whose enrollment shares
  the same section_id as the teacher's own class_teacher enrollment
  for the current academic year
- Admin can mark attendance for any student in their school
- Student has read-only access to their own attendance records only
