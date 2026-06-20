import enum
import uuid
from sqlalchemy import Text, DateTime, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FeeBillingCycle(str, enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class SchoolStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    subdomain: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    custom_domain: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    fee_billing_cycle: Mapped[FeeBillingCycle | None] = mapped_column(
        SAEnum(FeeBillingCycle, name="fee_billing_cycle"), nullable=True
    )
    status: Mapped[SchoolStatus] = mapped_column(
        SAEnum(SchoolStatus, name="school_status"),
        nullable=False,
        server_default=text("'active'"),
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
