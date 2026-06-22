# A2 School — DB Spec 09: `leave_applications`

## Dependencies
- `enrollments` (06) must exist first

## Purpose
Student submits a leave/absence request. Log only — no approval workflow,
no status field. Visible to the student's class teacher.

## Table: `leave_applications`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `enrollment_id` | UUID | NO | FK → enrollments.id. Student's current enrollment at time of submission. Student-type only. |
| `reason` | text | NO | |
| `start_date` | date | NO | |
| `end_date` | date | NO | |
| `created_at` | timestamp | NO | Default now() — acts as submission timestamp |

## No status column — intentional
No approval/reject workflow in v1. This is a submit-and-log feature only.
Do not add a status field without explicit request.

## Rules
- Only students can submit leave applications (for their own enrollment)
- Visible to: the teacher whose class_teacher enrollment shares the same
  section_id + academic_year_id as the student's enrollment. No separate
  recipient field needed — derivable via join.
- Admin can see all leave applications in their school
- Student can see only their own
