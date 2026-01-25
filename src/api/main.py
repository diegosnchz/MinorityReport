from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
import logging

# Import Project Modules
from src.ai.graph_loader import load_graph_from_neo4j
from models import Generator, Discriminator
from src.database.neo4j_client import db

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="The Evasion Protocol API", version="1.0")

# CORS (Allow Frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/graph")
def get_graph_topology():
    """Returns the current raw graph from Neo4j for visualization."""
    try:
        # We start fresh to get pure Neo4j data
        data = load_graph_from_neo4j()
        
        # Convert to serializable format (Node Link Data)
        nodes = []
        for i in range(data.num_nodes):
            uid = data.node_map[i]
            features = data.x[i].tolist()
            nodes.append({
                "id": uid,
                "label": f"Node-{i}",
                "x": features[0],
                "y": features[1],
                "is_hideout": bool(features[2])
            })
            
        edges = []
        rows, cols = data.edge_index
        risks = data.edge_attr[:, 0].tolist() # Risk is index 0
        
        for i in range(len(rows)):
            source_idx = int(rows[i])
            target_idx = int(cols[i])
            edges.append({
                "from": data.node_map[source_idx],
                "to": data.node_map[target_idx],
                "risk": risks[i]
            })
            
        return {"nodes": nodes, "edges": edges}
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
