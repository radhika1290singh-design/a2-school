# Plan: Spec 04 — `classes`

## Context
Defines grade levels (e.g. "Grade 5"). Persists across academic years — NOT
year-scoped. The same row is reused each year; enrollments tie students to a
class for a specific year. `display_order` drives both UI sort order and
year-end promotion sequencing and must stay gap-free.

## Dependencies
- `schools` (01) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/grade.py` |
| **Create** | `backend/alembic/versions/0004_create_classes_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.class_` |

## Model — `backend/app/models/class_.py`

```python
import uuid
from sqlalchemy import Text, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Class(Base):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_classes_school_name"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    fee_amount: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0004_create_classes_table.py`

- `revision = "0004"`, `down_revision = "0003"`
- No PostgreSQL enum types needed
- `upgrade`: `op.create_table("classes", ...)` with `UniqueConstraint("school_id", "name")`
- `downgrade`: `op.drop_table("classes")`

## Key decisions
- `fee_amount` nullable — admin sets it before academic year starts; fee periods cannot generate without it
- `display_order` NOT NULL — drives promotion logic, must be gap-free (1, 2, 3…)
- `ondelete="CASCADE"` on `school_id` FK — deleting a school removes its classes

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d classes   -- check display_order integer, fee_amount numeric nullable, unique constraint
```
