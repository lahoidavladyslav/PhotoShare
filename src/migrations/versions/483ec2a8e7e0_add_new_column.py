"""Add new column

Revision ID: 483ec2a8e7e0
Revises: 92ad42dd9de9
Create Date: 2026-05-18 12:00:41.863024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '483ec2a8e7e0'
down_revision: Union[str, None] = '92ad42dd9de9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
