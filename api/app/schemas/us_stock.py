from datetime import date, datetime

from pydantic import BaseModel


class UsStockFundamentalsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    lpa: float
    vpa: float
    roe: float
    shares_outstanding: float

    model_config = {"from_attributes": True}


class UsStockDcfFundamentalsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    reference_year: int
    ebit: float
    tax_rate: float | None
    depreciation_amortization: float | None
    capex: float | None
    nwc_change: float
    total_debt: float
    cash: float
    revenue: float
    inventory: float

    model_config = {"from_attributes": True}


class UsStockPayoutResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    payout_avg_5y: float

    model_config = {"from_attributes": True}


class ReitFundamentalsPoint(BaseModel):
    reference_year: int
    revenue: float
    real_estate_property_net: float | None
    real_estate_property_at_cost: float | None
    stockholders_equity: float
    net_income: float | None
    eps_diluted: float

    model_config = {"from_attributes": True}


class ReitFundamentalsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[ReitFundamentalsPoint]

    model_config = {"from_attributes": True}


class UsStockQuoteResponse(BaseModel):
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


class UsStockTechnicalsResponse(BaseModel):
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


class UsStockDividendsAvgResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    avg_dividend_5y: float

    model_config = {"from_attributes": True}


class UsStockPriceHistoryPoint(BaseModel):
    price_date: date
    close_price: float

    model_config = {"from_attributes": True}


class UsStockPriceHistoryResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[UsStockPriceHistoryPoint]

    model_config = {"from_attributes": True}


class UsStockDividendPaymentPoint(BaseModel):
    payment_date: date
    amount: float
    price_at_payment: float | None
    yield_pct: float | None

    model_config = {"from_attributes": True}


class UsStockDividendPaymentsResponse(BaseModel):
    ticker: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[UsStockDividendPaymentPoint]

    model_config = {"from_attributes": True}
