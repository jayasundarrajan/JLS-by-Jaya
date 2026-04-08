"""add outfits and outfit_items

Revision ID: b71ceb747496
Revises: a088d386a5d5
Create Date: 2026-01-13 10:23:35.130837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b71ceb747496"
down_revision: Union[str, None] = "a088d386a5d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- outfits ---
    op.create_table(
        "outfits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_outfits_user_id", "outfits", ["user_id"])

    # --- outfit_items ---
    op.create_table(
        "outfit_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "outfit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outfits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "closet_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("closet_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("scale", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("rotation", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("z_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_outfit_items_outfit_id", "outfit_items", ["outfit_id"])
    op.create_index("ix_outfit_items_closet_item_id", "outfit_items", ["closet_item_id"])


def downgrade() -> None:
    op.drop_index("ix_outfit_items_closet_item_id", table_name="outfit_items")
    op.drop_index("ix_outfit_items_outfit_id", table_name="outfit_items")
    op.drop_table("outfit_items")

    op.drop_index("ix_outfits_user_id", table_name="outfits")
    op.drop_table("outfits")
