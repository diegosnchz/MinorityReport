# Data Integration Guide: dataEngineer → feature/gat-model

## Resumen en Español 🇪🇸

Este documento explica cómo usar los datos de la branch `dataEngineer` para entrenar los modelos GAT en `feature/gat-model`.

### ¿Qué datos están disponibles en dataEngineer?

La branch `dataEngineer` contiene un sistema completo de generación y procesamiento de datos para el sistema Pre-Crime:

#### 1. **Generación de Datos de Ciudad** (`src/scripts/init_city_graph.py`)
- Genera **1000 ciudadanos** con características:
  - `id`: Identificador único
  - `name`: Nombre generado con Faker
  - `born`: Año de nacimiento
  - `risk_seed`: Semilla de riesgo (valor entre 0-1, distribución Beta)
  - `job`: Profesión del ciudadano
  
- Genera **50 ubicaciones** con:
  - Tipos: Bank, Jewelry Store, Subway Station, Dark Alley, Park, Cafe, Apartment Block
  - Coordenadas geográficas (latitud/longitud)
  - Factor de riesgo ambiental (`env_risk`)

- **Relaciones en el grafo:**
  - `KNOWS`: Conexiones sociales entre ciudadanos
  - `COMMITTED_CRIME`: Historial criminal
  - `VISITED`: Visitas a ubicaciones

#### 2. **Carga y Procesamiento de Datos** (`src/ai/graph_loader.py`)
Convierte datos de Neo4j a formato PyTorch Geometric:

- **Características procesadas:**
  - `age`: Edad normalizada (0-1)
  - `crim_deg` (criminal_degree): Número de amigos criminales
  - `job_*`: One-hot encoding de profesiones
  
- **Target (etiqueta):**
  - `risk_seed`: La variable que el modelo debe predecir

- **Estructura del grafo:**
  - Nodos: Ciudadanos
  - Edges: Relaciones sociales (KNOWS)

#### 3. **Modelo de Entrenamiento** (`train.py`)
- Implementación GAN (Generative Adversarial Network)
- Generator: Predice comportamiento criminal
- Discriminator: Detecta patrones de riesgo

### ¿Cómo usar estos datos en feature/gat-model?

#### Opción 1: Acceso Directo a Neo4j
```python
# Usa el cliente Neo4j para cargar datos
from src.utils.neo4j_data_fetcher import fetch_graph_data

data = fetch_graph_data()
# data contiene: x (features), edge_index (conexiones), y (labels)
```

#### Opción 2: Scripts de Exportación
```bash
# Exportar datos de Neo4j a archivos
python scripts/export_data_from_neo4j.py --output data/
# Genera: citizens.csv, edges.csv, features.pt
```

#### Opción 3: Copiar Utilidades de dataEngineer
Los siguientes archivos pueden ser adaptados:
- `graph_loader.py` → Convertir a formato compatible con GAT
- `neo4j_client.py` → Cliente de base de datos
- `init_city_graph.py` → Regenerar datos si es necesario

---

## English Summary 🇬🇧

### Available Data in dataEngineer Branch

**Key Components:**

1. **City Data Generator** (`src/scripts/init_city_graph.py`)
   - 1000 citizens with demographic and behavioral features
   - 50 locations with spatial coordinates and risk factors
   - Graph relationships: social network (KNOWS), crimes, visits

2. **Data Loader** (`src/ai/graph_loader.py`)
   - Converts Neo4j graph to PyTorch Geometric format
   - Feature engineering: age normalization, one-hot encoding, criminal influence
   - Target: risk_seed (latent risk variable)

3. **Training Pipeline** (`train.py`)
   - GAN-based adversarial training
   - Crime prediction models

### Integration Methods

#### Method 1: Direct Neo4j Access
Create a utility to query Neo4j and load data in real-time.

#### Method 2: Data Export Scripts
Export processed data to files (CSV, PyTorch tensors) for offline training.

#### Method 3: Adapt Existing Utilities
Copy and modify `graph_loader.py` to work with GAT models.

---

## Data Schema

### Node Features (Citizen)
| Feature | Type | Description | Range |
|---------|------|-------------|-------|
| age | float | Normalized age | 0.0 - 1.0 |
| criminal_degree | int | Number of criminal friends | 0 - N |
| job_* | binary | One-hot encoded profession | 0 or 1 |

### Graph Structure
- **Nodes**: Citizens (1000)
- **Edges**: Social connections (KNOWS relationships)
- **Labels**: risk_seed (regression target, 0-1)

### Location Features
| Feature | Type | Description |
|---------|------|-------------|
| type | string | Location category |
| env_risk | float | Environmental risk factor |
| coordinates | point | Geographic location |

---

## Next Steps

1. ✅ Document available data (this file)
2. ⏳ Create data fetcher utility for Neo4j
3. ⏳ Create data export scripts
4. ⏳ Adapt graph_loader for GAT models
5. ⏳ Test integration with sample data
6. ⏳ Train GAT model with real data

---

## Important Notes

⚠️ **DO NOT MODIFY dataEngineer BRANCH** - Only read/copy data from it
⚠️ All integration work happens in `feature/gat-model` branch
⚠️ Neo4j must be running with the generated city graph for live data access
