"""increase_article_section_content_size

Revision ID: 7df0f866a9bb
Revises: bf39de3abbbb
Create Date: 2025-12-12 19:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '7df0f866a9bb'
down_revision: Union[str, None] = 'bf39de3abbbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - change article_section.content and source_event.content from TEXT to MEDIUMTEXT."""
    # Change article_section.content column from TEXT to MEDIUMTEXT
    op.alter_column('article_section', 'content',
                    existing_type=sa.Text(),
                    type_=mysql.MEDIUMTEXT(),
                    existing_nullable=False)
    
    # Change source_event.content column from TEXT to MEDIUMTEXT
    op.alter_column('source_event', 'content',
                    existing_type=sa.Text(),
                    type_=mysql.MEDIUMTEXT(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema - change article_section.content and source_event.content back to TEXT."""
    # Change article_section.content column back to TEXT
    op.alter_column('article_section', 'content',
                    existing_type=mysql.MEDIUMTEXT(),
                    type_=sa.Text(),
                    existing_nullable=False)
    
    # Change source_event.content column back to TEXT
    op.alter_column('source_event', 'content',
                    existing_type=mysql.MEDIUMTEXT(),
                    type_=sa.Text(),
                    existing_nullable=False)
