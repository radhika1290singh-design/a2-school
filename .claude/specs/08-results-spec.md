# A2 School — DB Spec 08: `results`

## Dependencies
- `enrollments` (06) must exist first
- `users` (02) must exist first

## Purpose
Term-end report card results per student, per subject, per term.
NOT individual exam/test marks — term-end only.

## Table: `results`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `enrollment_id` | UUID | NO | FK → enrollments.id. Must be student-type |
| `term` | text | NO | e.g. "Term 1", "Final" — free text, varies by school |
| `subject` | text | NO | e.g. "Mathematics" — free text in v1, no subjects table yet |
| `marks_obtained` | numeric | YES | |
| `marks_total` | numeric | YES | e.g. 85 out of 100 |
| `grade` | text | YES | Optional letter grade e.g. "A", "B+" |
| `entered_by_user_id` | UUID | NO | FK → users.id. Teacher who entered it |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(enrollment_id, term, subject)` — one result per student per
  term per subject

## Rules
- Teacher can enter/edit results only for students in their own section
- Admin can enter/edit results for any student in their school
- Student has read-only access to their own results only
- At least one of marks_obtained/marks_total OR grade should be set
  (app-layer validation, not a DB constraint)
