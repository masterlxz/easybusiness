import json
from unittest.mock import patch

import pytest
import requests

from app.sources.sec_edgar import (
    SecEdgarError,
    fetch_dcf_fundamentals,
    fetch_fundamentals,
    fetch_payout,
    fetch_reit_fundamentals,
    resolve_cik,
)

CONTACT_EMAIL = "test@example.com"


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, content=None):
        self.status_code = status_code
        self._payload = payload
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self._payload


def _duration_row(val, fy=2025, end="2025-12-31", start="2025-01-01", filed="2026-02-01"):
    return {"start": start, "end": end, "val": val, "fy": fy, "fp": "FY", "form": "10-K", "filed": filed}


def _instant_row(val, end="2025-12-31", fy=2025, filed="2026-02-01"):
    return {"end": end, "val": val, "fy": fy, "fp": "FY", "form": "10-K", "filed": filed}


def _concept_response(rows):
    return _FakeResponse(200, {"units": {"USD": rows}})


def _not_found_response():
    return _FakeResponse(404, {})


@pytest.fixture(autouse=True)
def _no_rate_limit_and_own_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.sources.sec_edgar.REQUEST_INTERVAL_SECONDS", 0)
    monkeypatch.setattr("app.sources.sec_edgar.CACHE_DIR", tmp_path)
    monkeypatch.setattr("app.sources.sec_edgar.TICKERS_CACHE_PATH", tmp_path / "company_tickers.json")


def test_resolve_cik_finds_matching_ticker():
    tickers_payload = _FakeResponse(
        200,
        content=json.dumps(
            {
                "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
                "1": {"cik_str": 19617, "ticker": "JPM", "title": "JPMorgan Chase & Co"},
            }
        ).encode(),
    )
    with patch("app.sources.sec_edgar.requests.get", return_value=tickers_payload):
        assert resolve_cik("aapl", CONTACT_EMAIL) == 320193
        assert resolve_cik("UNKNOWNTICKER", CONTACT_EMAIL) is None


def test_resolve_cik_raises_without_contact_email():
    with pytest.raises(SecEdgarError):
        resolve_cik("AAPL", "")


def test_resolve_cik_wraps_network_error():
    with patch(
        "app.sources.sec_edgar.requests.get", side_effect=requests.ConnectionError("boom")
    ):
        with pytest.raises(SecEdgarError):
            resolve_cik("AAPL", CONTACT_EMAIL)


def test_fetch_fundamentals_computes_from_tags():
    responses = {
        "EarningsPerShareDiluted": _concept_response([_duration_row(5.0)]),
        "StockholdersEquity": _concept_response([_instant_row(1000.0)]),
        "NetIncomeLoss": _concept_response([_duration_row(200.0)]),
        "CommonStockSharesOutstanding": _concept_response([_instant_row(100.0)]),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        result = fetch_fundamentals(320193, CONTACT_EMAIL)

    assert result == {"lpa": 5.0, "vpa": 10.0, "roe": 20.0, "shares_outstanding": 100.0}


def test_fetch_fundamentals_returns_none_when_equity_not_positive():
    responses = {
        "EarningsPerShareDiluted": _concept_response([_duration_row(5.0)]),
        "StockholdersEquity": _concept_response([_instant_row(-1000.0)]),
        "NetIncomeLoss": _concept_response([_duration_row(200.0)]),
        "CommonStockSharesOutstanding": _concept_response([_instant_row(100.0)]),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        assert fetch_fundamentals(320193, CONTACT_EMAIL) is None


def test_fetch_dcf_fundamentals_computes_all_fields():
    responses = {
        "OperatingIncomeLoss": _concept_response([_duration_row(500_000_000)]),
        "LongTermDebtNoncurrent": _concept_response([_instant_row(100_000_000)]),
        "LongTermDebtCurrent": _concept_response([_instant_row(50_000_000)]),
        "CashAndCashEquivalentsAtCarryingValue": _concept_response([_instant_row(80_000_000)]),
        "Revenues": _concept_response([_duration_row(900_000_000)]),
        "RevenueFromContractWithCustomerExcludingAssessedTax": _not_found_response(),
        "InventoryNet": _concept_response(
            [
                _instant_row(40_000_000, end="2025-12-31", fy=2025),
                _instant_row(35_000_000, end="2024-12-31", fy=2024),
            ]
        ),
        "AccountsReceivableNetCurrent": _concept_response(
            [
                _instant_row(60_000_000, end="2025-12-31", fy=2025),
                _instant_row(55_000_000, end="2024-12-31", fy=2024),
            ]
        ),
        "AccountsPayableCurrent": _concept_response(
            [
                _instant_row(30_000_000, end="2025-12-31", fy=2025),
                _instant_row(25_000_000, end="2024-12-31", fy=2024),
            ]
        ),
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": _concept_response(
            [_duration_row(400_000_000)]
        ),
        "IncomeTaxExpenseBenefit": _concept_response([_duration_row(100_000_000)]),
        "DepreciationDepletionAndAmortization": _not_found_response(),
        "DepreciationAmortizationAndAccretionNet": _not_found_response(),
        "DepreciationAndAmortization": _concept_response([_duration_row(20_000_000)]),
        "Depreciation": _not_found_response(),
        "PaymentsToAcquirePropertyPlantAndEquipment": _concept_response([_duration_row(30_000_000)]),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        result = fetch_dcf_fundamentals(320193, CONTACT_EMAIL)

    assert result["reference_year"] == 2025
    assert result["ebit"] == 500.0
    assert result["tax_rate"] == 25.0
    assert result["depreciation_amortization"] == 20.0
    assert result["capex"] == 30.0
    assert result["nwc_change"] == pytest.approx(5.0)
    assert result["total_debt"] == 150.0
    assert result["cash"] == 80.0
    assert result["revenue"] == 900.0
    assert result["inventory"] == 40.0


def test_fetch_dcf_fundamentals_returns_none_without_ebit():
    with patch(
        "app.sources.sec_edgar.requests.get", return_value=_not_found_response()
    ):
        assert fetch_dcf_fundamentals(999999, CONTACT_EMAIL) is None


def test_fetch_payout_averages_across_years():
    responses = {
        "NetIncomeLoss": _concept_response(
            [_duration_row(200_000_000, fy=2025), _duration_row(150_000_000, fy=2024)]
        ),
        "PaymentsOfDividendsCommonStock": _concept_response(
            [_duration_row(40_000_000, fy=2025), _duration_row(30_000_000, fy=2024)]
        ),
        "PaymentsOfDividends": _not_found_response(),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        result = fetch_payout(320193, CONTACT_EMAIL)

    assert result == {"payout_avg_5y": pytest.approx(20.0)}


def test_fetch_payout_returns_none_without_net_income():
    with patch(
        "app.sources.sec_edgar.requests.get", return_value=_not_found_response()
    ):
        assert fetch_payout(999999, CONTACT_EMAIL) is None


def test_fetch_reit_fundamentals_computes_all_fields():
    responses = {
        "Revenues": _concept_response([_duration_row(900_000_000)]),
        "RevenueFromContractWithCustomerExcludingAssessedTax": _not_found_response(),
        "StockholdersEquity": _concept_response([_instant_row(1_000_000_000)]),
        "EarningsPerShareDiluted": _concept_response([_duration_row(2.5)]),
        "RealEstateInvestmentPropertyNet": _concept_response([_instant_row(5_000_000_000)]),
        "RealEstateInvestmentPropertyAtCost": _concept_response([_instant_row(6_000_000_000)]),
        "NetIncomeLoss": _concept_response([_duration_row(200_000_000)]),
        "ProfitLoss": _not_found_response(),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        result = fetch_reit_fundamentals(1048286, CONTACT_EMAIL)

    assert result["reference_year"] == 2025
    assert result["revenue"] == 900.0
    assert result["real_estate_property_net"] == 5000.0
    assert result["real_estate_property_at_cost"] == 6000.0
    assert result["stockholders_equity"] == 1000.0
    assert result["net_income"] == 200.0
    assert result["eps_diluted"] == 2.5


def test_fetch_reit_fundamentals_falls_back_to_profit_loss():
    """Mirrors the Simon Property finding: an UPREIT can report ProfitLoss
    instead of NetIncomeLoss — net_income must still resolve."""
    responses = {
        "Revenues": _concept_response([_duration_row(900_000_000)]),
        "RevenueFromContractWithCustomerExcludingAssessedTax": _not_found_response(),
        "StockholdersEquity": _concept_response([_instant_row(1_000_000_000)]),
        "EarningsPerShareDiluted": _concept_response([_duration_row(2.5)]),
        "RealEstateInvestmentPropertyNet": _not_found_response(),
        "RealEstateInvestmentPropertyAtCost": _not_found_response(),
        "NetIncomeLoss": _not_found_response(),
        "ProfitLoss": _concept_response([_duration_row(150_000_000)]),
    }

    def fake_get(url, **kwargs):
        for tag, resp in responses.items():
            if url.endswith(f"/{tag}.json"):
                return resp
        raise AssertionError(f"unexpected URL: {url}")

    with patch("app.sources.sec_edgar.requests.get", side_effect=fake_get):
        result = fetch_reit_fundamentals(1048286, CONTACT_EMAIL)

    assert result["net_income"] == 150.0
    assert result["real_estate_property_net"] is None
    assert result["real_estate_property_at_cost"] is None


def test_fetch_reit_fundamentals_returns_none_without_revenue():
    with patch(
        "app.sources.sec_edgar.requests.get", return_value=_not_found_response()
    ):
        assert fetch_reit_fundamentals(999999, CONTACT_EMAIL) is None
