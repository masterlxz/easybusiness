from datetime import date, datetime

from pydantic import BaseModel


class MetalQuoteResponse(BaseModel):
    metal_code: str
    name: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    price: float

    model_config = {"from_attributes": True}


class MetalPriceHistoryPoint(BaseModel):
    price_date: date
    close_price: float

    model_config = {"from_attributes": True}


class MetalPriceHistoryResponse(BaseModel):
    metal_code: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[MetalPriceHistoryPoint]

    model_config = {"from_attributes": True}
