from datetime import date, datetime

from pydantic import BaseModel


class StockQuoteResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    price: float
    name: str | None
    exchange: str | None
    currency: str | None

    model_config = {"from_attributes": True}


class StockTechnicalsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    sma_50: float | None
    sma_100: float | None
    sma_200: float | None
    cagr_5y: float | None
    cagr_10y: float | None

    model_config = {"from_attributes": True}


class StockDividendsAvgResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    avg_dividend_5y: float

    model_config = {"from_attributes": True}


class StockPriceHistoryPoint(BaseModel):
    price_date: date
    close_price: float

    model_config = {"from_attributes": True}


class StockPriceHistoryResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[StockPriceHistoryPoint]

    model_config = {"from_attributes": True}


class StockDividendPaymentPoint(BaseModel):
    payment_date: date
    amount: float
    price_at_payment: float | None
    yield_pct: float | None

    model_config = {"from_attributes": True}


class StockDividendPaymentsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[StockDividendPaymentPoint]

    model_config = {"from_attributes": True}


class StockBolsaiFundamentalsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    lpa: float
    vpa: float
    roe: float
    shares_outstanding: float
    cvm_code: str

    model_config = {"from_attributes": True}
