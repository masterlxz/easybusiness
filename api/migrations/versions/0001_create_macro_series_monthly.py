"""create macro_series_monthly

Revision ID: 0001
Revises:
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "macro_series_monthly",
        sa.Column("series_code", sa.String(32), primary_key=True),
        sa.Column("reference_month", sa.Date, primary_key=True),
        sa.Column("value_pct", sa.Numeric(10, 4), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_macro_series_monthly_series_code",
        "macro_series_monthly",
        ["series_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_macro_series_monthly_series_code", table_name="macro_series_monthly")
    op.drop_table("macro_series_monthly")
