"""
Infrastructure Adapter: FastAPI Web Server
Adaptador que expone la API REST usando FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from src.composition.container import get_container


class FastAPIServer:
    """
    Adaptador de Infraestructura: Servidor HTTP con FastAPI.
    
    Expone los casos de uso del dominio como endpoints REST.
    Es un DRIVER ADAPTER en la arquitectura hexagonal.
    """
    
    def __init__(self):
        self.app = None
        self.container = None
    
    def create_app(self) -> FastAPI:
        """Crea y configura la aplicación FastAPI."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            print("Iniciando Sistema Pre-Crime (Hexagonal)...")
            self.container = get_container()
            await self.container.initialize()
            yield
            # Shutdown
            print("Apagando sistema...")
            await self.container.shutdown()
        
        self.app = FastAPI(
            title="Pre-Crime Department API (Hexagonal)",
            description="Arquitectura Hexagonal - Ports & Adapters",
            version="2.0.0",
            lifespan=lifespan
        )
        
        # Configurar CORS
        self._configure_cors()
        
        # Registrar routers
        self._register_routers()
        
        # Static files
        self._configure_static_files()
        
        return self.app
    
    def _configure_cors(self):
        """Configura CORS."""
        def _parse_origins(value: str) -> list:
            if not value:
                return ["http://localhost:8000", "http://localhost:5000"]
            return [o.strip() for o in value.split(",") if o.strip()]
        
        allowed_origins = _parse_origins(os.getenv("ALLOWED_ORIGINS", ""))
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
    
    def _register_routers(self):
        """Registra todos los routers."""
        from src.infrastructure.web.routers.citizens import router as citizens_router
        from src.infrastructure.web.routers.predictions import router as predictions_router
        from src.infrastructure.web.routers.evasion import router as evasion_router
        from src.infrastructure.web.routers.simulation import router as simulation_router
        
        self.app.include_router(citizens_router, prefix="/api/v2")
        self.app.include_router(predictions_router, prefix="/api/v2")
        self.app.include_router(evasion_router, prefix="/api/v2")
        self.app.include_router(simulation_router, prefix="/api/v2")
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "architecture": "hexagonal"}
    
    def _configure_static_files(self):
        """Configura archivos estáticos."""
        try:
            self.app.mount("/static", StaticFiles(directory="app/static"), name="static")
            
            @self.app.get("/", response_class=HTMLResponse)
            async def root():
                with open("app/static/index.html", "r", encoding="utf-8") as f:
                    return f.read()
            
            @self.app.get("/favicon.ico", include_in_schema=False)
            async def favicon():
                return HTMLResponse(content="", status_code=204)
                
        except Exception as e:
            print(f"Static files not available: {e}")


# Instancia singleton
_fastapi_server = FastAPIServer()


def get_fastapi_app() -> FastAPI:
    """Factory para obtener la app FastAPI configurada."""
    return _fastapi_server.create_app()
