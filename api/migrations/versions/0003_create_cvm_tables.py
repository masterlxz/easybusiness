"""create CVM tables (company_roe, company_payout_avg, company_dcf_fundamentals, fii_monthly_indicators, fii_properties)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_roe",
        sa.Column("cvm_code", sa.Integer, primary_key=True),
        sa.Column("reference_year", sa.Integer, nullable=False),
        sa.Column("roe", sa.Numeric(10, 4), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "company_payout_avg",
        sa.Column("cvm_code", sa.Integer, primary_key=True),
        sa.Column("payout_avg_5y", sa.Numeric(10, 4), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "company_dcf_fundamentals",
        sa.Column("cvm_code", sa.Integer, primary_key=True),
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
        "fii_monthly_indicators",
        sa.Column("cnpj", sa.String(14), primary_key=True),
        sa.Column("reference_date", sa.Date, nullable=False),
        sa.Column("patrimonio_liquido", sa.Numeric(18, 2), nullable=False),
        sa.Column("valor_patrimonial_cota", sa.Numeric(18, 6), nullable=False),
        sa.Column("numero_cotistas", sa.Integer, nullable=True),
        sa.Column("dividend_yield_mes", sa.Numeric(10, 6), nullable=True),
        sa.Column("rentabilidade_efetiva_mes", sa.Numeric(10, 6), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "fii_properties",
        sa.Column("cnpj", sa.String(14), primary_key=True),
        sa.Column("nome_imovel", sa.String(255), primary_key=True),
        sa.Column("reference_date", sa.Date, nullable=False),
        sa.Column("endereco", sa.String(500), nullable=True),
        sa.Column("area_m2", sa.Numeric(14, 2), nullable=True),
        sa.Column("percentual_vacancia", sa.Numeric(8, 6), nullable=True),
        sa.Column("percentual_inadimplencia", sa.Numeric(8, 6), nullable=True),
        sa.Column("percentual_receitas_fii", sa.Numeric(8, 6), nullable=True),
        sa.Column("percentual_locado", sa.Numeric(8, 6), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("fii_properties")
    op.drop_table("fii_monthly_indicators")
    op.drop_table("company_dcf_fundamentals")
    op.drop_table("company_payout_avg")
    op.drop_table("company_roe")
