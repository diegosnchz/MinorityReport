# ai_interface.py
from database import db  # Reutilizamos la conexión que ya creaste
import random

class AIOracle:
    async def calcular_ruta_escape(self, ladron_id: str, ubicacion_actual_id: str):
        """
        Consulta a Neo4j para encontrar la ruta de escape óptima.
        Prioriza: Zonas con MENOS riesgo y MENOR distancia.
        """
        
        # 1. Definir un destino seguro (En una app real, esto sería dinámico)
        # Por ahora, buscamos cualquier nodo que sea 'Escondite' o 'Salida'
        query_destino = """
        MATCH (u:Ubicacion) 
        WHERE u.riesgo_actual < 0.3 AND u.id <> $origen
        RETURN u.id as id LIMIT 1
        """
        
        # 2. Query Maestra: Algoritmo Dijkstra ponderado
        # Usamos APOC para buscar el camino más eficiente.
        # Truco: Si el riesgo sube, el "coste" de pasar por ahí sube.
        query_ruta = """
        MATCH (inicio:Ubicacion {id: $origen})
        MATCH (fin:Ubicacion {id: $destino})
        
        CALL apoc.algo.dijkstra(
            inicio, 
            fin, 
            'CONECTA_CON', 
            'distancia', 
            1.0,   // Peso por defecto
            1      // Número de caminos a buscar
        ) YIELD path, weight
        
        RETURN [n in nodes(path) | n.id] as pasos, weight as coste_total
        """

        try:
            # A. Buscamos un destino seguro
            with db.driver.session() as session:
                result_dest = session.run(query_destino, origen=ubicacion_actual_id).single()
                if not result_dest:
                    return self._ruta_fallback("No hay refugios seguros")
                
                destino_id = result_dest["id"]

                # B. Calculamos la ruta hasta allí
                result_ruta = session.run(query_ruta, origen=ubicacion_actual_id, destino=destino_id).single()
                
                if result_ruta:
                    return RutaEscape(
                        destino_seguro=destino_id,
                        camino_nodos=result_ruta["pasos"],
                        probabilidad_exito=max(0.1, 1.0 - (result_ruta["coste_total"] / 1000)) # Simulación de %
                    )
                
        except Exception as e:
            print(f"❌ Error IA: {e}")
        
        return self._ruta_fallback("Fallo en cálculo")

    def _ruta_fallback(self, motivo):
        # Un plan B por si la base de datos falla
        return RutaEscape(
            destino_seguro="REFUGIO_EMERGENCIA",
            camino_nodos=["Ruta", "Desconocida", "Correr"],
            probabilidad_exito=0.0
        )

# Clase simple para devolver datos limpios
class RutaEscape:
    def __init__(self, destino_seguro, camino_nodos, probabilidad_exito):
        self.destino_seguro = destino_seguro
        self.camino_nodos = camino_nodos
        self.probabilidad_exito = probabilidad_exito

ai_oracle = AIOracle()