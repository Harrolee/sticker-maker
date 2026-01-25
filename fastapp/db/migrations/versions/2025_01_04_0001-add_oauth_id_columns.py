"""add oauth id columns

Revision ID: add_oauth_id_columns
Revises: add_user_auth_fields
Create Date: 2025-01-04 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_oauth_id_columns'
down_revision: Union[str, None] = 'add_user_auth_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('github_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('google_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'github_id')
    op.drop_column('users', 'google_id')
