from fastapi import FastAPI

from app.routers import companies, fiis, macro_series, stocks

app = FastAPI(title="EasyBusiness Super API", version="0.1.0")
app.include_router(macro_series.router)
app.include_router(stocks.router)
app.include_router(companies.router)
app.include_router(fiis.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
