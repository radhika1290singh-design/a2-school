# A2 School — DB Spec 03: `academic_years`

## Dependencies
- `schools` (01) must exist first

## Purpose
Defines the time dimension for all academic records. Every enrollment,
attendance, result, and fee record is scoped to an academic year, which is
what makes full historical record keeping possible without overwriting data.

## Table: `academic_years`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `school_id` | UUID | NO | FK → schools.id |
| `label` | text | NO | e.g. "2025-2026", admin-entered |
| `start_date` | date | NO | |
| `end_date` | date | NO | |
| `is_current` | boolean | NO | Default false. Only ONE per school can be true at a time — enforced at app layer (unset old, set new in one transaction) |
| `created_at` | timestamp | NO | Default now() |

## Constraints
- `UNIQUE(school_id, label)` — no duplicate year labels per school

## Rules
- Only `school_admin` can create/edit academic years for their school
- `super_admin` can see all
- `teacher` and `student` have read-only access
- When admin marks a year as `is_current = true`, the previous current
  year must be set to `false` in the same transaction (app-layer logic,
  not a DB constraint)
