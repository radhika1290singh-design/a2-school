import enum
import uuid
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
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status"), nullable=False
    )
    marked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
