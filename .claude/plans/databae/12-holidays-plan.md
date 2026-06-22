# Plan: Spec 12 — `holidays`

## Context
Fixed non-working-day calendar per school. Separate from `events` — holidays
are calendar entries (no-school days), events are announcements. `academic_year_id`
is nullable to allow recurring/fixed holidays not tied to a specific year, while
still supporting year-specific calendars.

## Dependencies
- `schools` (01) and `academic_years` (03) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/holiday.py` |
| **Create** | `backend/alembic/versions/0012_create_holidays_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.holiday` |

## Model — `backend/app/models/holiday.py`

```python
import uuid
from sqlalchemy import Text, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Holiday(Base):
    __tablename__ = "holidays"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0012_create_holidays_table.py`

- `revision = "0012"`, `down_revision = "0011"`
- No PostgreSQL enum types needed
- No unique constraints needed
- `upgrade`: `op.create_table("holidays", ...)`
- `downgrade`: `op.drop_table("holidays")`

## Key decisions
- `academic_year_id` nullable → `ondelete="SET NULL"` — holiday stays if the academic year is deleted
- `school_id` → `ondelete="CASCADE"` — scoped to tenant; holidays deleted with school
- Kept separate from `events` — different semantic meaning, no type/flag merging in v1
- No RSVP or attendance tracking in v1

## Verification
```bash
cd backend && alembic upgrade head   # final migration in the chain
alembic downgrade base               # drop all
alembic upgrade head                 # confirm full roundtrip
```
```sql
\dt                 -- confirm all 12 tables present
\d holidays         -- check nullable academic_year_id, SET NULL behavior
```
