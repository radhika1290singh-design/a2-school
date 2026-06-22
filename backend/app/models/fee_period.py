import enum
import uuid
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
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False
    )
    period_label: Mapped[str] = mapped_column(Text, nullable=False)
    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    amount_due: Mapped[Numeric] = mapped_column(Numeric, nullable=False)
    status: Mapped[FeeStatus] = mapped_column(
        SAEnum(FeeStatus, name="fee_status"),
        nullable=False,
        server_default=text("'unpaid'"),
    )
    paid_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    marked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
