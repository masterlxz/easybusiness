from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.crypto import (
    CryptoFearGreedResponse,
    CryptoIndicatorResponse,
    CryptoPriceHistoryResponse,
    CryptoQuoteResponse,
)
from app.services.crypto_service import (
    CoinNotFoundError,
    UnknownIndicatorError,
    get_or_refresh_eth_indicator,
    get_or_refresh_fear_greed,
    get_or_refresh_price_history,
    get_or_refresh_quote,
)
from app.sources.crypto_common import CryptoDataError

router = APIRouter(prefix="/v1/crypto", tags=["crypto"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from the crypto source and no cached data available"


@router.get("/eth-indicators/{indicator_code}", response_model=CryptoIndicatorResponse)
def get_eth_indicator(
    indicator_code: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_eth_indicator(db, indicator_code, settings.cache_ttl_seconds)
    except UnknownIndicatorError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Unknown indicator code: {indicator_code}"
        )
    except CryptoDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/fear-greed", response_model=CryptoFearGreedResponse)
def get_fear_greed(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_fear_greed(db, settings.cache_ttl_seconds)
    except CryptoDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/{symbol}/quote", response_model=CryptoQuoteResponse)
def get_quote(
    symbol: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_quote(
            db, symbol, settings.cache_ttl_seconds, settings.crypto_quote_ttl_seconds
        )
    except CoinNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown coin symbol: {symbol}")
    except CryptoDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/{symbol}/price-history", response_model=CryptoPriceHistoryResponse)
def get_price_history(
    symbol: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_price_history(
            db, symbol, settings.cache_ttl_seconds, settings.cache_ttl_seconds
        )
    except CoinNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown coin symbol: {symbol}")
    except CryptoDataError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
