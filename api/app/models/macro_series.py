from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MacroSeriesMonthly(Base):
    """One monthly data point of a macro series.

    Composite primary key (series_code, reference_month) — the target of
    the upsert's ON CONFLICT, equivalent to the (index_code, year_month)
    pair the Anchor project uses in its `macro_index_monthly` table.
    """

    __tablename__ = "macro_series_monthly"

    series_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    reference_month: Mapped[date] = mapped_column(Date, primary_key=True)
    value_pct: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
