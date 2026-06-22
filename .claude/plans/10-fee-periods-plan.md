# Plan: Spec 10 — `fee_periods`

## Context
Tracks fee payment status per student per billing period. Generated upfront
for the full academic year at enrollment creation time (all 12 months at once
for monthly, 4 for quarterly, 1 for yearly). `amount_due` is snapshotted from
`classes.fee_amount` at generation time — changing the class fee later does NOT
affect already-generated periods.

## Dependencies
- `enrollments` (06) and `users` (02) must exist first

## Files

| Action | Path |
|--------|------|
| **Create** | `backend/app/models/fee_period.py` |
| **Create** | `backend/alembic/versions/0010_create_fee_periods_table.py` |
| **Edit**   | `backend/alembic/env.py` — add `import app.models.fee_period` |

## Model — `backend/app/models/fee_period.py`

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

## Migration — `0010_create_fee_periods_table.py`

- `revision = "0010"`, `down_revision = "0009"`
- **New PostgreSQL enum**: `fee_status ('paid', 'unpaid')`
- `upgrade`: `op.execute("CREATE TYPE fee_status ...")` → `op.create_table(...)` with `server_default="unpaid"`
- `downgrade`: `op.drop_table(...)` → `op.execute("DROP TYPE IF EXISTS fee_status")`

## Key decisions
- `amount_due` is a snapshot (NOT a live FK to `classes.fee_amount`) — historical accuracy preserved
- `marked_by_user_id` nullable → `ondelete="SET NULL"` — record stays if marker user is deleted
- `status` defaults to `'unpaid'` — all generated periods start unpaid
- Generation logic (monthly/quarterly/yearly) is app-layer, not DB; this table just stores the output
- Billing cycle from `schools.fee_billing_cycle`: monthly=12 rows, quarterly=4, yearly=1

## Verification
```bash
cd backend && alembic upgrade head
```
```sql
\d fee_periods   -- check fee_status default='unpaid', nullable paid_date and marked_by_user_id
```
