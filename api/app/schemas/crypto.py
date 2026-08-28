from datetime import date, datetime

from pydantic import BaseModel


class CryptoIndicatorResponse(BaseModel):
    indicator_code: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    raw_value: float

    model_config = {"from_attributes": True}


class CryptoFearGreedResponse(BaseModel):
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    value: int
    classification: str
    reading_date: date

    model_config = {"from_attributes": True}


class CryptoQuoteResponse(BaseModel):
    symbol: str
    coin_id: str
    name: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    price: float

    model_config = {"from_attributes": True}


class CryptoPriceHistoryPoint(BaseModel):
    price_date: date
    price: float

    model_config = {"from_attributes": True}


class CryptoPriceHistoryResponse(BaseModel):
    symbol: str
    coin_id: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[CryptoPriceHistoryPoint]

    model_config = {"from_attributes": True}
