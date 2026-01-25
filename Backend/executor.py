import asyncio
import logging
from models import Alerta
from database import db
from ai_interface import ai_oracle
from sockets import manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class CrisisExecutor:
    """
    Execution Core del sistema.
    Cola FIFO + Persistencia + IA + Notificaciones.
    """

    def __init__(self):
        self.queue: asyncio.Queue[Alerta] = asyncio.Queue()
        self.is_running: bool = False
        self.last_computed_route = None

    async def add_alert(self, alerta: Alerta) -> None:
        """Productor: rápido y no bloqueante."""
        if not self.is_running:
            logging.warning("⚠️ El sistema se está apagando, alerta rechazada.")
            return

        logging.info(
            f"📥 ALERTA RECIBIDA | ladron={alerta.ladron_id} "
            f"ubicacion={alerta.ubicacion_actual_id} riesgo={alerta.nivel_riesgo}"
        )
        await self.queue.put(alerta)

    async def run_worker(self) -> None:
        """Consumidor: Worker en background."""
        self.is_running = True
        logging.info("⚙️ EXECUTOR INICIADO | Esperando eventos...")

        while self.is_running or not self.queue.empty():
            try:
                alerta: Alerta = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logging.warning("🛑 Worker cancelado.")
                break

            try:
                await self._process_alert(alerta)
            except Exception as e:
                logging.error(f"❌ ERROR PROCESANDO ALERTA: {e}")
            finally:
                self.queue.task_done()

        logging.info("✅ EXECUTOR DETENIDO: No quedan tareas pendientes.")

    async def stop_worker(self) -> None:
        """
        🛑 Graceful Shutdown:
        - deja de aceptar nuevas alertas
        - espera a terminar cola
        """
        logging.warning("🛑 SEÑAL DE APAGADO RECIBIDA. Deteniendo Executor...")
        self.is_running = False

        if not self.queue.empty():
            count = self.queue.qsize()
            logging.info(f"⏳ Esperando a que terminen {count} tareas pendientes...")
            await self.queue.join()

        logging.info("👋 Cola vacía. Executor listo para dormir.")

    async def _process_alert(self, alerta: Alerta) -> None:
        """Pipeline de procesamiento."""
        logging.info(f"🔥 PROCESANDO | sector={alerta.ubicacion_actual_id}")

        # 1️⃣ Persistencia Neo4j (si tu driver es síncrono -> offload)
        await asyncio.to_thread(
            db.actualizar_riesgo_nodo,
            alerta.ubicacion_actual_id,
            alerta.nivel_riesgo
        )

        # 2️⃣ IA (Oráculo) - internamente ya offloadea la parte Neo4j
        ruta = await ai_oracle.calcular_ruta_escape(
            alerta.ladron_id,
            alerta.ubicacion_actual_id
        )
        self.last_computed_route = ruta

        logging.info(f"🧭 RUTA CALCULADA | destino={ruta.destino_seguro}")

        # 3️⃣ WebSocket (Push Notification)
        logging.info(f"⚡ WEBSOCKET | Notificando a {alerta.ladron_id}...")
        await manager.send_personal_message(
            {
                "tipo": "RUTA_OPTIMA",
                "destino": ruta.destino_seguro,
                "nodos": ruta.camino_nodos,
                "probabilidad": ruta.probabilidad_exito
            },
            alerta.ladron_id
        )

        # 4️⃣ Gossip (stub)
        self._broadcast_danger(alerta, ruta)

    def _broadcast_danger(self, alerta: Alerta, ruta) -> None:
        logging.info(f"📡 GOSSIP | ¡Evitar {alerta.ubicacion_actual_id}!")

# Instancia global
executor = CrisisExecutor()