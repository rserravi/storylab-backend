"""move synopsis and treatment to screenplays

Revision ID: b693b67d3b9a
Revises: 0c1f90e75094
Create Date: 2024-01-01 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b693b67d3b9a"
down_revision: Union[str, Sequence[str], None] = "0c1f90e75094"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("screenplays", sa.Column("synopsis", sa.Text(), nullable=True))
    op.add_column("screenplays", sa.Column("treatment", sa.Text(), nullable=True))
    op.drop_column("projects", "synopsis")
    op.drop_column("projects", "treatment")


def downgrade() -> None:
    op.add_column("projects", sa.Column("treatment", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("synopsis", sa.Text(), nullable=True))
    op.drop_column("screenplays", "treatment")
    op.drop_column("screenplays", "synopsis")
