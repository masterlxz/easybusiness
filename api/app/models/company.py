from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CompanyRoe(Base):
    """Latest known ROE for a company (by CVM code) — one row per company,
    overwritten on refresh (only the most recent fiscal year is ever
    fetched from the source, see app/sources/cvm_dfp.py)."""

    __tablename__ = "company_roe"

    cvm_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)
    roe: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompanyPayoutAvg(Base):
    """Latest known 5-year average payout ratio for a company — same
    overwrite semantics as CompanyRoe."""

    __tablename__ = "company_payout_avg"

    cvm_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    payout_avg_5y: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompanyDcfFundamentals(Base):
    """Latest DCF/FCFF accounting fields for a company — same overwrite
    semantics as CompanyRoe (only the most recent fiscal year is kept;
    `reference_year` is a plain column, not part of the key, since the
    source never returns more than one year per call)."""

    __tablename__ = "company_dcf_fundamentals"

    cvm_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)
    ebit: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    depreciation_amortization: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    capex: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    nwc_change: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    total_debt: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    cash: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    revenue: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    inventory: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
