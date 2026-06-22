import enum
import uuid
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
            "section_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("enrollment_type = 'class_teacher'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    enrollment_type: Mapped[EnrollmentType] = mapped_column(
        SAEnum(EnrollmentType, name="enrollment_type"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
