"""add sticker status

Revision ID: add_sticker_status
Revises: add_created_at_stickers
Create Date: 2025-01-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sticker_status'
down_revision: Union[str, None] = 'add_created_at_stickers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column with default value
    op.add_column('stickers', 
        sa.Column('status', sa.String(), 
                 nullable=False, 
                 server_default='ready')  # Default existing stickers to ready
    )
    
    # Add image_path column
    op.add_column('stickers',
        sa.Column('image_path', sa.String(), 
                 nullable=True)
    )


def downgrade() -> None:
    op.drop_column('stickers', 'status')
    op.drop_column('stickers', 'image_path') 