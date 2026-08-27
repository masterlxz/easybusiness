"""create stock tables (quotes, technicals, dividends_avg, price_history, dividend_payments)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_quotes",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("exchange", sa.String(64), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "stock_technicals",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("sma_50", sa.Numeric(18, 6), nullable=True),
        sa.Column("sma_100", sa.Numeric(18, 6), nullable=True),
        sa.Column("sma_200", sa.Numeric(18, 6), nullable=True),
        sa.Column("cagr_5y", sa.Numeric(10, 4), nullable=True),
        sa.Column("cagr_10y", sa.Numeric(10, 4), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "stock_dividends_avg",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("avg_dividend_5y", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "stock_price_history",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("price_date", sa.Date, primary_key=True),
        sa.Column("close_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_stock_price_history_ticker", "stock_price_history", ["ticker"]
    )

    op.create_table(
        "stock_dividend_payments",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("payment_date", sa.Date, primary_key=True),
        sa.Column("amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("price_at_payment", sa.Numeric(18, 6), nullable=True),
        sa.Column("yield_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_stock_dividend_payments_ticker", "stock_dividend_payments", ["ticker"]
    )


def downgrade() -> None:
    op.drop_index("ix_stock_dividend_payments_ticker", table_name="stock_dividend_payments")
    op.drop_table("stock_dividend_payments")
    op.drop_index("ix_stock_price_history_ticker", table_name="stock_price_history")
    op.drop_table("stock_price_history")
    op.drop_table("stock_dividends_avg")
    op.drop_table("stock_technicals")
    op.drop_table("stock_quotes")
