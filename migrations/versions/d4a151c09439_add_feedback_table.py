"""add_feedback_table

Revision ID: d4a151c09439
Revises: c975de9d868b
Create Date: 2025-04-05 22:33:01.859350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a151c09439'
down_revision: Union[str, None] = 'c975de9d868b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
