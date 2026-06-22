"""add attempt_count to otp_requests

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "otp_requests",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("otp_requests", "attempt_count")
