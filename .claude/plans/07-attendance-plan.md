# Plan: Spec 07 — `attendance`

## Context
Daily attendance per student. One record per student per day — not
per-period or per-subject. Binary only: present or absent (no late/excused
in v1). Linked to `enrollment_id` so records stay pinned to the exact
year+section even after promotion.

## Dependencies
- `enrollments` (06) and `users` (02) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/attendance.py` |
| **Create** | `backend/alembic/versions/0007_create_attendance_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.attendance` |

## Model — `backend/app/models/attendance.py`

```python
import enum, uuid
from sqlalchemy import Enum as SAEnum, Date, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "date", name="uq_attendance_enrollment_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(SAEnum(AttendanceStatus, name="attendance_status"), nullable=False)
    marked_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

## Migration — `0007_create_attendance_table.py`

- `revision = "0007"`, `down_revision = "0006"`
- **New PostgreSQL enum**: `attendance_status ('present', 'absent')`
- `upgrade`: `op.execute("CREATE TYPE attendance_status ...")` → `op.create_table(...)`
- `downgrade`: `op.drop_table(...)` → `op.execute("DROP TYPE IF EXISTS attendance_status")`

## Key decisions
- `marked_by_user_id` NOT NULL → `ondelete="RESTRICT"` — cannot delete a teacher who has marked attendance records
- `enrollment_id` → `ondelete="CASCADE"` — attendance record is meaningless without the enrollment
- `UNIQUE(enrollment_id, date)` prevents double-marking
- Daily only — no per-period/per-subject granularity in v1

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d attendance   -- check date type, enum status, unique constraint, RESTRICT on marked_by
```
