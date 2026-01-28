from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import db_manager
from app.core.ai_engine import precog_system
from app.routers import (
    predictions, 
    citizens, 
    locations, 
    crimes, 
    visions, 
    simulation, 
    analytics, 
    map_router, 
    evasion_router
)
import numpy as np
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Conectar DB y Cargar Red Neuronal
    print("Iniciando Sistema Pre-Crime...")
    precog_system.load_models()
    await db_manager.connect()
    yield
    # Shutdown
    print("Apagando sistema...")
    await db_manager.close()

app = FastAPI(title="Pre-Crime Department API", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

def _parse_origins(value: str) -> list[str]:
    if not value:
        return ["http://localhost:8000", "http://localhost:5000"]
    return [o.strip() for o in value.split(",") if o.strip()]

allowed_origins = _parse_origins(os.getenv("ALLOWED_ORIGINS", ""))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include Routers
app.include_router(predictions.router)
app.include_router(citizens.router)
app.include_router(locations.router)
app.include_router(crimes.router)
app.include_router(visions.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(map_router.router)
app.include_router(evasion_router.router)

# Mount Panel Apps (Evasion Protocol)
import panel as pn
from app.evasion.ui.dashboard import create_app
from app.evasion.ui.chatbot import create_chat

pn.serve(
    {'/evasion/dashboard': create_app, '/evasion/chat': create_chat},
    port=5000, 
    allow_websocket_origin=["localhost:8000", "localhost:5000"],
    address="0.0.0.0",
    show=False,
    threaded=True
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return HTMLResponse(content="", status_code=204)

@app.get("/analytics-dashboard", response_class=HTMLResponse)
async def analytics_dashboard():
    with open("app/static/analytics.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/map-view", response_class=HTMLResponse)
async def map_dashboard():
    with open("app/static/map.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()
