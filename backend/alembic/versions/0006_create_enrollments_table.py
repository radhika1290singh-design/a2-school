"""create enrollments table

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE enrollment_type AS ENUM ('student', 'class_teacher')")
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_years.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enrollment_type",
            postgresql.ENUM("student", "class_teacher", name="enrollment_type", create_type=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "academic_year_id", "enrollment_type", name="uq_enrollments_user_year_type"),
    )
    op.create_index(
        "uq_enrollments_one_class_teacher_per_section",
        "enrollments",
        ["section_id", "academic_year_id"],
        unique=True,
        postgresql_where=sa.text("enrollment_type = 'class_teacher'"),
    )


def downgrade() -> None:
    op.drop_index("uq_enrollments_one_class_teacher_per_section", table_name="enrollments")
    op.drop_table("enrollments")
    op.execute("DROP TYPE IF EXISTS enrollment_type")
