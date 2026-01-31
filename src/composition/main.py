"""
Main Entry Point - Arquitectura Hexagonal
Punto de entrada principal que inicializa el contenedor y arranca la aplicación
"""

import uvicorn
import os
from src.infrastructure.web.fastapi_server import get_fastapi_app
from src.composition.container import get_container


def main():
    """Punto de entrada principal."""
    print("=" * 60)
    print("THE EVASION PROTOCOL - Arquitectura Hexagonal v2.0")
    print("=" * 60)
    print("\nInicializando contenedor de dependencias...")
    
    # Obtener configuración
    container = get_container()
    settings = container.settings
    
    print(f"Modo Demo: {settings.demo_mode}")
    print(f"AI Mock: {settings.use_mock_ai}")
    print(f"API Port: {settings.api_port}")
    
    # Crear aplicación FastAPI
    app = get_fastapi_app()
    
    print("\n" + "=" * 60)
    print(f"Servidor listo en http://{settings.api_host}:{settings.api_port}")
    print("=" * 60)
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
