from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StockQuote(Base):
    """Latest known quote for a ticker — one row per ticker, overwritten on
    every refresh (price changes constantly, unlike the append-only tables
    below)."""

    __tablename__ = "stock_quotes"

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


class StockTechnicals(Base):
    """Latest SMA/CAGR snapshot for a ticker — one row per ticker, same
    overwrite semantics as StockQuote."""

    __tablename__ = "stock_technicals"

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


class StockDividendsAvg(Base):
    """Latest 5-year average dividend per share for a ticker — one row per
    ticker, same overwrite semantics as StockQuote."""

    __tablename__ = "stock_dividends_avg"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    avg_dividend_5y: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StockPriceHistory(Base):
    """One closing price per (ticker, trading day) — append-only, a past
    trading day never changes once recorded."""

    __tablename__ = "stock_price_history"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StockDividendPayment(Base):
    """One dividend payment per (ticker, payment date) — append-only, a
    past payment never changes once recorded."""

    __tablename__ = "stock_dividend_payments"

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


class StockBolsaiFundamentals(Base):
    """Latest bolsai fundamentals snapshot for a ticker — one row per
    ticker, overwritten on refresh. `roe` is known to be less reliable than
    the CVM-computed one (see app/sources/acoes_bolsai.py); exposed as-is
    regardless. `cvm_code` lets a caller chain into
    `/v1/companies/{cvm_code}/...` without a separate resolution step."""

    __tablename__ = "stock_bolsai_fundamentals"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    lpa: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    vpa: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    roe: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    shares_outstanding: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    cvm_code: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
