"""create crypto tables (crypto_indicators, crypto_fear_greed, crypto_coin_resolution, crypto_quotes, crypto_price_history)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-28

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "crypto_indicators",
        sa.Column("indicator_code", sa.String(32), primary_key=True),
        sa.Column("raw_value", sa.Numeric(18, 8), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "crypto_fear_greed",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("value", sa.Integer, nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("reading_date", sa.Date, nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "crypto_coin_resolution",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("coin_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "crypto_quotes",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("coin_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(24, 10), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "crypto_price_history",
        sa.Column("symbol", sa.String(32), primary_key=True),
        sa.Column("price_date", sa.Date, primary_key=True),
        sa.Column("price", sa.Numeric(24, 10), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_crypto_price_history_symbol", "crypto_price_history", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_crypto_price_history_symbol", table_name="crypto_price_history")
    op.drop_table("crypto_price_history")
    op.drop_table("crypto_quotes")
    op.drop_table("crypto_coin_resolution")
    op.drop_table("crypto_fear_greed")
    op.drop_table("crypto_indicators")
