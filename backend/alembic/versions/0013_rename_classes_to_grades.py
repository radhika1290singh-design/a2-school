"""rename classes table to grades

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-22
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("classes", "grades")
    op.execute("ALTER TABLE grades RENAME CONSTRAINT uq_classes_school_name TO uq_grades_school_name")


def downgrade() -> None:
    op.execute("ALTER TABLE grades RENAME CONSTRAINT uq_grades_school_name TO uq_classes_school_name")
    op.rename_table("grades", "classes")
