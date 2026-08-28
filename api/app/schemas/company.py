from datetime import datetime

from pydantic import BaseModel


class CompanyRoeResponse(BaseModel):
    cvm_code: int
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    reference_year: int
    roe: float

    model_config = {"from_attributes": True}


class CompanyPayoutResponse(BaseModel):
    cvm_code: int
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    payout_avg_5y: float

    model_config = {"from_attributes": True}


class CompanyDcfFundamentalsResponse(BaseModel):
    cvm_code: int
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
