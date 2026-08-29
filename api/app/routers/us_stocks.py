from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.us_stock import (
    ReitFundamentalsResponse,
    UsStockDcfFundamentalsResponse,
    UsStockDividendPaymentsResponse,
    UsStockDividendsAvgResponse,
    UsStockFundamentalsResponse,
    UsStockPayoutResponse,
    UsStockPriceHistoryResponse,
    UsStockQuoteResponse,
    UsStockTechnicalsResponse,
)
from app.services.us_stock_service import (
    NoDividendDataError,
    NoFundamentalsDataError,
    TickerNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_fundamentals,
    get_or_refresh_payout,
    get_or_refresh_reit_fundamentals,
    get_or_refresh_us_dividend_payments,
    get_or_refresh_us_dividends_avg,
    get_or_refresh_us_price_history,
    get_or_refresh_us_quote,
    get_or_refresh_us_technicals,
)
from app.sources.acoes_yahoo import YahooFinanceError
from app.sources.sec_edgar import SecEdgarError

router = APIRouter(prefix="/v1/us-stocks/{ticker}", tags=["us-stocks"])

SOURCE_UNAVAILABLE_DETAIL = "Failed to fetch data from SEC EDGAR and no cached data available"
YAHOO_UNAVAILABLE_DETAIL = "Failed to fetch data from Yahoo Finance and no cached data available"


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


@router.get("/reit-fundamentals", response_model=ReitFundamentalsResponse)
def get_reit_fundamentals(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_reit_fundamentals(
            db, ticker, settings.cache_ttl_seconds, settings.fundamentals_ttl_seconds,
            settings.sec_edgar_contact_email,
        )
    except TickerNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown ticker: {ticker}")
    except SecEdgarError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=SOURCE_UNAVAILABLE_DETAIL)


# --- Fase 1.11.1 — Yahoo Finance without the ".SA" suffix ------------------
# Same 5 resources as /v1/stocks/{ticker}/..., for a no-suffix ticker (US
# stock, ETF-US, REIT, or a no-suffix index such as ^BVSP/IBOV).


@router.get("/quote", response_model=UsStockQuoteResponse)
def get_us_quote(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_us_quote(db, ticker, settings.stock_quote_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=YAHOO_UNAVAILABLE_DETAIL)


@router.get("/technicals", response_model=UsStockTechnicalsResponse)
def get_us_technicals(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_us_technicals(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=YAHOO_UNAVAILABLE_DETAIL)


@router.get("/dividends-avg", response_model=UsStockDividendsAvgResponse)
def get_us_dividends_avg(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_us_dividends_avg(db, ticker, settings.cache_ttl_seconds)
    except NoDividendDataError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No dividend data available for {ticker}"
        )
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=YAHOO_UNAVAILABLE_DETAIL)


@router.get("/price-history", response_model=UsStockPriceHistoryResponse)
def get_us_price_history(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_us_price_history(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=YAHOO_UNAVAILABLE_DETAIL)


@router.get("/dividend-payments", response_model=UsStockDividendPaymentsResponse)
def get_us_dividend_payments(
    ticker: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(require_api_key),
):
    try:
        return get_or_refresh_us_dividend_payments(db, ticker, settings.cache_ttl_seconds)
    except YahooFinanceError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=YAHOO_UNAVAILABLE_DETAIL)
