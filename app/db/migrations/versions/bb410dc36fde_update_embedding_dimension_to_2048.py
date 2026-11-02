"""update embedding dimension to 2048

Revision ID: bb410dc36fde
Revises: eb7f9e32ed2d
Create Date: 2026-10-28 20:46:14.351124

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = "bb410dc36fde"
down_revision: Union[str, Sequence[str], None] = "eb7f9e32ed2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("document_chunks", "embedding")
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding", pgvector.sqlalchemy.vector.VECTOR(dim=2048), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True
        ),
    )
    # ### end Alembic commands ###
