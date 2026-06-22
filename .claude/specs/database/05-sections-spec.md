# A2 School — DB Spec 05: `sections`

## Dependencies
- `schools` (01) must exist first
- `classes` (04) must exist first

## Purpose
A section is the actual group a student/teacher belongs to within a class.
e.g. "Grade 5 - A", "Grade 5 - B". A teacher is class-teacher of exactly
one section per academic year. A student belongs to exactly one section
per academic year.

## Table: `sections`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `class_id` | UUID | NO | FK → classes.id |
| `name` | text | NO | e.g. "A", "B", "Blue" — free text, not a fixed enum |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(class_id, name)` — no two sections with the same name under
  the same class

## Notes
- `school_id` is NOT a column here — reachable via
  `sections.class_id → classes.school_id`. Keeps schema normalized.
- Which teacher is class-teacher of a section is NOT stored here —
  that relationship lives in `enrollments` (06), since it changes per
  academic year
- Only `school_admin` can create/edit sections
