# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from models import Alerta
from executor import executor
from sockets import manager  # Importamos el manager desde sockets.py
import asyncio

app = FastAPI(title="The Evasion Protocol - Hive Core")

@app.on_event("startup")
async def startup_event():
    """Arranca el worker cuando enciendes el servidor"""
    asyncio.create_task(executor.run_worker())

@app.on_event("shutdown")
async def shutdown_event():
    """🛑 APAGADO CONTROLADO: Se ejecuta al pulsar Ctrl+C"""
    print("\n🚨 Apagando sistema... Esperando a que el Executor termine...")
    await executor.stop_worker()
    print("✅ Sistema apagado correctamente. ¡Hasta luego, Operador!")

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