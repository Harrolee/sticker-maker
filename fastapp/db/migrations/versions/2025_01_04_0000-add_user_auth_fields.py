"""add user auth fields

Revision ID: add_user_auth_fields
Revises: add_sticker_status
Create Date: 2025-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_auth_fields'
down_revision: Union[str, None] = 'add_sticker_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add username column (unique, nullable for existing users)
    op.add_column('users',
        sa.Column('username', sa.String(100), nullable=True)
    )
    op.create_unique_constraint('uq_users_username', 'users', ['username'])

    # Add password_hash column
    op.add_column('users',
        sa.Column('password_hash', sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'username')
    op.drop_column('users', 'password_hash')
