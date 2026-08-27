from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.stock import (
    StockDividendPaymentsResponse,
    StockDividendsAvgResponse,
    StockPriceHistoryResponse,
    StockQuoteResponse,
    StockTechnicalsResponse,
)
from app.services.stock_service import (
    NoDividendDataError,
    get_or_refresh_dividend_payments,
    get_or_refresh_dividends_avg,
    get_or_refresh_price_history,
    get_or_refresh_quote,
    get_or_refresh_technicals,
)
from app.sources.acoes_yahoo import YahooFinanceError

router = APIRouter(prefix="/v1/stocks/{ticker}", tags=["stocks"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from Yahoo Finance and no cached data available"


@router.get("/quote", response_model=StockQuoteResponse)
def get_quote(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_quote(db, ticker, settings.stock_quote_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/technicals", response_model=StockTechnicalsResponse)
def get_technicals(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_technicals(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/dividends-avg", response_model=StockDividendsAvgResponse)
def get_dividends_avg(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_dividends_avg(db, ticker, settings.cache_ttl_seconds)
    except NoDividendDataError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No dividend data available for {ticker}"
        )
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/price-history", response_model=StockPriceHistoryResponse)
def get_price_history(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_price_history(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


@router.get("/dividend-payments", response_model=StockDividendPaymentsResponse)
def get_dividend_payments(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_dividend_payments(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)
