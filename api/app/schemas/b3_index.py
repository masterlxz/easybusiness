from datetime import date, datetime

from pydantic import BaseModel


class B3IndexHistoryPoint(BaseModel):
    price_date: date
    close_price: float

    model_config = {"from_attributes": True}


class B3IndexHistoryResponse(BaseModel):
    index_code: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[B3IndexHistoryPoint]

    model_config = {"from_attributes": True}
