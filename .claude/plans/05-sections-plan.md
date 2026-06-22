# Plan: Spec 05 — `sections`

## Context
A section is the actual group a student/teacher belongs to within a class
(e.g. "Grade 5 - A", "Grade 5 - B"). A teacher is class-teacher of exactly
one section per academic year. A student belongs to exactly one section per
academic year. The class-teacher relationship is stored in `enrollments`, not
here, because it changes per year.

## Dependencies
- `schools` (01) — reachable via class_id, not a direct FK
- `classes` (04) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/section.py` |
| **Create** | `backend/alembic/versions/0005_create_sections_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.section` |

## Model — `backend/app/models/section.py`

```python
import uuid
from sqlalchemy import Text, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_sections_class_name"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0005_create_sections_table.py`

- `revision = "0005"`, `down_revision = "0004"`
- No PostgreSQL enum types needed
- `upgrade`: `op.create_table("sections", ...)` with `UniqueConstraint("class_id", "name")`
- `downgrade`: `op.drop_table("sections")`

## Key decisions
- **No `school_id` column** — intentionally normalized; school is reachable via `class_id → classes.school_id`
- Which teacher is class-teacher of a section is NOT stored here — lives in `enrollments` (changes per year)
- `ondelete="CASCADE"` on `class_id` FK — deleting a class removes its sections

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d sections   -- confirm no school_id column, unique constraint on (class_id, name)
```
