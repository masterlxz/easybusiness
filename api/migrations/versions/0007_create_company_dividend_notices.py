"""create company_dividend_notices

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_dividend_notices",
        sa.Column("cvm_code", sa.Integer, primary_key=True),
        sa.Column("protocolo_entrega", sa.String(512), primary_key=True),
        sa.Column("data_entrega", sa.Date, nullable=False),
        sa.Column("link_download", sa.String(512), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("company_dividend_notices")
