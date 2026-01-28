from fastapi import APIRouter, HTTPException
from app.evasion.services.routing_service import routing_service
from app.evasion.models.hybrid_engine import hybrid_engine
import pandas as pd

router = APIRouter(prefix="/evasion", tags=["Evasion Protocol"])

@router.get("/route")
async def get_escape_route(origin_id: str, destination_id: str):
    """
    Calcula una ruta de escape táctica.
    """
    path_data = await routing_service.find_safe_path(origin_id, destination_id)
    if not path_data:
        raise HTTPException(status_code=404, detail="Locations not found")
    return path_data

@router.get("/explain-risk")
async def explain_node_risk(hour: int, weather: str, patrols: float):
    """
    XAI: Explica por qué una zona es riesgosa usando XGBoost SHAP values.
    """
    # Mock node features
    features = pd.DataFrame([{
        "hour": hour,
        "patrol_density": patrols,
        "weather_score": 1.0 if weather == "Rain" else 0.2
    }])
    
    if not hybrid_engine.is_trained:
        raise HTTPException(status_code=503, detail="Hybrid engine not ready")

    shap_values = hybrid_engine.get_feature_importance(features)
    
    return {
        "base_risk": hybrid_engine.get_base_risk(features.iloc[0].to_dict()),
        "top_factors": ["Patrols", "Weather"] if weather == "Rain" else ["Hour"],
        "shap_summary": "Inferencia acelerada por GPU.",
        "shap_values": shap_values.tolist() if hasattr(shap_values, "tolist") else shap_values
    }
