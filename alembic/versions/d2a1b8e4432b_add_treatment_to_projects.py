"""add treatment to projects

Revision ID: d2a1b8e4432b
Revises: 6e5f66eedef6
Create Date: 2024-10-07 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd2a1b8e4432b'
down_revision: Union[str, Sequence[str], None] = '6e5f66eedef6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('treatment', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'treatment')
