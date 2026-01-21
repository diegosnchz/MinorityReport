from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import db_manager
from app.core.ai_engine import precog_system
from app.routers import predictions, citizens, locations, crimes, visions, simulation
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

# Include Routers
app.include_router(predictions.router)
app.include_router(citizens.router)
app.include_router(locations.router)
app.include_router(crimes.router)
app.include_router(visions.router)
app.include_router(simulation.router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return HTMLResponse(content="", status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()
