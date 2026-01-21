# main.py
from fastapi import FastAPI, BackgroundTasks
from models import Alerta, RutaEscape
from executor import executor
import asyncio

app = FastAPI(title="The Evasion Protocol - Hive Core")

@app.on_event("startup")
async def startup_event():
    # Arrancamos el Executor en el background al iniciar la API
    asyncio.create_task(executor.run_worker())

@app.get("/")
def read_root():
    return {"status": "The Hive is Online", "system": "Nominal"}

@app.post("/alert")
async def report_danger(alerta: Alerta):
    """
    Endpoint para que el 'Fantasma' (Cliente) envíe pánico.
    Member A: Recibe la petición HTTP.
    Member B: La lógica se delega al Executor.
    """
    # No bloqueamos esperando respuesta, lo metemos a la cola
    await executor.add_alert(alerta)
    return {"status": "received", "message": "Calculando evasión..."}

@app.get("/status")
def get_queue_status():
    return {"tareas_pendientes": executor.queue.qsize()}