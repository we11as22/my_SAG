"""increase_source_chunk_content_size

Revision ID: bf39de3abbbb
Revises: 865837abd4b7
Create Date: 2025-12-12 19:15:12.729694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'bf39de3abbbb'
down_revision: Union[str, None] = '865837abd4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - change content and raw_content columns from TEXT to MEDIUMTEXT."""
    # Change content column from TEXT to MEDIUMTEXT
    op.alter_column('source_chunk', 'content',
                    existing_type=sa.Text(),
                    type_=mysql.MEDIUMTEXT(),
                    existing_nullable=True)
    
    # Change raw_content column from TEXT to MEDIUMTEXT
    op.alter_column('source_chunk', 'raw_content',
                    existing_type=sa.Text(),
                    type_=mysql.MEDIUMTEXT(),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema - change content and raw_content columns back to TEXT."""
    # Change content column back to TEXT
    op.alter_column('source_chunk', 'content',
                    existing_type=mysql.MEDIUMTEXT(),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    # Change raw_content column back to TEXT
    op.alter_column('source_chunk', 'raw_content',
                    existing_type=mysql.MEDIUMTEXT(),
                    type_=sa.Text(),
                    existing_nullable=True)
