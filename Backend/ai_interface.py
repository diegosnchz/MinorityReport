# ai_interface.py
import asyncio
from models import RutaEscape


class AIOracle:
    """
    Wrapper del sistema de Inteligencia Artificial.
    
    Principios de diseño:
    - Encapsula completamente el modelo (GAT / LLM / ML).
    - Permite cambiar la IA sin modificar el Executor.
    - Simula una inferencia costosa (I/O o CPU-bound).
    """

    async def calcular_ruta_escape(
        self,
        ladron_id: str,
        ubicacion_actual_id: str
    ) -> RutaEscape:
        """
        Calcula la mejor ruta de evasión para un ladrón dado
        el estado actual del grafo.

        En producción:
        - Aquí se cargaría el subgrafo desde Neo4j
        - Se ejecutaría el modelo GAT
        - Se devolvería la predicción real
        """

        # Simulación de inferencia pesada
        await asyncio.sleep(1.5)

        # Resultado simulado (determinista para pruebas)
        return RutaEscape(
            destino_seguro="Tunel Norte",
            camino_nodos=[
                ubicacion_actual_id,
                "Alcantarilla 3",
                "Tunel Norte"
            ],
            probabilidad_exito=0.82
        )


# Instancia singleton del oráculo
ai_oracle = AIOracle()
