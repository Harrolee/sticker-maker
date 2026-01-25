"""add auth0 id column

Revision ID: add_auth0_id_column
Revises: add_oauth_id_columns
Create Date: 2025-01-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_auth0_id_column'
down_revision: Union[str, None] = 'add_oauth_id_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('auth0_id', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_users_auth0_id', 'users', ['auth0_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_auth0_id', 'users', type_='unique')
    op.drop_column('users', 'auth0_id')
