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
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False
    )
    term: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    marks_obtained: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    marks_total: Mapped[Numeric | None] = mapped_column(Numeric, nullable=True)
    grade: Mapped[str | None] = mapped_column(Text, nullable=True)
    entered_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
