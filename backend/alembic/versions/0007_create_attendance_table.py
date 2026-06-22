"""create attendance table

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE attendance_status AS ENUM ('present', 'absent')")
    op.create_table(
        "attendance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "enrollment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("present", "absent", name="attendance_status", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "marked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("enrollment_id", "date", name="uq_attendance_enrollment_date"),
    )


def downgrade() -> None:
    op.drop_table("attendance")
    op.execute("DROP TYPE IF EXISTS attendance_status")
