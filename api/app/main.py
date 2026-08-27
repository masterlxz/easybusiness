from fastapi import FastAPI

from app.routers import macro_series

app = FastAPI(title="EasyBusiness Super API", version="0.1.0")
app.include_router(macro_series.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
