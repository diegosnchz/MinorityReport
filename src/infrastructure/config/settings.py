"""
Infrastructure Configuration: Settings
Configuración de la aplicación usando variables de entorno
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


@dataclass
class Settings:
    """
    Configuración de la aplicación.
    
    Centraliza todas las configuraciones y variables de entorno.
    """
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "secret_password_123"
    
    # Application Mode
    demo_mode: bool = True
    use_mock_ai: bool = True
    
    # Server Configuration
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    panel_port: int = 5000
    
    # CORS
    allowed_origins: list = None
    
    # AI Configuration
    model_path: str = "models/"
    use_gpu: bool = True
    
    def __post_init__(self):
        # Override with environment variables
        self.neo4j_uri = os.getenv("NEO4J_URI", self.neo4j_uri)
        self.neo4j_user = os.getenv("NEO4J_USER", self.neo4j_user)
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", self.neo4j_password)
        
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        self.use_mock_ai = os.getenv("USE_MOCK_AI", "true").lower() == "true"
        
        self.api_port = int(os.getenv("API_PORT", self.api_port))
        self.panel_port = int(os.getenv("PANEL_PORT", self.panel_port))
        
        origins = os.getenv("ALLOWED_ORIGINS", "")
        if origins:
            self.allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]
        else:
            self.allowed_origins = ["http://localhost:8000", "http://localhost:5000"]
        
        self.use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
