from fastapi import FastAPI

from app.api import boroughs

app = FastAPI(title="GeoRAG Assistant API")

app.include_router(boroughs.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "GeoRAG Assistant"}
