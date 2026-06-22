# Plan: Spec 11 — `events`

## Context
School-wide announcements/events posted by school_admin. Visible to all users
in the school (students + teachers). No RSVP, no attendance tracking in v1 —
simple post + list view. Scoped to `school_id` for multi-tenancy.

## Dependencies
- `schools` (01) and `users` (02) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/event.py` |
| **Create** | `backend/alembic/versions/0011_create_events_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.event` |

## Model — `backend/app/models/event.py`

```python
import uuid
from sqlalchemy import Text, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[Date] = mapped_column(Date, nullable=False)
    posted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0011_create_events_table.py`

- `revision = "0011"`, `down_revision = "0010"`
- No PostgreSQL enum types needed
- No unique constraints needed
- `upgrade`: `op.create_table("events", ...)`
- `downgrade`: `op.drop_table("events")`

## Key decisions
- `posted_by_user_id` NOT NULL → `ondelete="RESTRICT"` — cannot delete an admin who has posted events
- `description` nullable — title-only events are valid
- `school_id` → `ondelete="CASCADE"` — scoped to tenant; events deleted with school
- No RSVP or attendance tracking in v1

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d events   -- check description nullable, event_date date type, RESTRICT on posted_by
```
