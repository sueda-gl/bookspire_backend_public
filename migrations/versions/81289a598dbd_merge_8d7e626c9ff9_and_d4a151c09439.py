"""merge 8d7e626c9ff9 and d4a151c09439

Revision ID: 81289a598dbd
Revises: 8d7e626c9ff9, d4a151c09439
Create Date: 2025-04-27 20:56:26.256741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81289a598dbd'
down_revision: Union[str, None] = ('8d7e626c9ff9', 'd4a151c09439')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
