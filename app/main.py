from fastapi import FastAPI

from app.api import boroughs, chat
from app.api import boroughs, chat, geo_chat

app = FastAPI(title="GeoRAG Assistant API")

app.include_router(boroughs.router)
app.include_router(chat.router)
app.include_router(boroughs.router)
app.include_router(chat.router)
app.include_router(geo_chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "GeoRAG Assistant"}
