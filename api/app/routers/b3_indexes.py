from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.b3_index import B3IndexHistoryResponse
from app.services.b3_index_service import UnknownIndexError, get_or_refresh_index_history
from app.sources.b3_index_stats import B3IndexStatsError

router = APIRouter(prefix="/v1/b3-indexes/{index_code}", tags=["b3-indexes"])


@router.get("/history", response_model=B3IndexHistoryResponse)
def get_index_history(
    index_code: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_index_history(db, index_code, settings.cache_ttl_seconds)
    except UnknownIndexError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown index code: {index_code}")
    except B3IndexStatsError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch data from B3 and no cached data available",
        )
