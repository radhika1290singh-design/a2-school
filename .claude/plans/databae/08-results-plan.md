# Plan: Spec 08 — `results`

## Context
Term-end report card results per student, per subject, per term. NOT individual
exam/test marks — term-end only. Subject and term are free text (no subjects
table in v1). At least one of marks or grade should be set — enforced at app
layer only, not a DB constraint.

## Dependencies
- `enrollments` (06) and `users` (02) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/result.py` |
| **Create** | `backend/alembic/versions/0008_create_results_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.result` |

## Model — `backend/app/models/result.py`

```python
import uuid
from sqlalchemy import Text, Numeric, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "term", "subject", name="uq_results_enrollment_term_subject"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    term: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    marks_obtained: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    marks_total: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    grade: Mapped[str | None] = mapped_column(Text, nullable=True)
    entered_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0008_create_results_table.py`

- `revision = "0008"`, `down_revision = "0007"`
- No PostgreSQL enum types needed
- `upgrade`: `op.create_table("results", ...)` with `UniqueConstraint("enrollment_id", "term", "subject")`
- `downgrade`: `op.drop_table("results")`

## Key decisions
- `entered_by_user_id` NOT NULL → `ondelete="RESTRICT"` — cannot delete a teacher who has entered results
- `marks_obtained`, `marks_total`, `grade` all nullable — schools may use marks-only, grade-only, or both
- No subjects table in v1 — `subject` is free text
- Validation that at least one of marks/grade is set is app-layer only

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d results   -- check nullable numerics, text term/subject, unique constraint
```
