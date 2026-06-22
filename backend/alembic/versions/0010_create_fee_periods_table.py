"""create fee_periods table

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE fee_status AS ENUM ('paid', 'unpaid')")
    op.create_table(
        "fee_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "enrollment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_label", sa.Text(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("amount_due", sa.Numeric(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("paid", "unpaid", name="fee_status", create_type=False),
            nullable=False,
            server_default="unpaid",
        ),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column(
            "marked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fee_periods")
    op.execute("DROP TYPE IF EXISTS fee_status")
