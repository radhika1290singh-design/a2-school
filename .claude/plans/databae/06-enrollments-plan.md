# Plan: Spec 06 — `enrollments`

## Context
The central linking table. Ties a user (student OR teacher) to a section for
a specific academic year. All history is preserved by never modifying old rows —
promotion creates a new enrollment row. Attendance, results, and fee periods all
reference `enrollment_id`, keeping records pinned to the exact year+class+section.

## Dependencies
- `users` (02), `sections` (05), `academic_years` (03) must all exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/enrollment.py` |
| **Create** | `backend/alembic/versions/0006_create_enrollments_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.enrollment` |

## Model — `backend/app/models/enrollment.py`

```python
import enum, uuid
from sqlalchemy import Enum as SAEnum, DateTime, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class EnrollmentType(str, enum.Enum):
    student = "student"
    class_teacher = "class_teacher"

class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "academic_year_id", "enrollment_type", name="uq_enrollments_user_year_type"),
        Index(
            "uq_enrollments_one_class_teacher_per_section",
            "section_id", "academic_year_id",
            unique=True,
            postgresql_where=text("enrollment_type = 'class_teacher'"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    enrollment_type: Mapped[EnrollmentType] = mapped_column(SAEnum(EnrollmentType, name="enrollment_type"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0006_create_enrollments_table.py`

- `revision = "0006"`, `down_revision = "0005"`
- **New PostgreSQL enum**: `enrollment_type ('student', 'class_teacher')`
- `upgrade`: `op.execute("CREATE TYPE enrollment_type ...")` → `op.create_table(...)` → `op.create_index(...)` (partial index)
- `downgrade`: `op.drop_index(...)` → `op.drop_table(...)` → `op.execute("DROP TYPE IF EXISTS enrollment_type")`

Partial unique index (after `create_table`):
```python
op.create_index(
    "uq_enrollments_one_class_teacher_per_section",
    "enrollments", ["section_id", "academic_year_id"],
    unique=True,
    postgresql_where=sa.text("enrollment_type = 'class_teacher'"),
)
```

## Key decisions
- **Partial unique index** — only one class-teacher per section per year, but many students allowed
- **Promotion model** — create new row, never modify old; history queryable by `academic_year_id`
- Role enforcement (student ↔ student type, teacher ↔ class_teacher type) is app-layer only, not a DB constraint
- All FKs `ondelete="CASCADE"` — enrollment is meaningless without its user/section/year

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d enrollments           -- check enum column, unique constraint
\d+ enrollments          -- confirm partial index visible
```
