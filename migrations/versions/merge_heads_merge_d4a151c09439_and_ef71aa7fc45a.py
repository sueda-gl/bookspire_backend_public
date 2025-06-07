"""Merge d4a151c09439 and ef71aa7fc45a

Revision ID: merge_heads
Revises: ef71aa7fc45a
Create Date: 2025-04-27 19:01:18.025244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_heads'
down_revision: Union[str, None] = 'ef71aa7fc45a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
