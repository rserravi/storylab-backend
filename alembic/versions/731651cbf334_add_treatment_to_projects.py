"""add treatment to projects

Revision ID: 731651cbf334
Revises: 6e5f66eedef6
Create Date: 2025-08-14 00:00:00.000000+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "731651cbf334"
down_revision: Union[str, Sequence[str], None] = "6e5f66eedef6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("treatment", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "treatment")
