# executor.py
import asyncio
import logging
from models import Alerta
from database import db
from ai_interface import ai_oracle

# Configuración básica de logging (profesional, no prints)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class CrisisExecutor:
    """
    Execution Core del sistema.

    Responsabilidades:
    - Desacoplar la recepción de alertas del procesamiento pesado
    - Garantizar orden FIFO
    - Orquestar:
        * Persistencia (Neo4j)
        * IA (Oráculo)
        * Difusión de eventos (Gossip)
    """

    def __init__(self):
        self.queue: asyncio.Queue[Alerta] = asyncio.Queue()
        self.is_running: bool = False

        # Estado interno (expuesto luego por la API)
        self.last_computed_route = None

    async def add_alert(self, alerta: Alerta) -> None:
        """
        Productor:
        Método rápido, no bloqueante.
        La API delega aquí y responde inmediatamente.
        """
        logging.info(
            f"📥 ALERTA RECIBIDA | ladrón={alerta.ladron_id} "
            f"ubicación={alerta.ubicacion_actual_id}"
        )
        await self.queue.put(alerta)

    async def run_worker(self) -> None:
        """
        Consumidor:
        Worker en background que procesa alertas una a una.
        """
        self.is_running = True
        logging.info("⚙️ EXECUTOR INICIADO | Esperando eventos...")

        while self.is_running:
            alerta: Alerta = await self.queue.get()

            try:
                await self._process_alert(alerta)
            except Exception as e:
                logging.error(f"❌ ERROR PROCESANDO ALERTA: {e}")
            finally:
                self.queue.task_done()

    async def _process_alert(self, alerta: Alerta) -> None:
        """
        Pipeline de procesamiento de una alerta.
        """

        logging.info(
            f"🔥 PROCESANDO AMENAZA | sector={alerta.ubicacion_actual_id} "
            f"riesgo={alerta.nivel_riesgo}"
        )

        # 1️⃣ Persistencia: actualizar el grafo
        db.actualizar_riesgo_nodo(
            alerta.ubicacion_actual_id,
            alerta.nivel_riesgo
        )

        # 2️⃣ IA: calcular ruta de evasión
        ruta = await ai_oracle.calcular_ruta_escape(
            alerta.ladron_id,
            alerta.ubicacion_actual_id
        )

        self.last_computed_route = ruta

        logging.info(
            f"🧭 RUTA CALCULADA | destino={ruta.destino_seguro} "
            f"éxito={ruta.probabilidad_exito}"
        )

        # 3️⃣ Gossip / Broadcast
        self._broadcast_danger(alerta, ruta)

    def _broadcast_danger(self, alerta: Alerta, ruta) -> None:
        """
        Simulación del protocolo Gossip.
        """
        logging.info(
            f"📡 GOSSIP | Evitar {alerta.ubicacion_actual_id} | "
            f"Ruta alternativa: {ruta.destino_seguro}"
        )


# Instancia global del Executor
executor = CrisisExecutor()
