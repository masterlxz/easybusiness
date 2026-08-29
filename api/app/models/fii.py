from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FiiMonthlyIndicator(Base):
    """Latest known monthly report for a fund (by CNPJ, digits-only) — one
    row per fund, overwritten on refresh (only the most recent month is
    ever fetched from the source)."""

    __tablename__ = "fii_monthly_indicators"

    cnpj: Mapped[str] = mapped_column(String(14), primary_key=True)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    patrimonio_liquido: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    valor_patrimonial_cota: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    numero_cotistas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dividend_yield_mes: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    rentabilidade_efetiva_mes: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FiiCnpjResolution(Base):
    """Fase 1.11.3 — cached ticker -> fund CNPJ resolution, one row per
    ticker, overwritten on refresh. Essentially permanent (a fund's CNPJ
    never changes), same reasoning as SecEdgarCikResolution/
    CryptoCoinResolution."""

    __tablename__ = "fii_cnpj_resolution"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FiiProperty(Base):
    """One property from a fund's latest quarterly report — refreshed via
    delete-then-insert per CNPJ (see app/services/fii_service.py), not
    upsert: a fund's property list for the latest quarter is a full
    snapshot, not an accumulating history, so a property no longer
    reported must disappear rather than linger as stale data."""

    __tablename__ = "fii_properties"

    cnpj: Mapped[str] = mapped_column(String(14), primary_key=True)
    nome_imovel: Mapped[str] = mapped_column(String(255), primary_key=True)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    endereco: Mapped[str | None] = mapped_column(String(500), nullable=True)
    area_m2: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    percentual_vacancia: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    percentual_inadimplencia: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    percentual_receitas_fii: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    percentual_locado: Mapped[float | None] = mapped_column(Numeric(8, 6), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
