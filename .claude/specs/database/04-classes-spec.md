# A2 School — DB Spec 04: `classes`

## Dependencies
- `schools` (01) must exist first

## Purpose
Represents a grade level (e.g. "Grade 5"). Persists across academic years —
NOT year-scoped itself. The same "Grade 5" row is reused every year;
it's the `enrollments` table that ties students to a class in a specific year.

## Table: `classes`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `school_id` | UUID | NO | FK → schools.id |
| `name` | text | NO | e.g. "Grade 5", "Class 10" — free text, not a fixed enum |
| `fee_amount` | numeric | YES | Same for every student in this class. Nullable until admin sets it — fee periods cannot generate until this is set |
| `display_order` | integer | NO | **Drives both UI sort order AND year-end promotion sequencing.** Must be sequential/gap-free (1, 2, 3...). Promotion suggests moving a student to the class with the next-higher display_order in the same school |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(school_id, name)` — no two classes with the same name per school

## Rules
- Only `school_admin` can create/edit classes
- `display_order` must be kept gap-free and sequential by admin — it drives
  promotion logic directly, not just cosmetic sorting
- `fee_amount` should be set before the academic year starts, since
  fee periods are generated upfront from this value at enrollment creation
