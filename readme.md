# Project: The Evasion Protocol (Minority Report - Robbers Side)

> **Premisa:** En un mundo donde la policía predice el crimen, nosotros somos la anomalía.
> **Objetivo:** Crear un sistema descentralizado que utilice **IA de Grafos (GAT/GCN)** para calcular rutas de escape dinámicas e invisibles a la predicción policial estándar.

---

## Arquitectura del Sistema

El sistema sigue un modelo **Cliente-Servidor con Persistencia en Grafos**, dividido en dos capas principales:

1.  **Capa de Producción (The Hive):** Servidor central (o distribuido) que procesa la lógica pesada, gestiona la cola de eventos y consulta la base de datos de conocimiento.
2.  **Capa de Cliente (The Ghost):** Interfaz ligera para los "ladrones" que visualiza el mapa y recibe instrucciones de evasión en tiempo real.

### Tecnologías Clave (Basado en Apuntes de Clase)
* **Core IA:** GCN (Contexto) y GAT (Atención Selectiva).
* **Precog v2.0 (Advanced):** TGN (Memoria Temporal) y GNNExplainer (XAI).
* **Persistencia:** Neo4j (Graph Database).
* **Ejecución:** Modelo `Executor` con Colas (FIFO) para gestión de crisis.
* **Red:** Simulación de protocolo Gossip para comunicación entre ladrones.

---

## Distribución de Roles y Ramas de Git

Somos 5 integrantes divididos en 4 ramas funcionales. El Backend (Core) soporta la carga de trabajo de dos personas.

### 1. El Arquitecto del Grafo (Data Engineer)
* **Rama:** `feature/neo4j-topology`
* **Responsable:** 1 Integrante
* **Misión:** Construir el "Knowledge Graph" de la ciudad.
* **Tareas:**
    * Levantar instancia Docker de **Neo4j**.
    * **Modelado del Grafo (Ref: Sección 1 y 4 apuntes):**
        * Definir Nodos: `Escondite`, `Banco`, `Comisaría`, `PuntoCiego`.
        * Definir Relaciones: `CONECTA_CON` (peso: distancia), `VIGILADO_POR` (peso: riesgo).
    * Crear scripts de "Seed Data" para poblar la ciudad inicial.

### 2. El Oráculo (AI Specialist)
* **Rama:** `feature/gat-model`
* **Responsable:** 1 Integrante
* **Misión:** El cerebro que decide por dónde huir.
* **Tareas:**
    * Implementar **GCN (Sección 2)**: Para que cada nodo sepa el nivel de peligro promedio de su vecindario.
    * Implementar **GAT (Sección 3)**: La joya del proyecto.
        * *Lógica:* El mecanismo de atención ($\alpha$) debe priorizar aristas con bajo riesgo policial y alta ocultación.
        * *Input:* Matriz de Adyacencia + Features (Nivel de Policia).
        * *Output:* Probabilidad de "Ruta Segura".

### 3. Los Operadores (Backend & Execution Core)
* **Rama:** `feature/production-core`
* **Responsables:** 2 Integrantes (Pair Programming)
* **Misión:** Orquestar la lógica y asegurar que el sistema no colapse.
* **Tareas Integrante A (API & State):**
    * Crear API (FastAPI/Flask) para recibir coordenadas de los ladrones.
    * Conexión driver con Neo4j.
* **Tareas Integrante B (Executor & Queue - Sección 8 apuntes):**
    * Implementar una **Cola (FIFO)** para recibir alertas ("¡Policía en sector 4!").
    * Implementar el **Executor**: Un worker que toma alertas de la cola, invoca al modelo GAT y devuelve la ruta.
    * *Extra:* Lógica básica de **Mesh/Gossip (Sección 6)** para notificaciones de peligro.

### 4. El Fantasma (Frontend Client)
* **Rama:** `feature/ghost-client`
* **Responsable:** 1 Integrante
* **Misión:** Visualización táctica para el usuario.
* **Tareas:**
    * Visualización del Grafo (similar a `graph-viz` en los apuntes).
    * Interfaz de estado: "Seguro" (Verde) vs "Detectado" (Rojo).
    * Botón de Pánico que envía petición a la API.

---

## Flujo Técnico del "Juego"

### Escenario: Evasión en Tiempo Real

1.  **Trigger:** El Ladrón 1 avista un coche patrulla y pulsa "Alerta" en el Cliente.
2.  **Ingesta (Queue):** La API recibe la alerta y la mete en la `TaskQueue` (Fundamento: Cola FIFO).
3.  **Procesamiento (Executor):**
    * El `Executor` hace *pull* de la tarea.
    * Consulta a **Neo4j** el estado actual de los nodos cercanos.
    * Actualiza el peso de la arista a "RIESGO ALTO".
4.  **Inteligencia (GAT):**
    * El modelo GAT recalcula los coeficientes de atención.
    * Las conexiones hacia la zona del patrulla reciben atención $\approx 0$.
    * Se ilumina una ruta de callejones traseros (atención alta).
5.  **Respuesta:** El Cliente recibe la nueva lista de nodos y dibuja el camino en el mapa.

---

## Getting Started (Comandos Rápidos)

### 1. Levantar Infraestructura (Neo4j)
```bash
# docker-compose.yml (Skeleton)
version: '3.8'
services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474" # HTTP
      - "7687:7687" # Bolt
    environment:
      NEO4J_AUTH: neo4j/secret_password
```

### 2. Estructura de Datos (Cypher Query Ejemplo)
```cypher
// Crear un nodo seguro conectado a una calle peligrosa
CREATE (s:Escondite {name: 'Sotano Bar'})
CREATE (c:Calle {name: 'Gran Via', riesgo: 0.9})
CREATE (s)-[:CONECTA_CON {distancia: 10}]->(c)
```

### 3. Ejecución del Modelo (Pseudo-Python)
```python
# Lógica del Oráculo
def predecir_ruta(grafo_data):
    # GAT Layer
    x, edge_index = grafo_data.x, grafo_data.edge_index
    # La atención pondera la seguridad, no solo la distancia
    x = gat_conv(x, edge_index) 
    return ruta_optima(x)
```

---

## Pre-Crime v2.0: Intel Avanzado

Hemos evolucionado el sistema para superar la predicción policial estándar mediante dos módulos críticos:

### 1. Memoria Temporal (TGN - Temporal Graph Networks)
El sistema ya no solo mira "quién conoce a quién", sino **cuándo** y **con qué frecuencia** interactúan.
*   **Módulo:** `PrecogTGN` en `app/models/neural_net.py`.
*   **Función:** Detecta ráfagas de actividad sospechosa en el tiempo. Permite al sistema anticiparse a redadas basándose en secuencias de movimientos, no solo en fotos estáticas.

### 2. Transparencia y Auditoría (XAI - Explainable AI)
Para entender por qué el Oráculo marca un riesgo, hemos implementado **GNNExplainer**.
*   **Endpoint:** `GET /visions/{vision_id}/explain`
*   **Respuesta:** Devuelve un desglose de las conexiones exactas que están inflando el nivel de riesgo.
*   **Uso:** Permite a los operativos saber si una alerta es por un contacto social ("Conoce a X") o por una acción física ("Estuvo en el Banco Y").

> **Nota para el equipo:** El dashboard 3D (`/static/index.html`) visualiza estas alertas en tiempo real.

## Pre-Crime v3.0: Hyper-Scale Data Engine (HPC)

Para procesar terabytes de datos de la ciudad en milisegundos y evitar la captura, hemos reescrito el núcleo del sistema utilizando un stack de **Computación de Alto Rendimiento (HPC)**.

### Optimizaciones Críticas Implementadas:
1. **The Data Highway (Apache Arrow & Parquet):** Se acabó consultar la base de datos (Neo4j) en cada tick. El histórico de crímenes se mapea directamente a la RAM mediante *Zero-Copy* con **Arrow**, eliminando la latencia de I/O.
2. **GPU Acceleration (NVIDIA RAPIDS):** Procesamiento de datos (cuDF) y modelo base (XGBoost) ejecutados 100% en la VRAM de la GPU.
3. **Cálculo a Velocidad de Luz (Numba JIT):** Las funciones matemáticas pesadas de la heurística de evasión están compiladas en código máquina C++ usando `@jit`, haciendo el cálculo de rutas un 50x más rápido.
4. **Cubos de Datos Climáticos (Zarr & Xarray):** Análisis multidimensional de patrones de crimen históricos usando tensores, superando las limitaciones del SQL tradicional.

> **Nota de Rendimiento:** La inferencia ahora ocurre en `< 15ms`. Somos literalmente más rápidos que el sistema que intenta atraparnos.
