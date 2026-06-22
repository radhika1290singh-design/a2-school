# A2 School — DB Spec 11: `events`

## Dependencies
- `schools` (01) must exist first
- `users` (02) must exist first

## Purpose
School-wide announcements/events posted by admin. Visible to all users
in the school (students + teachers).

## Table: `events`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | Primary key |
| `school_id` | UUID | NO | FK → schools.id |
| `title` | text | NO | |
| `description` | text | YES | |
| `event_date` | date | NO | |
| `posted_by_user_id` | UUID | NO | FK → users.id. Must be school_admin |
| `created_at` | timestamp | NO | Default now() |

## Rules
- Only school_admin can create/edit/delete events
- All users in the same school (teacher + student) have read access
- Scoped to school_id — no cross-school visibility
- No RSVP, no attendance tracking in v1
