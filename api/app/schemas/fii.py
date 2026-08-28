from datetime import date, datetime

from pydantic import BaseModel


class FiiMonthlyIndicatorsResponse(BaseModel):
    cnpj: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    reference_date: date
    patrimonio_liquido: float
    valor_patrimonial_cota: float
    numero_cotistas: int | None
    dividend_yield_mes: float | None
    rentabilidade_efetiva_mes: float | None

    model_config = {"from_attributes": True}


class FiiPropertyPoint(BaseModel):
    nome_imovel: str
    reference_date: date
    endereco: str | None
    area_m2: float | None
    percentual_vacancia: float | None
    percentual_inadimplencia: float | None
    percentual_receitas_fii: float | None
    percentual_locado: float | None

    model_config = {"from_attributes": True}


class FiiPropertiesResponse(BaseModel):
    cnpj: str
    source: str
    cached: bool
    stale: bool
    fetched_at: datetime | None
    data: list[FiiPropertyPoint]

    model_config = {"from_attributes": True}
