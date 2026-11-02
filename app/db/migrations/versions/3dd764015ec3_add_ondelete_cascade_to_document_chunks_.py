"""add ondelete cascade to document_chunks fk

Revision ID: 3dd764015ec3
Revises: bb410dc36fde
Create Date: 2026-11-02 12:55:53.780535

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3dd764015ec3"
down_revision: Union[str, Sequence[str], None] = "bb410dc36fde"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "document_chunks_document_id_fkey", "document_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "document_chunks_document_id_fkey", "document_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "documents",
        ["document_id"],
        ["id"],
    )
