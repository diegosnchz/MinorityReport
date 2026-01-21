# 🔮 Project Pre-Crime: Predictive Justice System

![Python](https://img.shields.io/badge/Python-3.9-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Neo4j](https://img.shields.io/badge/Neo4j-GraphDB-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-GNN-orange)

> *"No construyes un sistema para predecir el futuro. Construyes un sistema para cambiarlo."*

**Project Pre-Crime** es una prueba de concepto (PoC) de un sistema de vigilancia predictiva inspirado en *Minority Report*. Utiliza una arquitectura moderna de **Graph Machine Learning** para analizar patrones en una ciudad sintética y predecir crímenes antes de que ocurran.

## 🏗 Arquitectura

El sistema se aleja de las arquitecturas monolíticas tradicionales (Java/Spring) para abrazar un stack nativo de IA:

1.  **Cerebro (AI Engine):** Modelos **GraphSAGE** y **GAT** (Graph Attention Networks) implementados en PyTorch Geometric. Analizan la topología de la red criminal.
2.  **Memoria (Graph DB):** **Neo4j** almacena la ciudad: 1,000 ciudadanos, ubicaciones y el historial de crímenes.
3.  **Sistema Nervioso (API):** **FastAPI** (Python) orquesta la inferencia en tiempo real, conectando la base de datos con los tensores neuronales.
4.  **Interfaz (Dashboard):** Visualización 3D interactiva usando WebGL (`3d-force-graph`).

## 🚀 Instalación y Despliegue

La forma más sencilla de ejecutar la simulación completa es usando Docker.

### Prerrequisitos
- Docker & Docker Compose instalados.

### Pasos

1.  Clonar el repositorio:
    ```bash
    git clone https://github.com/tu-usuario/project-pre-crime.git
    cd project-pre-crime
    ```

2.  Arrancar los "Precogs":
    ```bash
    docker-compose up --build
    ```

3.  Acceder al Dashboard:
    Abre tu navegador en `http://localhost:8000`.

## 🕹 Uso de la Simulación

1.  **Generación de Mundo:** Al iniciar, el sistema estará vacío. Usa el endpoint `/simulation/generate` (o el script de inicialización) para crear la ciudad sintética.
2.  **Dashboard:** En la pantalla principal verás el grafo 3D.
3.  **Simular:** Haz clic en el botón "RUN SIMULATION STEP".
    *   El sistema moverá a los ciudadanos.
    *   La red neuronal calculará riesgos.
    *   Si se detecta una anomalía (>85%), aparecerá una "Bola Roja" (Nodo de Visión) en el grafo.

## 🛠 Tech Stack

*   **Lenguaje:** Python 3.9
*   **Web Framework:** FastAPI + Uvicorn
*   **Database:** Neo4j (Cypher Query Language)
*   **ML Libraries:** PyTorch, PyTorch Geometric, Scikit-Learn
*   **Data Validation:** Pydantic v2
*   **Frontend:** HTML5, 3d-force-graph.js

## 📄 Estructura del Proyecto

```text
/app
├── core/         # Configuración de DB y Carga de Modelos
├── models/       # Esquemas Pydantic (Citizens, Crimes, Visions)
├── repositories/ # Consultas Cypher optimizadas
├── routers/      # Endpoints de la API
├── services/     # Lógica de negocio y Simulación
└── static/       # Dashboard HTML/JS
```

## ⚖️ Nota Ética

Este proyecto es una exploración técnica de las capacidades de las GNNs (Graph Neural Networks). No debe utilizarse como base para sistemas de vigilancia reales sin capas profundas de auditoría ética, explicabilidad (XAI) y supervisión humana, debido a los riesgos inherentes de sesgo algorítmico en datos policiales.