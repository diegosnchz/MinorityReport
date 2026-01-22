from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import db_manager
from app.core.ai_engine import precog_system
from app.routers import predictions, citizens, locations, crimes, visions, simulation, analytics, map_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Proxy/Redirect for ease of access (Optional, usually we run Panel separately or use middleware)
# For simplicity in this demo, accessing port 5000 directly is easier, 
# but let's document it for the user.

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
