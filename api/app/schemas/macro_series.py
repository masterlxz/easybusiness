from datetime import date, datetime

from pydantic import BaseModel


class MacroSeriesPoint(BaseModel):
    reference_month: date
    value_pct: float

    model_config = {"from_attributes": True}


class MacroSeriesResponse(BaseModel):
    series_code: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[MacroSeriesPoint]

    model_config = {"from_attributes": True}
