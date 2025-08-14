"""add synopsis to projects

Revision ID: 6e5f66eedef6
Revises: aae5779358b8
Create Date: 2024-10-07 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6e5f66eedef6'
down_revision: Union[str, Sequence[str], None] = 'aae5779358b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('synopsis', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'synopsis')
