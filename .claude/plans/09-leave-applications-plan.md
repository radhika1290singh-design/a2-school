# Plan: Spec 09 — `leave_applications`

## Context
Student submits a leave/absence request. Log only — no approval workflow,
no status field in v1. Visible to the student's class teacher (derivable via
join through enrollment → section). `created_at` acts as the submission
timestamp.

## Dependencies
- `enrollments` (06) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/leave_application.py` |
| **Create** | `backend/alembic/versions/0009_create_leave_applications_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.leave_application` |

## Model — `backend/app/models/leave_application.py`

```python
import uuid
from sqlalchemy import Text, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class LeaveApplication(Base):
    __tablename__ = "leave_applications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0009_create_leave_applications_table.py`

- `revision = "0009"`, `down_revision = "0008"`
- No PostgreSQL enum types needed
- No unique constraints needed
- `upgrade`: `op.create_table("leave_applications", ...)`
- `downgrade`: `op.drop_table("leave_applications")`

## Key decisions
- **No `status` column** — intentional per spec; submit-and-log only, no approval/reject in v1
- **No separate recipient field** — teacher visibility is derivable via join (enrollment → section)
- `enrollment_id` → `ondelete="CASCADE"` — application is meaningless without the enrollment

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d leave_applications   -- confirm no status column, date columns present
```
