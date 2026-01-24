# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from models import Alerta
from executor import executor
from sockets import manager
import asyncio

# --- DEFINICIÓN DEL CICLO DE VIDA (LIFESPAN) ---
# Esto sustituye a los antiguos 'startup' y 'shutdown'
@asynccontextmanager
async def lifespan(app: FastAPI):
    #  🟢 ZONA DE ARRANQUE
    print("🚀 THE HIVE: Iniciando sistemas y Executor...")
    asyncio.create_task(executor.run_worker())
    
    yield  # <--- El servidor funciona aquí
    
    #  🔴 ZONA DE APAGADO
    print("\n🛑 THE HIVE: Deteniendo sistemas...")
    await executor.stop_worker()
    print("✅ THE HIVE: Apagado completado.")

# --- INICIALIZAMOS LA APP CON LIFESPAN ---
app = FastAPI(
    title="The Evasion Protocol - Hive Core",
    lifespan=lifespan
)

# ❌ AQUÍ HE BORRADO LOS BLOQUES @app.on_event("startup") y ("shutdown") 
# PORQUE YA ESTÁN DENTRO DE LIFESPAN. ¡NO LOS NECESITAS!

@app.get("/")
def read_root():
    return {"status": "The Hive is Online", "system": "Nominal"}

@app.post("/alert")
async def report_danger(alerta: Alerta):
    """Endpoint para recibir alertas de los ladrones"""
    await executor.add_alert(alerta)
    return {"status": "received", "message": "Procesando evasión..."}

@app.get("/status")
def get_queue_status():
    return {
        "estado_worker": "Activo" if executor.is_running else "Apagándose",
        "tareas_pendientes": executor.queue.qsize()
    }

# Endpoint WebSocket
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(client_id)