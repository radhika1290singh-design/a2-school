"""create results table

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "enrollment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("term", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(), nullable=True),
        sa.Column("marks_total", sa.Numeric(), nullable=True),
        sa.Column("grade", sa.Text(), nullable=True),
        sa.Column(
            "entered_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("enrollment_id", "term", "subject", name="uq_results_enrollment_term_subject"),
    )


def downgrade() -> None:
    op.drop_table("results")
