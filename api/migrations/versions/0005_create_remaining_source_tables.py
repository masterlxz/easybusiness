"""create remaining source tables (b3_index_history, metal_quotes, metal_price_history, stock_bolsai_fundamentals, sec_edgar_cik_resolution, us_stock_fundamentals, us_stock_dcf_fundamentals, us_stock_payout_avg)

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-28

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "b3_index_history",
        sa.Column("index_code", sa.String(16), primary_key=True),
        sa.Column("price_date", sa.Date, primary_key=True),
        sa.Column("close_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "metal_quotes",
        sa.Column("metal_code", sa.String(8), primary_key=True),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "metal_price_history",
        sa.Column("metal_code", sa.String(8), primary_key=True),
        sa.Column("price_date", sa.Date, primary_key=True),
        sa.Column("close_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "stock_bolsai_fundamentals",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("lpa", sa.Numeric(18, 6), nullable=False),
        sa.Column("vpa", sa.Numeric(18, 6), nullable=False),
        sa.Column("roe", sa.Numeric(10, 4), nullable=False),
        sa.Column("shares_outstanding", sa.Numeric(20, 2), nullable=False),
        sa.Column("cvm_code", sa.String(16), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "sec_edgar_cik_resolution",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("cik", sa.BigInteger, nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "us_stock_fundamentals",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("lpa", sa.Numeric(18, 6), nullable=False),
        sa.Column("vpa", sa.Numeric(18, 6), nullable=False),
        sa.Column("roe", sa.Numeric(10, 4), nullable=False),
        sa.Column("shares_outstanding", sa.Numeric(20, 2), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "us_stock_dcf_fundamentals",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("reference_year", sa.Integer, nullable=False),
        sa.Column("ebit", sa.Numeric(18, 6), nullable=False),
        sa.Column("tax_rate", sa.Numeric(10, 4), nullable=True),
        sa.Column("depreciation_amortization", sa.Numeric(18, 6), nullable=True),
        sa.Column("capex", sa.Numeric(18, 6), nullable=True),
        sa.Column("nwc_change", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_debt", sa.Numeric(18, 6), nullable=False),
        sa.Column("cash", sa.Numeric(18, 6), nullable=False),
        sa.Column("revenue", sa.Numeric(18, 6), nullable=False),
        sa.Column("inventory", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "us_stock_payout_avg",
        sa.Column("ticker", sa.String(32), primary_key=True),
        sa.Column("payout_avg_5y", sa.Numeric(10, 4), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("us_stock_payout_avg")
    op.drop_table("us_stock_dcf_fundamentals")
    op.drop_table("us_stock_fundamentals")
    op.drop_table("sec_edgar_cik_resolution")
    op.drop_table("stock_bolsai_fundamentals")
    op.drop_table("metal_price_history")
    op.drop_table("metal_quotes")
    op.drop_table("b3_index_history")
