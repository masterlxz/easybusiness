from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.fii import FiiMonthlyIndicatorsResponse, FiiPropertiesResponse
from app.services.fii_service import (
    FundNotFoundError,
    get_or_refresh_monthly_indicators,
    get_or_refresh_properties,
)
from app.sources.cvm_fii import CvmFiiDataError

router = APIRouter(prefix="/v1/fiis/{cnpj}", tags=["fiis"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from CVM and no cached data available"


@router.get("/monthly-indicators", response_model=FiiMonthlyIndicatorsResponse)
def get_monthly_indicators(
    cnpj: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_monthly_indicators(db, cnpj, settings.cvm_ttl_seconds)
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
        return get_or_refresh_properties(db, cnpj, settings.cvm_ttl_seconds)
    except CvmFiiDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
