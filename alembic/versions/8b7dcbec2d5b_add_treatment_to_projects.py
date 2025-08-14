"""add treatment to projects

Revision ID: 8b7dcbec2d5b
Revises: 6e5f66eedef6
Create Date: 2024-09-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8b7dcbec2d5b'
down_revision = '6e5f66eedef6'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('projects', sa.Column('treatment', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('projects', 'treatment')
