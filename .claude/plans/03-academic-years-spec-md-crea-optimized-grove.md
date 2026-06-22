# Plan: Specs 04–12 — Models + Migrations

## Context
Specs 03 (academic_years) is already implemented (revision 0003). This plan
covers the remaining 9 entities from the DB spec. All are Phase 1 schema
work only — no routers or endpoints. Migration chain starts from revision 0003.

---

## Files to create / modify

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/class_.py` |
| **Create** | `backend/app/models/section.py` |
| **Create** | `backend/app/models/enrollment.py` |
| **Create** | `backend/app/models/attendance.py` |
| **Create** | `backend/app/models/result.py` |
| **Create** | `backend/app/models/leave_application.py` |
| **Create** | `backend/app/models/fee_period.py` |
| **Create** | `backend/app/models/event.py` |
| **Create** | `backend/app/models/holiday.py` |
| **Create** | `backend/alembic/versions/0004_create_classes_table.py` |
| **Create** | `backend/alembic/versions/0005_create_sections_table.py` |
| **Create** | `backend/alembic/versions/0006_create_enrollments_table.py` |
| **Create** | `backend/alembic/versions/0007_create_attendance_table.py` |
| **Create** | `backend/alembic/versions/0008_create_results_table.py` |
| **Create** | `backend/alembic/versions/0009_create_leave_applications_table.py` |
| **Create** | `backend/alembic/versions/0010_create_fee_periods_table.py` |
| **Create** | `backend/alembic/versions/0011_create_events_table.py` |
| **Create** | `backend/alembic/versions/0012_create_holidays_table.py` |
| **Edit**   | `backend/alembic/env.py` — add 9 model imports |

---

## Conventions (from existing code)
- All models: inherit `Base` from `app.database`, use `Mapped` + `mapped_column`
- UUID PK: `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4`
- All FKs to `schools.id` / `users.id` / etc. use `ondelete="CASCADE"` unless noted
- FKs for audit columns (`marked_by_user_id`, `entered_by_user_id`, `posted_by_user_id`) use `ondelete="RESTRICT"` — prevent deleting a user who has records
- FK for nullable audit columns use `ondelete="SET NULL"`
- Timestamps: `DateTime(timezone=True), server_default=text("now()")`
- PostgreSQL ENUM types: created via `op.execute("CREATE TYPE ...")` before the table, `create_type=False` on the column, dropped in `downgrade()`

---

## Spec 04 — `classes` (revision 0004, down_revision=0003)

No enum types.

**Model** `backend/app/models/class_.py`:
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

**Migration** upgrade: `op.create_table("classes", ...)` with UniqueConstraint.  
**Migration** downgrade: `op.drop_table("classes")`.

---

## Spec 05 — `sections` (revision 0005, down_revision=0004)

No enum types. Note: **no `school_id` column** — school is reachable via `class_id → classes.school_id`.

**Model** `backend/app/models/section.py`:
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

**Migration**: same pattern; no enum types.

---

## Spec 06 — `enrollments` (revision 0006, down_revision=0005)

**New PostgreSQL enum**: `enrollment_type` with values `('student', 'class_teacher')`.

**Special constraint**: partial unique index `UNIQUE(section_id, academic_year_id) WHERE enrollment_type = 'class_teacher'` — one class-teacher per section per year.  
In Alembic, add this *after* `create_table` as a separate `op.create_index`:
```python
op.create_index(
    "uq_enrollments_one_class_teacher_per_section",
    "enrollments",
    ["section_id", "academic_year_id"],
    unique=True,
    postgresql_where=sa.text("enrollment_type = 'class_teacher'"),
)
```
In the model, add to `__table_args__`:
```python
Index("uq_enrollments_one_class_teacher_per_section", "section_id", "academic_year_id",
      unique=True, postgresql_where=text("enrollment_type = 'class_teacher'")),
```

**Model** `backend/app/models/enrollment.py`:
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
        Index("uq_enrollments_one_class_teacher_per_section", "section_id", "academic_year_id",
              unique=True, postgresql_where=text("enrollment_type = 'class_teacher'")),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    enrollment_type: Mapped[EnrollmentType] = mapped_column(SAEnum(EnrollmentType, name="enrollment_type"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

---

## Spec 07 — `attendance` (revision 0007, down_revision=0006)

**New PostgreSQL enum**: `attendance_status` with values `('present', 'absent')`.

`marked_by_user_id` is NOT NULL → `ondelete="RESTRICT"` (can't delete a teacher who has marked attendance).

**Model** `backend/app/models/attendance.py`:
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

---

## Spec 08 — `results` (revision 0008, down_revision=0007)

No enum types. `entered_by_user_id` NOT NULL → `ondelete="RESTRICT"`.

**Model** `backend/app/models/result.py`:
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

---

## Spec 09 — `leave_applications` (revision 0009, down_revision=0008)

No enum types. No status field — intentional per spec.

**Model** `backend/app/models/leave_application.py`:
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

---

## Spec 10 — `fee_periods` (revision 0010, down_revision=0009)

**New PostgreSQL enum**: `fee_status` with values `('paid', 'unpaid')`.

`marked_by_user_id` is **nullable** → `ondelete="SET NULL"`.

**Model** `backend/app/models/fee_period.py`:
```python
import enum, uuid
from sqlalchemy import Enum as SAEnum, Text, Date, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class FeeStatus(str, enum.Enum):
    paid = "paid"
    unpaid = "unpaid"

class FeePeriod(Base):
    __tablename__ = "fee_periods"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    period_label: Mapped[str] = mapped_column(Text, nullable=False)
    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    amount_due: Mapped[Numeric] = mapped_column(Numeric, nullable=False)
    status: Mapped[FeeStatus] = mapped_column(SAEnum(FeeStatus, name="fee_status"), nullable=False, server_default=text("'unpaid'"))
    paid_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    marked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
```

---

## Spec 11 — `events` (revision 0011, down_revision=0010)

No enum types. `posted_by_user_id` NOT NULL → `ondelete="RESTRICT"`.

**Model** `backend/app/models/event.py`:
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

---

## Spec 12 — `holidays` (revision 0012, down_revision=0011)

No enum types. `academic_year_id` **nullable** → `ondelete="SET NULL"`.

**Model** `backend/app/models/holiday.py`:
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

---

## Migration structure for enum-using specs

For 0006, 0007, 0010 — follow the pattern from 0001 exactly:
```python
def upgrade() -> None:
    op.execute("CREATE TYPE enrollment_type AS ENUM ('student', 'class_teacher')")
    op.create_table("enrollments", ...)
    op.create_index(...)  # partial index for class_teacher

def downgrade() -> None:
    op.drop_index("uq_enrollments_one_class_teacher_per_section", table_name="enrollments")
    op.drop_table("enrollments")
    op.execute("DROP TYPE IF EXISTS enrollment_type")
```

Enum type names (PostgreSQL): `enrollment_type`, `attendance_status`, `fee_status`.

---

## env.py additions

Add 9 imports after the existing `import app.models.academic_year` line:
```python
import app.models.class_           # noqa: F401
import app.models.section          # noqa: F401
import app.models.enrollment       # noqa: F401
import app.models.attendance       # noqa: F401
import app.models.result           # noqa: F401
import app.models.leave_application  # noqa: F401
import app.models.fee_period       # noqa: F401
import app.models.event            # noqa: F401
import app.models.holiday          # noqa: F401
```

---

## Verification

```bash
cd backend
alembic upgrade head       # applies 0004–0012 cleanly
alembic downgrade base     # drops all tables in reverse order
alembic upgrade head       # confirm full roundtrip
```

Spot-check in `a2school_dev`:
```sql
\dt                         -- all 12 tables present
\d enrollments              -- check partial index and enum column
\d fee_periods              -- check fee_status default and nullable FK
```
