# executor.py
import asyncio
import logging
from models import Alerta
from database import db
from ai_interface import ai_oracle
from sockets import manager # Importamos el manager compartido

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class CrisisExecutor:
    """
    Execution Core del sistema.
    Gestiona la cola de alertas, persistencia, IA y notificaciones.
    """

    def __init__(self):
        self.queue: asyncio.Queue[Alerta] = asyncio.Queue()
        self.is_running: bool = False
        self.last_computed_route = None

    async def add_alert(self, alerta: Alerta) -> None:
        """Productor: Método rápido, no bloqueante."""
        if not self.is_running:
            logging.warning("⚠️ El sistema se está apagando, alerta rechazada.")
            return

        logging.info(
            f"📥 ALERTA RECIBIDA | ladrón={alerta.ladron_id} "
            f"ubicación={alerta.ubicacion_actual_id}"
        )
        await self.queue.put(alerta)

    async def run_worker(self) -> None:
        """Consumidor: Worker en background."""
        self.is_running = True
        logging.info("⚙️ EXECUTOR INICIADO | Esperando eventos...")

        while self.is_running or not self.queue.empty():
            # Si estamos apagando (is_running=False), seguimos solo si quedan cosas en la cola
            
            try:
                # Esperamos una alerta con un timeout para poder revisar is_running periódicamente
                # Si la cola está vacía y is_running es False, saldremos del loop
                alerta: Alerta = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            try:
                await self._process_alert(alerta)
            except Exception as e:
                logging.error(f"❌ ERROR PROCESANDO ALERTA: {e}")
            finally:
                # Marcamos la tarea como completada para el shutdown
                self.queue.task_done()
        
        logging.info("✅ EXECUTOR DETENIDO: No quedan tareas pendientes.")

    async def stop_worker(self):
        """
        🛑 Graceful Shutdown:
        Detiene la aceptación de nuevas tareas y espera a que terminen las actuales.
        """
        logging.warning("🛑 SEÑAL DE APAGADO RECIBIDA. Deteniendo Executor...")
        self.is_running = False
        
        if not self.queue.empty():
            count = self.queue.qsize()
            logging.info(f"⏳ Esperando a que terminen {count} tareas pendientes...")
            # Esperamos a que queue.task_done() sea llamado para cada item restante
            await self.queue.join()
        
        logging.info("👋 Cola vacía. Executor listo para dormir.")

    async def _process_alert(self, alerta: Alerta) -> None:
        """Pipeline de procesamiento."""
        
        logging.info(f"🔥 PROCESANDO | sector={alerta.ubicacion_actual_id}")

        # 1️⃣ Persistencia (Neo4j)
        # Nota: Asegúrate de tener la versión nueva de database.py con 'Onda Expansiva'
        db.actualizar_riesgo_nodo(alerta.ubicacion_actual_id, alerta.nivel_riesgo)

        # 2️⃣ IA (Oráculo)
        ruta = await ai_oracle.calcular_ruta_escape(
            alerta.ladron_id, 
            alerta.ubicacion_actual_id
        )
        self.last_computed_route = ruta

        logging.info(f"🧭 RUTA CALCULADA | destino={ruta.destino_seguro}")

        # 3️⃣ WebSocket (Push Notification)
        if manager:
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

        # 4️⃣ Gossip
        self._broadcast_danger(alerta, ruta)

    def _broadcast_danger(self, alerta: Alerta, ruta) -> None:
        logging.info(f"📡 GOSSIP | ¡Evitar {alerta.ubicacion_actual_id}!")

# Instancia global
executor = CrisisExecutor()