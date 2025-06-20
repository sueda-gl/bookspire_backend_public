"""create_story_sessions_with_language_

Revision ID: f116c4e51b3e
Revises: 4d424ef7c613
Create Date: 2025-04-28 13:58:42.275022

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f116c4e51b3e'
down_revision: Union[str, None] = '4d424ef7c613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('story_sessions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('language_level', sa.String(length=5), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_story_sessions_user_id'), 'story_sessions', ['user_id'], unique=False)
    
    op.create_table('story_messages',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('message_id', sa.String(length=36), nullable=False),
    sa.Column('character_id', sa.String(length=50), nullable=False),
    sa.Column('is_complete', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['story_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_story_messages_message_id'), 'story_messages', ['message_id'], unique=False)
    
    op.create_table('story_hints',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('message_id', sa.String(length=36), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('is_used', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['message_id'], ['story_messages.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['story_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('story_hints')
    op.drop_index(op.f('ix_story_messages_message_id'), table_name='story_messages')
    op.drop_table('story_messages')
    op.drop_index(op.f('ix_story_sessions_user_id'), table_name='story_sessions')
    op.drop_table('story_sessions')
    # ### end Alembic commands ###
