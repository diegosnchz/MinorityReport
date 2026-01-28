from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
import logging
import os

# Import Project Modules
from src.ai.graph_loader import load_graph_from_neo4j
from models import Generator, Discriminator
from src.database.neo4j_client import db

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="The Evasion Protocol API", version="1.0")

# CORS (Allow Frontend to connect)
def _parse_origins(value: str) -> list[str]:
    if not value:
        return ["http://localhost:8000", "http://localhost:3000"]
    return [o.strip() for o in value.split(",") if o.strip()]

allowed_origins = _parse_origins(os.getenv("ALLOWED_ORIGINS", ""))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Global Model Store (In a real app, use a lifespan manager)
ai_models = {}

class PredictionRequest(BaseModel):
    num_samples: int = 1

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup."""
    logger.info("Starting Evasion Protocol API...")
    # Initialize simplified models matching our feature dimensions
    # Input Dim = 3 (X, Y, IsHideout)
    ai_models['generator'] = Generator(in_channels=3, out_channels=3)
    ai_models['discriminator'] = Discriminator(in_channels=3)
    
    # In a real scenario, we would load state_dict here
    logger.info("AI Models Initialized.")

@app.get("/health")
def health_check():
    return {"status": "online", "system": "The Hive"}

def _serialize_nodes(data) -> list[dict]:
    return [
        {
            "id": data.node_map[i],
            "label": f"Node-{i}",
            "x": float(data.x[i][0]),
            "y": float(data.x[i][1]),
            "is_hideout": bool(data.x[i][2])
        }
        for i in range(data.num_nodes)
    ]

def _serialize_edges(data) -> list[dict]:
    rows, cols = data.edge_index
    risks = data.edge_attr[:, 0].tolist()  # Risk is index 0
    return [
        {
            "from": data.node_map[int(rows[i])],
            "to": data.node_map[int(cols[i])],
            "risk": risks[i]
        }
        for i in range(len(rows))
    ]

@app.get("/graph")
def get_graph_topology():
    """Returns the current raw graph from Neo4j for visualization."""
    try:
        data = load_graph_from_neo4j()
        return {"nodes": _serialize_nodes(data), "edges": _serialize_edges(data)}
    except Exception as e:
        logger.error(f"Error fetching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_safe_zones(request: PredictionRequest):
    """
    Runs the Generator to find 'Safe Paths' or 'Anomalies'.
    In proper GAN logic: Generator tries to create paths that look 'Safe'.
    """
    try:
        data = load_graph_from_neo4j()
        
        # Run Inference
        # We pass the real graph to the model
        model = ai_models['generator']
        model.eval()
        
        with torch.no_grad():
            # For this demo, we pass existing node features to transform them
            # into "Safe Embeddings"
            embeddings = model(data.x, data.edge_index)
            
            # Simple Heuristic: If embedding value > threshold, it's a recommended node
            # This is a simplification of complex GAT logic
            scores = embeddings.mean(dim=1).tolist()
            
        recommendations = []
        for i, score in enumerate(scores):
            recommendations.append({
                "node_id": data.node_map[i],
                "safety_score": score
            })
            
        # Sort by safety (highest first)
        recommendations.sort(key=lambda x: x['safety_score'], reverse=True)
        
        return {"recommendations": recommendations[:5]}
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
