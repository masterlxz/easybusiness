from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetalQuote(Base):
    """Latest known quote for a metal (by ISO 4217 code) — one row per
    metal, overwritten on refresh."""

    __tablename__ = "metal_quotes"

    metal_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MetalPriceHistory(Base):
    """One closing price per (metal code, trading day) — append-only, a
    past trading day never changes once recorded."""

    __tablename__ = "metal_price_history"

    metal_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
