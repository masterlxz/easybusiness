from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import requests

from app.sources.cvm_dfp import CvmDataError, fetch_dcf_fundamentals, fetch_payout, fetch_roe
from tests.cvm_fixtures import DMPL_FIELDS, DRE_FIELDS, build_zip, dmpl_row, dre_row

YEAR = datetime.now(timezone.utc).year - 1


def _fake_response(content: bytes):
    class FakeResponse:
        def __init__(self, content: bytes):
            self._content = content

        def raise_for_status(self):
            pass

        @property
        def content(self):
            return self._content

    return FakeResponse(content)


def _roe_zip():
    dre_rows = [dre_row(cd_conta="3.01", ds_conta="Lucro Líquido Consolidado do Período", vl_conta="100000")]
    bpp_rows = [dre_row(cd_conta="2.01", ds_conta="Patrimônio Líquido Consolidado", vl_conta="500000")]
    return build_zip(
        {
            f"dfp_cia_aberta_DRE_con_{YEAR}.csv": dre_rows,
            f"dfp_cia_aberta_BPP_con_{YEAR}.csv": bpp_rows,
        },
        {
            f"dfp_cia_aberta_DRE_con_{YEAR}.csv": DRE_FIELDS,
            f"dfp_cia_aberta_BPP_con_{YEAR}.csv": DRE_FIELDS,
        },
    )


def test_fetch_roe_computes_from_matched_accounts(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get", return_value=_fake_response(_roe_zip())
        ):
            result = fetch_roe(4170)

    assert result == {"reference_year": YEAR, "roe": 20.0}


def test_fetch_roe_unknown_company_returns_none(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get", return_value=_fake_response(_roe_zip())
        ):
            assert fetch_roe(999999) is None


def test_fetch_roe_wraps_network_error(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get", side_effect=requests.ConnectionError("boom")
        ):
            with pytest.raises(CvmDataError):
                fetch_roe(4170)


def _dcf_zip():
    dre_rows = [
        dre_row(cd_conta="3.01", vl_conta="100000"),  # revenue
        dre_row(cd_conta="3.05", vl_conta="50000"),  # ebit
        dre_row(cd_conta="3.07", vl_conta="40000"),  # pretax income
        dre_row(cd_conta="3.08", vl_conta="-10000"),  # tax expense
    ]
    bpa_rows = [
        dre_row(cd_conta="1.01.01", vl_conta="20000"),
        dre_row(cd_conta="1.01.02", vl_conta="5000"),
        dre_row(cd_conta="1.01.03", vl_conta="10000"),
        dre_row(cd_conta="1.01.04", vl_conta="8000"),
        dre_row(cd_conta="1.01.03", ordem="PENÚLTIMO", vl_conta="9000"),
        dre_row(cd_conta="1.01.04", ordem="PENÚLTIMO", vl_conta="7000"),
    ]
    bpp_rows = [
        dre_row(cd_conta="2.01.02", vl_conta="6000"),
        dre_row(cd_conta="2.01.02", ordem="PENÚLTIMO", vl_conta="5000"),
        dre_row(cd_conta="2.01.04", vl_conta="15000"),
        dre_row(cd_conta="2.02.01", vl_conta="25000"),
    ]
    dfc_rows = [
        dre_row(cd_conta="6.01.01.01", ds_conta="Depreciação e amortização", vl_conta="3000"),
        dre_row(cd_conta="6.02.01", ds_conta="Aquisição de imobilizado", vl_conta="-4000"),
    ]
    files = {
        f"dfp_cia_aberta_DRE_con_{YEAR}.csv": dre_rows,
        f"dfp_cia_aberta_BPA_con_{YEAR}.csv": bpa_rows,
        f"dfp_cia_aberta_BPP_con_{YEAR}.csv": bpp_rows,
        f"dfp_cia_aberta_DFC_MI_con_{YEAR}.csv": dfc_rows,
    }
    return build_zip(files, {name: DRE_FIELDS for name in files})


def test_fetch_dcf_fundamentals_computes_all_fields(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get", return_value=_fake_response(_dcf_zip())
        ):
            result = fetch_dcf_fundamentals(4170)

    assert result["reference_year"] == YEAR
    assert result["ebit"] == 50.0
    assert result["tax_rate"] == 25.0
    assert result["depreciation_amortization"] == 3.0
    assert result["capex"] == 4.0
    assert result["nwc_change"] == pytest.approx(1.0)
    assert result["total_debt"] == 40.0
    assert result["cash"] == 25.0
    assert result["revenue"] == 100.0
    assert result["inventory"] == 8.0


def test_fetch_dcf_fundamentals_unknown_company_returns_none(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get", return_value=_fake_response(_dcf_zip())
        ):
            assert fetch_dcf_fundamentals(999999) is None


def _payout_zip_for_year(year: int, net_income: str | None, distributions: str | None):
    """`net_income=None` builds a zip with the DRE/DMPL files present (real
    header row) but zero rows for this company — simulates "no usable data
    this year", not a malformed/missing file."""
    dre_rows = (
        []
        if net_income is None
        else [
            dre_row(
                cd_conta="3.01",
                ds_conta="Lucro Líquido Consolidado do Período",
                vl_conta=net_income,
                dt_refer=f"{year}-12-31",
            )
        ]
    )
    dmpl_rows = (
        []
        if distributions is None
        else [
            dmpl_row(
                cd_conta="5.04.06",
                ds_conta="Dividendos",
                vl_conta=distributions,
                dt_refer=f"{year}-12-31",
            )
        ]
    )
    return build_zip(
        {
            f"dfp_cia_aberta_DRE_con_{year}.csv": dre_rows,
            f"dfp_cia_aberta_DMPL_con_{year}.csv": dmpl_rows,
        },
        {
            f"dfp_cia_aberta_DRE_con_{year}.csv": DRE_FIELDS,
            f"dfp_cia_aberta_DMPL_con_{year}.csv": DMPL_FIELDS,
        },
    )


def test_fetch_payout_averages_across_years(tmp_path):
    def fake_get(url, **kwargs):
        year = int(url.rsplit("_", 1)[-1].removesuffix(".zip"))
        # 2 of the 5 years have usable data, matching the "some years may be
        # missing" behavior the source is designed to tolerate.
        if year in (YEAR, YEAR - 1):
            net_income = "100000"  # 100 (millions)
            distributions = "-20000" if year == YEAR else "-40000"  # abs() -> 20 / 40
            return _fake_response(_payout_zip_for_year(year, net_income, distributions))
        return _fake_response(_payout_zip_for_year(year, None, None))

    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch("app.sources.cvm_dfp.requests.get", side_effect=fake_get):
            result = fetch_payout(4170)

    # sum(distributions) / sum(net_income) = (20 + 40) / (100 + 100) * 100 = 30%
    assert result == {"payout_avg_5y": 30.0}


def test_fetch_payout_no_usable_years_returns_none(tmp_path):
    with patch("app.sources.cvm_dfp.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_dfp.requests.get",
            side_effect=lambda url, **kwargs: _fake_response(
                _payout_zip_for_year(int(url.rsplit("_", 1)[-1].removesuffix(".zip")), None, None)
            ),
        ):
            assert fetch_payout(4170) is None
