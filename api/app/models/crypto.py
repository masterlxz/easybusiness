from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CryptoIndicator(Base):
    """Latest known reading of an ETH health indicator (by indicator code,
    see app/sources/crypto_indicator_catalog.py) — one row per indicator,
    overwritten on refresh, no accumulated history."""

    __tablename__ = "crypto_indicators"

    indicator_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    raw_value: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CryptoFearGreed(Base):
    """Latest known global Fear & Greed reading — singleton row (`id` is
    always 1, there's only ever one global reading)."""

    __tablename__ = "crypto_fear_greed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CryptoCoinResolution(Base):
    """Cached symbol -> CoinGecko coin id resolution — one row per symbol,
    overwritten on refresh (a symbol's coin id essentially never changes,
    but this still goes through the same TTL-checked cache-through as
    everything else rather than being treated as permanent)."""

    __tablename__ = "crypto_coin_resolution"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    coin_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CryptoQuote(Base):
    """Latest known quote for a coin (by symbol) — one row per symbol,
    overwritten on refresh (price changes constantly)."""

    __tablename__ = "crypto_quotes"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    coin_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(24, 10), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CryptoPriceHistory(Base):
    """One closing price per (symbol, day) — append-only, a past trading
    day never changes once recorded."""

    __tablename__ = "crypto_price_history"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    price: Mapped[float] = mapped_column(Numeric(24, 10), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
