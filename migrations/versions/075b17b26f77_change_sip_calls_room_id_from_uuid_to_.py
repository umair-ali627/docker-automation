"""Change sip_calls room_id from UUID to String

Revision ID: 075b17b26f77
Revises: 1b2d69dc269d
Create Date: 2025-08-28 02:32:26.507466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '075b17b26f77'
down_revision: Union[str, None] = '1b2d69dc269d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
