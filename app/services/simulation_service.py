import random
import asyncio
from datetime import datetime, timedelta
from app.repositories.citizen_repo import citizen_repo
from app.repositories.location_repo import location_repo
from app.repositories.vision_repo import vision_repo
from app.models.schemas_vision import VisionCreate
import app.core.hardware_switch as hw

class SimulationService:
    """
    El 'Dios' de la simulación.
    Orquesta el movimiento de ciudadanos y la generación de crímenes futuros.
    """
    async def run_step(self):
        """Ejecuta un 'tick' de la simulación."""
        print("Simulando actividad en la ciudad...")
        
        # Clear old visions before generating new ones to avoid accumulation
        await self._clear_old_visions()
        
        if hw.DEMO_MODE:
            # En demo mode, no tocamos la BD.
            # Podríamos modificar un estado en memoria si quisiéramos,
            # pero para la visualización basta con que no falle.
            print("DEMO MODE: Simulating activity (No DB Check)")
            return {"processed": 10, "crimes": 2, "note": "Simulation skipped in Demo Mode"}

        # 1. Obtener actores aleatorios (Muestreo)
        citizens = await citizen_repo.find_all(limit=50)
        locations = await location_repo.find_all(limit=20)
        
        if not citizens or not locations:
            print("Faltan datos para simular.")
            return

        # 2. Lógica de "Pre-Crimen" (BATCH PROCESS)
        # Generamos múltiples intentos para poblar el grafo
        results = []
        for _ in range(10):
            suspect = random.choice(citizens)
            target = random.choice(locations)
            
            # Boost artificial para DEMO: +0.2 al riesgo base
            probability = self._calculate_mock_probability(suspect, target) + 0.15
            
            # 3. Si el riesgo es alto, creamos la conexión en el Grafo
            if probability > 0.4: # Umbral más alto pero con boost
                print(f"BOLA ROJA GENERADA: {suspect['name']} en {target['name']} (Prob: {probability:.2f})")
                vision_data = VisionCreate(
                    citizen_id=suspect['id'],
                    location_id=target['id'],
                    probability=min(probability, 0.99),
                    predicted_date=datetime.now() + timedelta(hours=random.randint(1, 48)),
                    ai_model_version="Sim_v1"
                )
                await vision_repo.create_vision(vision_data)
                results.append("CRIME_DETECTED")
        return {"processed": 10, "crimes": len(results)}

    def _calculate_mock_probability(self, citizen: dict, location: dict) -> float:
        """
        Simula la lógica de la red neuronal.
        Si el ciudadano tiene alto 'risk_seed' y el lugar es peligroso, la probabilidad sube.
        """
        base_risk = citizen.get('risk_seed', 0.1)
        env_risk = location.get('env_risk', 0.1)
        
        # Ruido aleatorio
        noise = random.uniform(-0.1, 0.2)
        
        prob = (base_risk * 0.6) + (env_risk * 0.4) + noise
        return min(max(prob, 0.0), 0.99)

    async def _clear_old_visions(self):
        """Clear all existing open visions to avoid accumulation."""
        from app.core.database import db_manager
        query = "MATCH (v:Vision) DETACH DELETE v"
        await db_manager.query(query)
        print("Cleared old visions.")

simulation_service = SimulationService()
