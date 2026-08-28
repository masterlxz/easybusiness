import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401 — registers model classes on Base.metadata
from app.database import Base, SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    yield


@pytest.fixture()
def db_session():
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.execute(
            text(
                "TRUNCATE TABLE macro_series_monthly, stock_quotes, stock_technicals, "
                "stock_dividends_avg, stock_price_history, stock_dividend_payments, "
                "company_roe, company_payout_avg, company_dcf_fundamentals, "
                "fii_monthly_indicators, fii_properties, "
                "crypto_indicators, crypto_fear_greed, crypto_coin_resolution, "
                "crypto_quotes, crypto_price_history"
            )
        )
        session.commit()
        session.close()
