# app/routers/predictions.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.database import db_manager
from app.core.ai_engine import precog_system # Asumimos que esto carga el modelo .pt
from app.models.schemas_citizen import PredictionOutput, CitizenFeatureVector

router = APIRouter(
    prefix="/precogs",
    tags=["Predictions"]
)

@router.get("/scan/{citizen_id}", response_model=PredictionOutput)
async def scan_citizen(citizen_id: int):
    """
    ENDPOINT PRINCIPAL:
    Analiza el riesgo de un ciudadano basándose en su grafo social y comportamiento
    reciente.
    """
    # 1. FETCH: Obtener el contexto del ciudadano desde Neo4j
    # Buscamos al ciudadano, contamos amigos criminales y obtenemos su 'risk_seed'
    cypher_query = """
    MATCH (c:Citizen {id: $cid})
    OPTIONAL MATCH (c)-[:KNOWS]-(friend)
    OPTIONAL MATCH (friend)-[r:COMMITTED_CRIME]->()
    WITH c, count(r) as criminal_contacts
    // Devolvemos las features que el modelo GNN necesita
    RETURN c.id as id,
           c.name as name,
           c.risk_seed as risk_seed,
           c.job as job,
           criminal_contacts as criminal_degree
    """
    
    results = await db_manager.query(cypher_query, {"cid": citizen_id})
    
    if not results:
        raise HTTPException(status_code=404, detail="Ciudadano no encontrado en el sistema.")
        
    raw_data = results[0]

    # 2. TRANSFORM: Preparar datos para PyTorch
    # Convertimos los datos crudos de Neo4j al formato que espera la IA
    # (En un caso real, aquí haríamos One-Hot Encoding del trabajo, normalización, etc.)
    features = CitizenFeatureVector(
        id=raw_data['id'],
        name=raw_data['name'],
        status="ACTIVE",
        criminal_degree=raw_data['criminal_degree'],
        risk_seed=raw_data['risk_seed'],
        job_vector=[0.0, 1.0, 0.0] # Mock del vector
    )

    # 3. INFERENCE: Preguntar al Modelo (Precog System)
    # Esta función (definida en ai_engine) corre el tensor por GraphSAGE/GAT
    ai_verdict = precog_system.predict(features)

    # 4. RESPONSE: Formatear la salida
    # Si la probabilidad supera el 85%, se emite una "Bola Roja"
    verdict_label = "SAFE"
    if ai_verdict["probability"] > 0.85:
        verdict_label = "INTERVENE"
        # Opcional: Escribir la predicción de vuelta en Neo4j para visualización
        await _register_prediction_in_db(citizen_id, ai_verdict["probability"])
        
    elif ai_verdict["probability"] > 0.60:
        verdict_label = "WATCHLIST"
        
    return PredictionOutput(
        subject_id=citizen_id,
        target_location_id="UNKNOWN_FUTURE_LOC", # RedGAN predeciría esto
        probability=ai_verdict["probability"],
        verdict=verdict_label
    )

async def _register_prediction_in_db(citizen_id: int, prob: float):
    """Función auxiliar para persistir la 'Bola Roja' en el grafo."""
    query = """
    MATCH (c:Citizen {id: $cid})
    MERGE (c)-[r:FUTURE_CRIME_PREDICTED]->(c)
    SET r.probability = $prob, r.timestamp = datetime()
    """
    await db_manager.query(query, {"cid": citizen_id, "prob": prob})
