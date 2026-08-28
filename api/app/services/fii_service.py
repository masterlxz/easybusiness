"""Cache-through orchestration for CVM FII (real estate fund) data.

`monthly_indicators` is "1 row per CNPJ, overwritten on refresh" (see
app/services/single_row_cache.py) — same shape as the company fundamentals
services. `properties` is different: a fund can have several properties in
its latest quarterly report, but it's still only ever the *latest*
snapshot, not an accumulating history — refreshing deletes the fund's
existing rows and inserts the fresh set in one transaction, so a property
no longer reported disappears instead of lingering as stale data.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.fii import FiiMonthlyIndicator, FiiProperty
from app.services.freshness import is_fresh
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.cvm_fii import (
    CvmFiiDataError,
    fetch_monthly_indicators,
    fetch_property_data,
    normalize_cnpj,
)

logger = logging.getLogger(__name__)

SOURCE_NAME = "cvm_fii"


class FundNotFoundError(ValueError):
    """Raised when a CNPJ has no data of the requested kind and no cache
    exists — a legitimate absence of data, not a source failure."""


def get_or_refresh_monthly_indicators(db: Session, cnpj: str, ttl_seconds: int) -> dict:
    cnpj_digits = normalize_cnpj(cnpj)
    row, cached, stale = get_or_refresh_single_row(
        db, FiiMonthlyIndicator, FiiMonthlyIndicator.cnpj, cnpj_digits, ttl_seconds,
        fetch_monthly_indicators, SOURCE_NAME, CvmFiiDataError, FundNotFoundError,
    )
    return {
        "cnpj": cnpj_digits,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "reference_date": row.reference_date,
        "patrimonio_liquido": row.patrimonio_liquido,
        "valor_patrimonial_cota": row.valor_patrimonial_cota,
        "numero_cotistas": row.numero_cotistas,
        "dividend_yield_mes": row.dividend_yield_mes,
        "rentabilidade_efetiva_mes": row.rentabilidade_efetiva_mes,
    }


def get_or_refresh_properties(db: Session, cnpj: str, ttl_seconds: int) -> dict:
    cnpj_digits = normalize_cnpj(cnpj)

    latest_fetched_at = db.scalar(
        select(func.max(FiiProperty.fetched_at)).where(FiiProperty.cnpj == cnpj_digits)
    )

    cached, stale = True, False
    if not is_fresh(latest_fetched_at, ttl_seconds):
        try:
            items = fetch_property_data(cnpj_digits)
            now = datetime.now(timezone.utc)
            db.execute(delete(FiiProperty).where(FiiProperty.cnpj == cnpj_digits))
            if items:
                db.add_all(
                    [
                        FiiProperty(
                            cnpj=cnpj_digits,
                            nome_imovel=item["nome_imovel"],
                            reference_date=item["reference_date"],
                            endereco=item["endereco"],
                            area_m2=item["area_m2"],
                            percentual_vacancia=item["percentual_vacancia"],
                            percentual_inadimplencia=item["percentual_inadimplencia"],
                            percentual_receitas_fii=item["percentual_receitas_fii"],
                            percentual_locado=item["percentual_locado"],
                            source=SOURCE_NAME,
                            fetched_at=now,
                        )
                        for item in items
                    ]
                )
            db.commit()
            cached = False
        except CvmFiiDataError:
            if latest_fetched_at is None:
                raise
            logger.warning("CVM FII unavailable for %s, serving stale cache", cnpj_digits)
            stale = True

    rows = db.scalars(
        select(FiiProperty).where(FiiProperty.cnpj == cnpj_digits).order_by(FiiProperty.nome_imovel)
    ).all()

    return {
        "cnpj": cnpj_digits,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
