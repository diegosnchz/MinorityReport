import asyncio
from database import db
from models import RutaEscape

class AIOracle:
    async def calcular_ruta_escape(self, ladron_id: str, ubicacion_actual_id: str) -> RutaEscape:
        """
        Wrapper async que NO bloquea el event loop:
        ejecuta la lógica Neo4j síncrona en un thread.
        """
        try:
            return await asyncio.to_thread(self._calcular_ruta_escape_sync, ladron_id, ubicacion_actual_id)
        except Exception as e:
            print(f"❌ Error IA (async wrapper): {e}")
            return self._ruta_fallback("Fallo en cálculo (wrapper)")

    def _calcular_ruta_escape_sync(self, ladron_id: str, ubicacion_actual_id: str) -> RutaEscape:
        """
        Lógica síncrona (Neo4j driver normal).
        """
        query_destino = """
        MATCH (u:Ubicacion)
        WHERE u.riesgo_actual < 0.3 AND u.id <> $origen
        RETURN u.id as id
        LIMIT 1
        """

        # ⚠️ OJO: esta query depende de que APOC esté instalado y compatible.
        # Si falla, hacemos fallback.
        query_ruta = """
        MATCH (inicio:Ubicacion {id: $origen})
        MATCH (fin:Ubicacion {id: $destino})

        CALL apoc.algo.dijkstra(
            inicio,
            fin,
            'CONECTA_CON',
            'distancia'
        ) YIELD path, weight

        RETURN [n in nodes(path) | n.id] as pasos, weight as coste_total
        """

        try:
            with db.driver.session() as session:
                # 1) destino seguro
                result_dest = session.run(query_destino, origen=ubicacion_actual_id).single()
                if not result_dest:
                    return self._ruta_fallback("No hay refugios seguros")

                destino_id = result_dest["id"]

                # 2) ruta
                result_ruta = session.run(
                    query_ruta,
                    origen=ubicacion_actual_id,
                    destino=destino_id
                ).single()

                if result_ruta:
                    coste = float(result_ruta["coste_total"]) if result_ruta["coste_total"] is not None else 9999.0
                    prob = max(0.1, 1.0 - (coste / 1000.0))

                    return RutaEscape(
                        destino_seguro=destino_id,
                        camino_nodos=result_ruta["pasos"],
                        probabilidad_exito=prob
                    )

        except Exception as e:
            print(f"❌ Error IA (sync neo4j/apoc): {e}")

        return self._ruta_fallback("Fallo en cálculo")

    def _ruta_fallback(self, motivo: str) -> RutaEscape:
        return RutaEscape(
            destino_seguro="REFUGIO_EMERGENCIA",
            camino_nodos=["Ruta", "Desconocida", "Correr"],
            probabilidad_exito=0.0
        )

ai_oracle = AIOracle()