from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, func
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


# --- Fase 1.11.1 — Yahoo Finance without the ".SA" suffix (US stocks, ---
# --- ETF-US, REIT, and no-suffix indices such as IBOV/^BVSP) -----------
# Same 5-table shape as app.models.stock, reusing app.sources.acoes_yahoo
# with suffix="" instead of the ".SA" default.


class UsStockQuote(Base):
    """Latest known quote for a no-suffix ticker — one row per ticker,
    overwritten on every refresh, same semantics as stock.StockQuote."""

    __tablename__ = "us_stock_quotes"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockTechnicals(Base):
    """Latest SMA/CAGR snapshot for a no-suffix ticker — one row per
    ticker, same overwrite semantics as UsStockQuote."""

    __tablename__ = "us_stock_technicals"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    sma_50: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    sma_100: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    sma_200: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    cagr_5y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cagr_10y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockDividendsAvg(Base):
    """Latest 5-year average dividend per share for a no-suffix ticker —
    one row per ticker, same overwrite semantics as UsStockQuote."""

    __tablename__ = "us_stock_dividends_avg"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    avg_dividend_5y: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockPriceHistory(Base):
    """One closing price per (ticker, trading day) — append-only, a past
    trading day never changes once recorded."""

    __tablename__ = "us_stock_price_history"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsStockDividendPayment(Base):
    """One dividend payment per (ticker, payment date) — append-only, a
    past payment never changes once recorded."""

    __tablename__ = "us_stock_dividend_payments"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    payment_date: Mapped[date] = mapped_column(Date, primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    price_at_payment: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    yield_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ReitFundamentals(Base):
    """Fase 1.11.2 — REIT real-estate indicators via SEC EDGAR. Time-series,
    not overwritten: one INSERT per fetch, keyed by (ticker, reference_year),
    same append-only shape as UsStockPriceHistory rather than the
    single-row-per-ticker shape of UsStockFundamentals — a REIT's own SEC
    filings only add one new fiscal year at a time, so history naturally
    accumulates instead of being replaced. FFO/AFFO/occupancy aren't XBRL
    tags in any taxonomy (confirmed live against Realty Income, Simon
    Property, Prologis, AvalonBay) — this table only holds what the SEC
    exposes automatically. `real_estate_property_net`/`_at_cost` and
    `net_income` are nullable — not every REIT's taxonomy reports them
    consistently (e.g. Simon Property, an UPREIT, reports `ProfitLoss`
    instead of `NetIncomeLoss`)."""

    __tablename__ = "reit_fundamentals"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    reference_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    revenue: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    real_estate_property_net: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    real_estate_property_at_cost: Mapped[float | None] = mapped_column(
        Numeric(18, 6), nullable=True
    )
    stockholders_equity: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    net_income: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    eps_diluted: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
