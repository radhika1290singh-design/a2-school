# A2 School — DB Spec 12: `holidays`

## Dependencies
- `schools` (01) must exist first
- `academic_years` (03) must exist first

## Purpose
Fixed non-working-day calendar per school. Separate from events —
holidays are calendar entries (no school days), events are announcements.

## Table: `holidays`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `school_id` | UUID | NO | FK → schools.id |
| `name` | text | NO | e.g. "Diwali", "Summer Break" |
| `date` | date | NO | |
| `academic_year_id` | UUID | YES | FK → academic_years.id. Nullable — allows recurring/fixed holidays not tied to a specific year, but settable for year-specific calendars |
| `created_at` | timestamp | NO | Default now() |

## Rules
- Only school_admin can create/edit/delete holidays
- All users in the same school have read access
- Scoped to school_id — no cross-school visibility
- Kept separate from events table — different semantic meaning even though
  both have a date + name. No type/flag merging in v1.
