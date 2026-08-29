from datetime import date
from unittest.mock import patch

import pytest

from app.services.fii_service import (
    FundNotFoundError,
    TickerNotResolvedError,
    get_or_refresh_cnpj_resolution,
    get_or_refresh_monthly_indicators,
    get_or_refresh_properties,
)
from app.sources.acoes_bolsai import BolsaiError
from app.sources.cvm_fii import CvmFiiDataError

CNPJ_PUNCTUATED = "00.332.266/0001-31"
CNPJ_DIGITS = "00332266000131"


def _indicators():
    return {
        "reference_date": date(2026, 2, 1),
        "patrimonio_liquido": 258340696.87,
        "valor_patrimonial_cota": 92.26,
        "numero_cotistas": 3578,
        "dividend_yield_mes": 0.004338,
        "rentabilidade_efetiva_mes": 0.004874,
    }


def test_monthly_indicators_normalizes_cnpj_and_caches(db_session):
    with patch(
        "app.services.fii_service.fetch_monthly_indicators", return_value=_indicators()
    ) as mock_fetch:
        result = get_or_refresh_monthly_indicators(db_session, CNPJ_PUNCTUATED, ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cnpj"] == CNPJ_DIGITS
    assert result["cached"] is False


def test_monthly_indicators_second_call_within_ttl_uses_cache(db_session):
    with patch(
        "app.services.fii_service.fetch_monthly_indicators", return_value=_indicators()
    ) as mock_fetch:
        get_or_refresh_monthly_indicators(db_session, CNPJ_DIGITS, ttl_seconds=3600)
        result = get_or_refresh_monthly_indicators(db_session, CNPJ_DIGITS, ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_monthly_indicators_unknown_fund_without_cache_raises(db_session):
    with patch("app.services.fii_service.fetch_monthly_indicators", return_value=None):
        with pytest.raises(FundNotFoundError):
            get_or_refresh_monthly_indicators(db_session, "99999999000199", ttl_seconds=3600)


def test_monthly_indicators_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.services.fii_service.fetch_monthly_indicators", return_value=_indicators()
    ):
        get_or_refresh_monthly_indicators(db_session, CNPJ_DIGITS, ttl_seconds=0)
    with patch(
        "app.services.fii_service.fetch_monthly_indicators",
        side_effect=CvmFiiDataError("down"),
    ):
        result = get_or_refresh_monthly_indicators(db_session, CNPJ_DIGITS, ttl_seconds=0)

    assert result["stale"] is True


def _property(name="Via Parque Shopping"):
    return {
        "nome_imovel": name,
        "reference_date": date(2026, 6, 30),
        "endereco": "Av. Ayrton Senna, 3000",
        "area_m2": 56484.83,
        "percentual_vacancia": 0.169062,
        "percentual_inadimplencia": 0.014417,
        "percentual_receitas_fii": 0.967897,
        "percentual_locado": None,
    }


def test_properties_first_call_fetches_and_caches(db_session):
    with patch(
        "app.services.fii_service.fetch_property_data", return_value=[_property()]
    ) as mock_fetch:
        result = get_or_refresh_properties(db_session, CNPJ_PUNCTUATED, ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cnpj"] == CNPJ_DIGITS
    assert len(result["data"]) == 1


def test_properties_refresh_replaces_the_full_set(db_session):
    with patch(
        "app.services.fii_service.fetch_property_data", return_value=[_property("Imóvel A")]
    ):
        get_or_refresh_properties(db_session, CNPJ_DIGITS, ttl_seconds=0)

    # Next quarter: "Imóvel A" no longer reported, "Imóvel B" is new — the
    # refreshed set must reflect exactly the latest fetch, not accumulate.
    with patch(
        "app.services.fii_service.fetch_property_data", return_value=[_property("Imóvel B")]
    ):
        result = get_or_refresh_properties(db_session, CNPJ_DIGITS, ttl_seconds=0)

    names = {row.nome_imovel for row in result["data"]}
    assert names == {"Imóvel B"}


def test_properties_empty_result_is_not_an_error(db_session):
    with patch("app.services.fii_service.fetch_property_data", return_value=[]):
        result = get_or_refresh_properties(db_session, CNPJ_DIGITS, ttl_seconds=3600)

    assert result["data"] == []


def test_properties_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.services.fii_service.fetch_property_data", return_value=[_property()]
    ):
        get_or_refresh_properties(db_session, CNPJ_DIGITS, ttl_seconds=0)
    with patch(
        "app.services.fii_service.fetch_property_data",
        side_effect=CvmFiiDataError("down"),
    ):
        result = get_or_refresh_properties(db_session, CNPJ_DIGITS, ttl_seconds=0)

    assert result["stale"] is True
    assert len(result["data"]) == 1


# --- ticker -> CNPJ resolution (Fase 1.11.3) --------------------------------


def _resolution():
    return {"cnpj": CNPJ_DIGITS, "fund_name": "CSHG LOGISTICA FII"}


def test_cnpj_resolution_first_call_fetches_and_caches(db_session):
    with patch(
        "app.services.fii_service.resolve_cnpj", return_value=_resolution()
    ) as mock_resolve:
        result = get_or_refresh_cnpj_resolution(
            db_session, "hglg11", ttl_seconds=3600, bolsai_api_key="fake-key"
        )

    mock_resolve.assert_called_with("HGLG11", "fake-key")
    assert result["ticker"] == "HGLG11"
    assert result["cnpj"] == CNPJ_DIGITS
    assert result["cached"] is False


def test_cnpj_resolution_second_call_within_ttl_uses_cache(db_session):
    with patch(
        "app.services.fii_service.resolve_cnpj", return_value=_resolution()
    ) as mock_resolve:
        get_or_refresh_cnpj_resolution(
            db_session, "HGLG11", ttl_seconds=3600, bolsai_api_key="fake-key"
        )
        result = get_or_refresh_cnpj_resolution(
            db_session, "HGLG11", ttl_seconds=3600, bolsai_api_key="fake-key"
        )

    assert mock_resolve.call_count == 1
    assert result["cached"] is True


def test_cnpj_resolution_unresolved_without_cache_raises(db_session):
    with patch("app.services.fii_service.resolve_cnpj", return_value=None):
        with pytest.raises(TickerNotResolvedError):
            get_or_refresh_cnpj_resolution(
                db_session, "AMBIGUOUS1", ttl_seconds=3600, bolsai_api_key="fake-key"
            )


def test_cnpj_resolution_source_error_with_cache_serves_stale(db_session):
    with patch("app.services.fii_service.resolve_cnpj", return_value=_resolution()):
        get_or_refresh_cnpj_resolution(
            db_session, "HGLG11", ttl_seconds=0, bolsai_api_key="fake-key"
        )
    with patch(
        "app.services.fii_service.resolve_cnpj", side_effect=BolsaiError("down")
    ):
        result = get_or_refresh_cnpj_resolution(
            db_session, "HGLG11", ttl_seconds=0, bolsai_api_key="fake-key"
        )

    assert result["stale"] is True
    assert result["cnpj"] == CNPJ_DIGITS
