from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.macro_series import MacroSeriesResponse
from app.services.macro_series_service import UnknownSeriesError, get_or_refresh_series
from app.sources.bcb_sgs import BcbSgsError

router = APIRouter(prefix="/v1/macro-series", tags=["macro-series"])


@router.get("/{series_code}", response_model=MacroSeriesResponse)
def get_macro_series(
    series_code: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_series(db, series_code, settings.cache_ttl_seconds)
    except UnknownSeriesError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Unknown series code: {series_code}"
        )
    except BcbSgsError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from BCB SGS and no cached data available",
        )
