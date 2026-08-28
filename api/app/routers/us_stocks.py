from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.us_stock import (
    UsStockDcfFundamentalsResponse,
    UsStockFundamentalsResponse,
    UsStockPayoutResponse,
)
from app.services.us_stock_service import (
    NoFundamentalsDataError,
    TickerNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_fundamentals,
    get_or_refresh_payout,
)
from app.sources.sec_edgar import SecEdgarError

router = APIRouter(prefix="/v1/us-stocks/{ticker}", tags=["us-stocks"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from SEC EDGAR and no cached data available"


@router.get("/fundamentals", response_model=UsStockFundamentalsResponse)
def get_fundamentals(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_fundamentals(
            db, ticker, settings.cache_ttl_seconds, settings.fundamentals_ttl_seconds,
            settings.sec_edgar_contact_email,
        )
    except TickerNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown ticker: {ticker}")
    except NoFundamentalsDataError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No fundamentals available for {ticker}"
        )
    except SecEdgarError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/dcf-fundamentals", response_model=UsStockDcfFundamentalsResponse)
def get_dcf_fundamentals(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_dcf_fundamentals(
            db, ticker, settings.cache_ttl_seconds, settings.fundamentals_ttl_seconds,
            settings.sec_edgar_contact_email,
        )
    except TickerNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown ticker: {ticker}")
    except NoFundamentalsDataError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No DCF fundamentals available for {ticker}"
        )
    except SecEdgarError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/payout", response_model=UsStockPayoutResponse)
def get_payout(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_payout(
            db, ticker, settings.cache_ttl_seconds, settings.fundamentals_ttl_seconds,
            settings.sec_edgar_contact_email,
        )
    except TickerNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown ticker: {ticker}")
    except NoFundamentalsDataError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No payout data available for {ticker}"
        )
    except SecEdgarError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
