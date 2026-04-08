"""add image_path to closet_items

Revision ID: a088d386a5d5
Revises: 90fbdd7185bd
Create Date: 2026-01-08 11:48:28.138145
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a088d386a5d5'
down_revision: Union[str, None] = '90fbdd7185bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "closet_items",
        sa.Column("image_path", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("closet_items", "image_path")
