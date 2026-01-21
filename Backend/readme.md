¡Excelente rol! Ser los Operadores (Backend & Execution Core) significa ser el sistema nervioso central de "The Evasion Protocol". Sin vosotros, el modelo de IA es solo matemática en un papel y el cliente es solo un dibujo bonito.

Dado que sois dos personas (Pair Programming) y tenéis que integrar partes críticas (Neo4j, Cola FIFO, API y llamada al modelo AI), os propongo una arquitectura robusta pero ágil usando Python + FastAPI. FastAPI es ideal porque maneja asincronía nativa (perfecto para colas y bases de datos).

Aquí tenéis la hoja de ruta técnica paso a paso para implementar vuestra rama feature/production-core.

📂 Estructura de Archivos Recomendada
Organizad vuestro código así para separar responsabilidades (Member A vs Member B):

Plaintext

/backend
│
├── main.py            # (Member A) Punto de entrada y Endpoints API
├── database.py        # (Member A) Conexión Singleton con Neo4j
├── executor.py        # (Member B) La lógica de la Cola FIFO y el Worker
├── ai_interface.py    # (Member B) Wrapper para llamar al código del "Oráculo"
└── models.py          # (Shared) Definición de esquemas de datos (Pydantic)
Paso 1: Definir los Datos (Shared)
Primero, acordad qué datos viajan por el sistema en models.py.

Python

# models.py
from pydantic import BaseModel
from typing import List, Optional

class Alerta(BaseModel):
    ladron_id: str
    ubicacion_actual_id: str
    amenaza_detectada: str # Ej: "PATRULLA", "DRONE"
    nivel_riesgo: float

class RutaEscape(BaseModel):
    destino_seguro: str
    camino_nodos: List[str]
    probabilidad_exito: float
Paso 2: Conexión a Neo4j (Member A)
Tu misión es crear una conexión eficiente que no se abra y cierre en cada petición. Usaremos el patrón Singleton en database.py.

Python

# database.py
from neo4j import GraphDatabase
import os

class Neo4jProvider:
    def __init__(self):
        # En producción usar variables de entorno
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "secret_password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def actualizar_riesgo_nodo(self, nodo_id, riesgo_adicional):
        """
        Consulta Cypher para aumentar el riesgo de un nodo y sus vecinos
        """
        query = """
        MATCH (n:Escondite {name: $id})
        SET n.riesgo = n.riesgo + $riesgo
        WITH n
        MATCH (n)-[r:CONECTA_CON]-(vecino)
        SET vecino.riesgo = vecino.riesgo + ($riesgo * 0.5)
        RETURN n, vecino
        """
        with self.driver.session() as session:
            session.run(query, id=nodo_id, riesgo=riesgo_adicional)
            print(f"⚠️ Neo4j: Riesgo actualizado en zona {nodo_id}")

db = Neo4jProvider()
Paso 3: El Executor y la Cola FIFO (Member B)
Esta es la parte crítica de la "Sección 8" de vuestros apuntes. Necesitáis un sistema que ingiera alertas rápido (API) y las procese una a una (Worker) para no saturar el cálculo de la IA.

Usaremos asyncio.Queue para simular esta cola en memoria.

Python

# executor.py
import asyncio
from models import Alerta
from database import db
# from ai_module import GATModel  <-- Aquí importaríais el código del Oráculo

class CrisisExecutor:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_running = False

    async def add_alert(self, alerta: Alerta):
        """Método Productor: Mete eventos a la cola"""
        print(f"📥 Cola: Recibida alerta de {alerta.ladron_id}")
        await self.queue.put(alerta)

    async def run_worker(self):
        """Método Consumidor: Procesa eventos en background"""
        self.is_running = True
        print("⚙️ Executor: Worker iniciado y esperando amenazas...")
        
        while self.is_running:
            # 1. Sacar de la cola (FIFO)
            alerta = await self.queue.get()
            
            # 2. Procesamiento (Simulando carga de trabajo)
            print(f"🔥 Executor: Procesando amenaza en {alerta.ubicacion_actual_id}")
            
            # A. Actualizar Grafo (Persistencia)
            # Llamamos a la función de Member A
            db.actualizar_riesgo_nodo(alerta.ubicacion_actual_id, alerta.nivel_riesgo)

            # B. Invocar IA (GAT) - Simulado
            # ruta = GATModel.predict(grafo_actualizado)
            await asyncio.sleep(1) # Simular tiempo de cálculo de la IA
            
            # C. Lógica Gossip (Sección 6): Notificar a otros
            self.broadcast_danger(alerta)

            self.queue.task_done()

    def broadcast_danger(self, alerta):
        """Simulación simple de protocolo Gossip"""
        print(f"📡 GOSSIP: ¡Atención a todos los ladrones! Evitar sector {alerta.ubicacion_actual_id}")

# Instancia global
executor = CrisisExecutor()
Paso 4: La API (Member A + Integración)
Finalmente, en main.py unís todo. Es importante levantar el worker del Executor cuando arranca la app.

Python

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
🧪 Cómo probar que funciona (Flujo del Juego)
Levantar Neo4j: Aseguraos de que el Docker de Neo4j está corriendo.

Ejecutar la API:

Bash

uvicorn main:app --reload
Simular un Ladrón (Client): Abrid otra terminal y enviad una alerta con curl (o usad Postman):

Bash

curl -X 'POST' \
  'http://127.0.0.1:8000/alert' \
  -H 'Content-Type: application/json' \
  -d '{
  "ladron_id": "Ghost_1",
  "ubicacion_actual_id": "Sotano Bar",
  "amenaza_detectada": "PRECRIMEN_UNIT",
  "nivel_riesgo": 0.9
}'
Lo que veréis en la consola del servidor:

📥 Cola: Recibida alerta de Ghost_1 (Inmediato)

🔥 Executor: Procesando amenaza en Sotano Bar (El worker se despierta)

⚠️ Neo4j: Riesgo actualizado en zona Sotano Bar (Database hit)

📡 GOSSIP: ¡Atención a todos los ladrones!... (Notificación)

💡 Valor Extra para vuestra nota
Para destacar en la parte de "Operadores", aseguraos de explicar bien el concepto de Desacoplamiento.

Decid: "Usamos una cola FIFO porque si 50 ladrones envían alertas a la vez, no queremos que la API se caiga intentando recalcular la IA 50 veces simultáneamente. La API solo recibe (rápido) y el Executor procesa (ordenado)."

¿Queréis que profundice en cómo conectar la salida del Executor con el Frontend para que se dibuje la línea roja/verde?