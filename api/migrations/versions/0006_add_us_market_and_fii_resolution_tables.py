"""add us market and fii resolution tables (us_stock_quotes, us_stock_technicals, us_stock_dividends_avg, us_stock_price_history, us_stock_dividend_payments, reit_fundamentals, fii_cnpj_resolution)

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "us_stock_quotes",
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
        "us_stock_technicals",
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
        "us_stock_dividends_avg",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("avg_dividend_5y", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "us_stock_price_history",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("price_date", sa.Date, primary_key=True),
        sa.Column("close_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "us_stock_dividend_payments",
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

    op.create_table(
        "reit_fundamentals",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("reference_year", sa.Integer, primary_key=True),
        sa.Column("revenue", sa.Numeric(18, 6), nullable=False),
        sa.Column("real_estate_property_net", sa.Numeric(18, 6), nullable=True),
        sa.Column("real_estate_property_at_cost", sa.Numeric(18, 6), nullable=True),
        sa.Column("stockholders_equity", sa.Numeric(18, 6), nullable=False),
        sa.Column("net_income", sa.Numeric(18, 6), nullable=True),
        sa.Column("eps_diluted", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "fii_cnpj_resolution",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column("fund_name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("fii_cnpj_resolution")
    op.drop_table("reit_fundamentals")
    op.drop_table("us_stock_dividend_payments")
    op.drop_table("us_stock_price_history")
    op.drop_table("us_stock_dividends_avg")
    op.drop_table("us_stock_technicals")
    op.drop_table("us_stock_quotes")
