"""recreate users and add otp_requests

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old incompatible users table (empty, safe to drop)
    op.drop_table("users")

    # New enums (keep existing 'role' enum — same values)
    op.execute("CREATE TYPE user_status AS ENUM ('pending', 'active')")
    op.execute("CREATE TYPE otp_purpose AS ENUM ('activation', 'password_reset')")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "role",
            postgresql.ENUM(name="role", create_type=False),
            nullable=False,
        ),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "active", name="user_status", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("school_id", "phone_number", name="uq_users_school_phone"),
        sa.CheckConstraint("role != 'super_admin' OR school_id IS NULL", name="ck_super_admin_no_school"),
        sa.CheckConstraint("role = 'super_admin' OR school_id IS NOT NULL", name="ck_non_super_admin_has_school"),
    )

    op.create_table(
        "otp_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column(
            "purpose",
            postgresql.ENUM("activation", "password_reset", name="otp_purpose", create_type=False),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("otp_requests")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_status")
    op.execute("DROP TYPE IF EXISTS otp_purpose")
