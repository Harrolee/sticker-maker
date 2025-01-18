"""Add created_at to stickers

Revision ID: add_created_at_stickers
Revises: 03935256cdef
Create Date: 2024-11-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'add_created_at_stickers'
down_revision: Union[str, None] = '03935256cdef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_at column with default current timestamp
    op.add_column('stickers', 
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    
    # Update existing rows to have a created_at value
    op.execute("""
        UPDATE stickers 
        SET created_at = CURRENT_TIMESTAMP 
        WHERE created_at IS NULL
    """)
    
    # Make the column not nullable after setting defaults
    op.alter_column('stickers', 'created_at',
        existing_type=sa.DateTime(),
        nullable=False
    )
    
    # Make storefront_product_id nullable
    op.alter_column('stickers', 'storefront_product_id',
        existing_type=sa.String(length=100),
        nullable=True
    )


def downgrade() -> None:
    # Make storefront_product_id not nullable again
    op.alter_column('stickers', 'storefront_product_id',
        existing_type=sa.String(length=100),
        nullable=False
    )
    
    # Drop the created_at column
    op.drop_column('stickers', 'created_at') 