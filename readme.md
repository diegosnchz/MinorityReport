# Project: The Evasion Protocol (Minority Report)

> **Premisa:** En un mundo donde la policía predice el crimen, nosotros somos la anomalía.
> **Objetivo:** Crear un sistema descentralizado que utilice **IA de Grafos (GAT/GCN)** y **HPC** para calcular rutas de escape invisibles a la predicción policial.

---

## 🏛️ Arquitectura Definitiva: Hyper-Scale & Edge-AI

El sistema ha evolucionado de una simple visualización a una infraestructura industrial de nivel militar dividida en tres capas críticas:

```mermaid
graph TD
    subgraph EDGE ["Edge / Sensors"]
        S[loT Sensors / Drones] -->|JSON| N[Nuclio Function]
        N -->|Anonymization & Jitter| N
        N -->|Apache Arrow Buffer| K[Kafka / Event Bus]
    end

    subgraph CORE ["HPC Core (GPU Driven)"]
        K -->|Ingest Stream| R[RAPIDS (cuDF)]
        R -->|Data Wrangling| P[Parquet Lake]
        R -->|Spatial Indexing| Z[Zarr / Xarray Cubes]
        
        subgraph AI ["AI Engine"]
            P -->|Tabular Feats| XG[XGBoost (Risk)]
            Z -->|Spatial Graph| GAT[Graph Attention Network (Node Embed)]
            XG -->|Logits| ENS[Ensemble]
            GAT -->|Embeddings| ENS
            O[Optuna] -.->|Hyperparam Tuning| XG & GAT
            KF[Kubeflow] -->|Orchestration| O
        end
    end

    subgraph VIS ["Command Center"]
        ENS -->|Inference Stream| D[Deck.gl (3D Map)]
        ENS -->|Aggregates| BK[Bokeh (Forense)]
        ENS -->|KPIs| PN[Panel Dashboard]
        
        U[User / CDO] -->|Natural Language| LM[Lumen Chatbot]
        LM -->|Query| PN
    end
```

---

## 🚀 Módulos del Sistema

### 1. Ingesta Zero-Copy & Privacidad (Nuclio + Arrow)
- **Localización:** `edge_serverless/`
- **Nuclio**: Funciones serverless que interceptan datos de drones en el Edge.
- **Privacidad**: Aplicamos Jitter Geoespacial y Hashing SHA-256 antes de que el dato toque el Core.
- **Apache Arrow**: Serialización binaria para transmisión **Zero-Copy** directamente a la VRAM de la GPU.

### 2. Inteligencia Híbrida (XGBoost + GAT)
- **Localización:** `ai_engine/`
- **Motor Híbrido**: Combinamos la potencia tabular de **XGBoost (GPU)** con la comprensión topológica de las **GAT (Graph Attention Networks)**.
- **Optuna**: Optimización bayesiana automática de hiperparámetros con poda de trials ineficientes.
- **Kubeflow**: Orquestación completa del ciclo de vida (ETL -> Tune -> Train -> Deploy).

### 3. Centro de Mando Táctico (HoloViz + Deck.gl)
- **Localización:** `ui_command_center/`
- **Deck.gl 3D**: Mapa de alta fidelidad que visualiza los pesos de atención de la GAT (las rutas de escape que más "brillan").
- **Bokeh Forensics**: Herramientas de *Linked Brushing* para analizar el efecto cascada de las intervenciones policiales.
- **Lumen Agent**: Chatbot conversacional que permite interrogar al dataset de predicciones en lenguaje natural.

---

## 📊 Performance Benchmarks: Legacy vs. HPC

El sistema está optimizado para procesar **millones de eventos** con latencia sub-milisegundo.

| Operación / Cuello de Botella | Stack Legacy (Standard) | Stack HPC (The Evasion Protocol) | Mejora (Speedup) |
| :--- | :--- | :--- | :--- |
| **Data Ingestion (I/O)** | CSV + Pandas (`read_csv`) | Parquet + Apache Arrow (Zero-Copy) | **104x** |
| **Pathfinding Math (CPU)** | Python Puro (Loops) | Numba (`@jit` Compiled C++) | **283x** |
| **ML Inference (Risk)** | Pandas + XGBoost (CPU) | cuDF + XGBoost (`gpu_hist`) | **26x** |
| **Time-Series Slicing** | Cypher Query / SQL | Xarray / Zarr (Data Cubes) | **33x** |

---

## 🛠️ Stack Tecnológico
- **GPU Acceleration**: RAPIDS (cuDF), XGBoost, PyTorch Geometric.
- **Compute**: Numba, Apache Arrow, Xarray.
- **Persistence**: Neo4j, Parquet, Zarr.
- **Orchestration**: Kubeflow, Optuna, Nuclio.
- **Visualization**: Deck.gl, Panel, Bokeh, Lumen.

---

## 🚦 Cómo empezar

1. **Infraestructura**: Levanta Neo4j con `docker-compose up`.
2. **Simulación**: Ejecuta `python tests/test_api_output.py` para verificar el flujo de datos.
3. **Dashboards**: Lanza el centro de mando con `panel serve ui_command_center/dashboards/*.py`.

---
> **Clasificado:** Solo para uso de operativos del Sector Madrid.
