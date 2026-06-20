"""create schools table

Revision ID: 0001
Revises:
Create Date: 2026-06-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE fee_billing_cycle AS ENUM ('monthly', 'quarterly', 'yearly')")
    op.execute("CREATE TYPE school_status AS ENUM ('active', 'suspended')")
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("subdomain", sa.Text(), nullable=False),
        sa.Column("custom_domain", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("primary_color", sa.Text(), nullable=True),
        sa.Column("secondary_color", sa.Text(), nullable=True),
        sa.Column(
            "fee_billing_cycle",
            postgresql.ENUM("monthly", "quarterly", "yearly", name="fee_billing_cycle", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("active", "suspended", name="school_status", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("subdomain", name="uq_schools_subdomain"),
        sa.UniqueConstraint("custom_domain", name="uq_schools_custom_domain"),
    )


def downgrade() -> None:
    op.drop_table("schools")
    op.execute("DROP TYPE IF EXISTS fee_billing_cycle")
    op.execute("DROP TYPE IF EXISTS school_status")
