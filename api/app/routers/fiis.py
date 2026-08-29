from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.fii import (
    FiiCnpjResolutionResponse,
    FiiMonthlyIndicatorsResponse,
    FiiPropertiesResponse,
)
from app.services.fii_service import (
    FundNotFoundError,
    TickerNotResolvedError,
    get_or_refresh_cnpj_resolution,
    get_or_refresh_monthly_indicators,
    get_or_refresh_properties,
)
from app.sources.acoes_bolsai import BolsaiError
from app.sources.cvm_fii import CvmFiiDataError

router = APIRouter(prefix="/v1/fiis/{cnpj}", tags=["fiis"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from CVM and no cached data available"

# Separate router: the ticker->CNPJ resolution (Fase 1.11.3) is keyed by
# ticker, not CNPJ, so it can't share the `{cnpj}`-prefixed router above.
# No route collision — every path under the router above always has a
# literal segment after the CNPJ ("monthly-indicators"/"properties"), while
# "resolve/{ticker}" is a distinct 2-segment shape.
resolve_router = APIRouter(prefix="/v1/fiis", tags=["fiis"])


@resolve_router.get("/resolve/{ticker}", response_model=FiiCnpjResolutionResponse)
def get_cnpj_resolution(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_cnpj_resolution(
            db, ticker, settings.fundamentals_ttl_seconds, settings.bolsai_api_key
        )
    except TickerNotResolvedError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Could not resolve ticker to a CNPJ: {ticker}"
        )
    except (CvmFiiDataError, BolsaiError):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/monthly-indicators", response_model=FiiMonthlyIndicatorsResponse)
def get_monthly_indicators(
    cnpj: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_monthly_indicators(db, cnpj, settings.fundamentals_ttl_seconds)
    except FundNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No monthly indicators available for CNPJ {cnpj}"
        )
    except CvmFiiDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/properties", response_model=FiiPropertiesResponse)
def get_properties(
    cnpj: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_properties(db, cnpj, settings.fundamentals_ttl_seconds)
    except CvmFiiDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
