from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecEdgarCikResolution(Base):
    """Cached ticker -> SEC CIK resolution — one row per ticker, overwritten
    on refresh (a ticker's CIK essentially never changes, same reasoning as
    CryptoCoinResolution)."""

    __tablename__ = "sec_edgar_cik_resolution"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    cik: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockFundamentals(Base):
    """Latest known LPA/VPA/ROE snapshot for a US ticker — one row per
    ticker, overwritten on refresh (only the most recent fiscal year is
    ever fetched from the source)."""

    __tablename__ = "us_stock_fundamentals"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    lpa: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    vpa: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    roe: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    shares_outstanding: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockDcfFundamentals(Base):
    """Latest DCF/FCFF accounting fields for a US ticker — same overwrite
    semantics as UsStockFundamentals."""

    __tablename__ = "us_stock_dcf_fundamentals"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
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


class UsStockPayoutAvg(Base):
    """Latest known 5-year average payout ratio for a US ticker — same
    overwrite semantics as UsStockFundamentals."""

    __tablename__ = "us_stock_payout_avg"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    payout_avg_5y: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
