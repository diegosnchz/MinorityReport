import random
import asyncio
from datetime import datetime, timedelta
from app.repositories.citizen_repo import citizen_repo
from app.repositories.location_repo import location_repo
from app.repositories.vision_repo import vision_repo
from app.models.schemas_vision import VisionCreate

class SimulationService:
    """
    El 'Dios' de la simulación.
    Orquesta el movimiento de ciudadanos y la generación de crímenes futuros.
    """
    async def run_step(self):
        """Ejecuta un 'tick' de la simulación."""
        print("Simulando actividad en la ciudad...")
        
        # 1. Obtener actores aleatorios (Muestreo)
        citizens = await citizen_repo.find_all(limit=50)
        locations = await location_repo.find_all(limit=20)
        
        if not citizens or not locations:
            print("Faltan datos para simular.")
            return

        # 2. Lógica de "Pre-Crimen"
        # Seleccionamos un par aleatorio y calculamos probabilidad
        suspect = random.choice(citizens)
        target = random.choice(locations)
        
        # Simulamos la inferencia de la IA (GraphSAGE + RedGAN)
        # En producción, aquí llamaríamos a `ai_engine.predict()`
        probability = self._calculate_mock_probability(suspect, target)
        
        # 3. Si el riesgo es alto, creamos la conexión en el Grafo
        if probability > 0.75:
            print(f"BOLA ROJA GENERADA: {suspect['name']} en {target['name']}")
            vision_data = VisionCreate(
                citizen_id=suspect['id'],
                location_id=target['id'],
                probability=probability,
                predicted_date=datetime.now() + timedelta(hours=random.randint(1, 48)),
                ai_model_version="Sim_v1"
            )
            # Aquí es donde se "Conecta el Grafo":
            # (Citizen)-[:APPEARS_IN]->(Vision)-[:TARGETS]->(Location)
            await vision_repo.create_vision(vision_data)
        else:
            print(f"   ...Análisis negativo ({probability:.2f}). Ciudad segura.")

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

simulation_service = SimulationService()
