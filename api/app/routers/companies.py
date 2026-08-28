from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.company import (
    CompanyDcfFundamentalsResponse,
    CompanyPayoutResponse,
    CompanyRoeResponse,
)
from app.services.company_service import (
    CompanyNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_payout,
    get_or_refresh_roe,
)
from app.sources.cvm_dfp import CvmDataError

router = APIRouter(prefix="/v1/companies/{cvm_code}", tags=["companies"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from CVM and no cached data available"


@router.get("/roe", response_model=CompanyRoeResponse)
def get_roe(
    cvm_code: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_roe(db, cvm_code, settings.fundamentals_ttl_seconds)
    except CompanyNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No ROE data available for CVM code {cvm_code}"
        )
    except CvmDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/payout", response_model=CompanyPayoutResponse)
def get_payout(
    cvm_code: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_payout(db, cvm_code, settings.fundamentals_ttl_seconds)
    except CompanyNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No payout data available for CVM code {cvm_code}"
        )
    except CvmDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/dcf-fundamentals", response_model=CompanyDcfFundamentalsResponse)
def get_dcf_fundamentals(
    cvm_code: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_dcf_fundamentals(db, cvm_code, settings.fundamentals_ttl_seconds)
    except CompanyNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"No DCF fundamentals available for CVM code {cvm_code}",
        )
    except CvmDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
