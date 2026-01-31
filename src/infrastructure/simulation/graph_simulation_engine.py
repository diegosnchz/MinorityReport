"""
Infrastructure: Graph Simulation Engine
Implementación del motor de simulación de actividad criminal
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

from src.domain.models.citizen import Citizen, CitizenId
from src.domain.models.location import Location, LocationId
from src.domain.models.vision import Vision, VisionId, VisionStatus
from src.domain.repositories.citizen_repository import CitizenRepository
from src.domain.repositories.location_repository import LocationRepository
from src.domain.repositories.vision_repository import VisionRepository
from src.domain.services.ai_engine import AIPredictionEngine
from src.domain.services.simulation_engine import SimulationEngine

logger = logging.getLogger("GraphSimulationEngine")


class GraphSimulationEngine(SimulationEngine):
    """
    Adaptador de Infraestructura: Motor de simulación basado en grafos.
    
    Simula movimiento de ciudadanos y generación de crímenes futuros
    usando el grafo de conocimiento.
    """
    
    def __init__(self, 
                 citizen_repo: CitizenRepository,
                 location_repo: LocationRepository,
                 vision_repo: VisionRepository,
                 ai_engine: AIPredictionEngine):
        self._citizen_repo = citizen_repo
        self._location_repo = location_repo
        self._vision_repo = vision_repo
        self._ai_engine = ai_engine
        self._total_steps = 0
        self._total_visions = 0
        self._running = False
    
    async def run_step(self) -> Dict:
        """Ejecuta un paso de simulación."""
        self._running = True
        self._total_steps += 1
        
        logger.info(f"Simulation step {self._total_steps}: Running...")
        
        # 1. Obtener actores y ubicaciones
        citizens = await self._citizen_repo.find_all(limit=50)
        locations = await self._location_repo.find_all(limit=20)
        
        if not citizens or not locations:
            logger.warning("Insufficient data for simulation")
            return {"processed": 0, "crimes_detected": 0, "visions_created": 0}
        
        # 2. Generar predicciones
        visions_created = 0
        crimes_detected = 0
        
        for _ in range(min(10, len(citizens))):
            suspect = random.choice(citizens)
            target = random.choice(locations)
            
            # Calcular probabilidad
            if self._ai_engine.is_ready():
                prediction = await self._ai_engine.predict_single(suspect, target)
                probability = prediction.probability
            else:
                # Heurística simple
                probability = self._calculate_mock_probability(suspect, target)
            
            # Boost para demo
            probability = min(probability + 0.15, 0.99)
            
            # Crear visión si el riesgo es alto
            if probability > 0.4:
                crimes_detected += 1
                vision = Vision(
                    id=VisionId(str(uuid.uuid4())),
                    citizen_id=suspect.id,
                    location_id=target.id,
                    probability=probability,
                    predicted_date=datetime.now() + timedelta(hours=random.randint(1, 48)),
                    status=VisionStatus.PENDING,
                    ai_model_version="Sim_v2",
                    created_at=datetime.now()
                )
                await self._vision_repo.save(vision)
                visions_created += 1
                logger.info(f"Vision created: {suspect.name} at {target.name} (prob: {probability:.2f})")
        
        self._total_visions += visions_created
        
        return {
            "processed": 10,
            "crimes_detected": crimes_detected,
            "visions_created": visions_created
        }
    
    async def run_batch(self, steps: int) -> Dict:
        """Ejecuta múltiples pasos."""
        total_visions = 0
        for _ in range(steps):
            result = await self.run_step()
            total_visions += result.get("visions_created", 0)
        
        return {
            "steps": steps,
            "total_visions_created": total_visions
        }
    
    async def reset(self) -> None:
        """Reinicia la simulación."""
        self._total_steps = 0
        self._total_visions = 0
        self._running = False
        logger.info("Simulation reset")
    
    def is_running(self) -> bool:
        """Verifica si la simulación está activa."""
        return self._running
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de la simulación."""
        return {
            "total_steps": self._total_steps,
            "total_visions": self._total_visions,
            "running": self._running
        }
    
    def _calculate_mock_probability(self, citizen: Citizen, location: Location) -> float:
        """Calcula probabilidad mock."""
        base_risk = citizen.risk_seed
        env_risk = location.get_risk_score()
        noise = random.uniform(-0.1, 0.2)
        
        prob = (base_risk * 0.6) + (env_risk * 0.4) + noise
        return min(max(prob, 0.0), 0.99)
