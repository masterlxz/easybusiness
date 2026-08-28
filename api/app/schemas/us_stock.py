from datetime import datetime

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
