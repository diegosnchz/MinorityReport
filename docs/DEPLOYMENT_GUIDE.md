# MinorityReport - Guía Definitiva de Deployment y Uso

## Tabla de Contenidos
1. [Requerimientos del Sistema](#requerimientos-del-sistema)
2. [Instalación Inicial](#instalación-inicial)
3. [Deployment Rápido](#deployment-rápido)
4. [Uso Detallado](#uso-detallado)
5. [Entrenamiento de Modelos](#entrenamiento-de-modelos)
6. [Verificación y Testing](#verificación-y-testing)

---

## Requerimientos del Sistema

### Hardware Mínimo

#### Para Desarrollo/Testing
- **CPU**: Intel i5/Ryzen 5 o superior (4+ cores)
- **RAM**: 8 GB mínimo, 16 GB recomendado
- **Disco**: 20 GB libres para Docker + datos
- **GPU**: Opcional (CPU funciona pero es más lento)

#### Para Entrenamiento Óptimo (Recomendado)
- **CPU**: Intel i7/Ryzen 7 o superior
- **RAM**: 16 GB mínimo, 32 GB recomendado
- **Disco**: 50+ GB SSD
- **GPU**: NVIDIA con CUDA 11.8+ (3060 Ti / 4070 Ti / mejor)
- **Memoria VRAM**: 6 GB mínimo (GTX 1660), 12+ GB ideal

### Software Requerido

| Software | Versión Mínima | Para Qué |
|----------|-----------------|----------|
| Docker Desktop | 4.10+ | Ejecutar Neo4j |
| Python | 3.11.0+ | Entrenamiento |
| Git | 2.30+ | Control de versiones |
| NVIDIA CUDA Toolkit | 11.8 | Aceleración GPU (opcional) |
| pip | 22.0+ | Gestor de paquetes Python |

### Verificación de Requisitos

```powershell
# Verificar Docker
docker --version
docker-compose --version

# Verificar Python
python --version

# Verificar Git
git --version

# Verificar NVIDIA (si tienes GPU)
nvidia-smi
```

---

## Instalación Inicial

### 1. Clonar y Preparar Repositorio

```powershell
# Clonar el proyecto
git clone https://github.com/diegosnchz/MinorityReport.git
cd MinorityReport

# Verificar estructura
dir src/models, src/utils, scripts/
```

### 2. Crear Entorno Virtual Python

```powershell
# Crear venv311
python -m venv venv311

# Activar (Windows)
.\venv311\Scripts\Activate.ps1

# Activar (Linux/Mac)
source venv311/bin/activate
```

### 3. Instalar Dependencias

```powershell
# Actualizar pip
pip install --upgrade pip

# Instalar requerimientos base
pip install -r config/requirements.txt

# Para GPU con CUDA 11.8
pip install -r config/requirements_cuda.txt

# O manualmente (si prefieres control)
pip install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install torch-geometric==2.7.0
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch_2.0.0+cu118.html
pip install neo4j pandas numpy scikit-learn
```

### 4. Verificar Instalación

```powershell
# Verificar PyTorch y CUDA
python -c "
import torch
print(f'PyTorch Version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Device: {torch.cuda.get_device_name(0)}')
    print(f'CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')
"

# Verificar PyG
python -c "import torch_geometric; print(f'PyG Version: {torch_geometric.__version__}')"

# Verificar Neo4j
python -c "from neo4j import GraphDatabase; print('Neo4j driver OK')"
```

---

## Deployment Rápido

### Opción 1: Automatizado (Recomendado)

```powershell
# Ejecutar script de deployment completo
.\deploy_real_environment.ps1 -Citizens 200 -Epochs 100

# Opciones:
# -Citizens: Número de ciudadanos a generar (default: 200)
# -Epochs: Épocas de entrenamiento (default: 100)
# -SkipDocker: Saltar Docker si ya está corriendo
# -SkipSeed: No repoblar BD si ya tiene datos
# -SkipTraining: Solo levantar servicios sin entrenar
# -WriteBack: Escribir predicciones de vuelta a Neo4j
```

### Opción 2: Paso a Paso Manual

#### Paso 1: Iniciar Docker y Neo4j
```powershell
# Limpiar contenedores anteriores (si es necesario)
docker-compose down -v

# Iniciar Neo4j
docker-compose up neo4j -d

# Esperar 30 segundos a que inicie
Start-Sleep -Seconds 30

# Verificar que está corriendo
docker ps | Select-String "neo4j"
```

#### Paso 2: Activar Python Environment
```powershell
.\venv311\Scripts\Activate.ps1
```

#### Paso 3: Poblar Base de Datos
```powershell
# Generar datos de prueba
python scripts/seed_neo4j.py --citizens 200

# Opciones:
# --citizens N: Número de ciudadanos (default: 100)
# --no-clear: No limpiar datos anteriores
# --uri: Neo4j URI (default: bolt://localhost:7687)
# --user: Usuario (default: neo4j)
# --password: Contraseña (default: minorityreport)
```

#### Paso 4: Entrenar Modelos
```powershell
# Entrenar ambos modelos
python scripts/train_with_neo4j.py --model both --epochs 100

# Opciones:
# --model {crime,escape,both}: Qué modelo entrenar
# --epochs N: Número de épocas
# --device {cuda,cpu}: Dispositivo (auto-detect si omite)
# --write-back: Guardar predicciones en Neo4j
```

### Opción 3: Entrenar Localmente sin Docker (Solo CPU/GPU)

```powershell
# Entrenar con datos sintéticos (sin Neo4j)
python run_oracle_training.py
python run_graphsage_training.py

# O con datos de Neo4j si quieres Neo4j en otra máquina
python scripts/train_with_neo4j.py --model both --epochs 50 --device cuda
```

---

## Uso Detallado

### Neo4j Browser

**Acceso**: http://localhost:7474

**Credenciales por defecto**:
- Usuario: `neo4j`
- Contraseña: `minorityreport`

**Queries útiles**:

```cypher
// Ver estadísticas
MATCH (n) RETURN labels(n) as tipo, count(*) as cantidad

// Ciudadanos de alto riesgo
MATCH (c:Citizen) WHERE c.preCrimeRiskScore > 0.7 RETURN c.name, c.preCrimeRiskScore ORDER BY c.preCrimeRiskScore DESC

// Ubicaciones conectadas (red de calles)
MATCH (l1:Location)-[r:CONNECTED_TO]->(l2:Location) RETURN l1.name, l2.name, r.distance ORDER BY r.distance

// Ciudadanos visitando ubicaciones
MATCH (c:Citizen)-[v:VISITS]->(l:Location) WHERE v.frequency > 0.5 RETURN c.name, l.name, v.frequency

// Red social de un ciudadano
MATCH (c:Citizen {id: 0})-[:KNOWS]-(friend) RETURN friend.name, friend.preCrimeRiskScore
```

### Cargar y Usar Modelos Entrenados

```python
import torch
from src.models.graphsage_model import create_graphsage_model

# Cargar modelo de predicción de crimen
model = create_graphsage_model(
    in_channels=20,
    hidden_channels=64,
    out_channels=2,
    aggregator='mean'
)
state_dict = torch.load('models/crime_prediction_best.pt')
model.load_state_dict(state_dict)
model.eval()

# Hacer predicción
with torch.no_grad():
    logits = model(x, edge_index)
    probabilities = torch.softmax(logits, dim=1)
    risk_scores = probabilities[:, 1]  # Probabilidad de "alto riesgo"
```

### Integración con API Backend

```python
# ejemplo_api.py
from fastapi import FastAPI
from src.utils.neo4j_data_fetcher import Neo4jDataFetcher

app = FastAPI()

@app.post("/predict/crime-risk")
async def predict_crime_risk(citizen_id: int):
    """Predecir riesgo de crimen para un ciudadano"""
    fetcher = Neo4jDataFetcher()
    citizen_data = fetcher.get_pyg_data(relationship_type="KNOWS")
    
    with torch.no_grad():
        predictions = model(citizen_data.x, citizen_data.edge_index)
        risk_score = float(predictions[citizen_id, 1])
    
    fetcher.close()
    return {"citizen_id": citizen_id, "risk_score": risk_score}
```

---

## Entrenamiento de Modelos

### Parámetros de Entrenamiento

#### Crime Prediction (Predicción de Crimen)
- **Arquitectura**: GCN (Graph Convolutional Network)
- **Input**: Características de ciudadanos (20 features)
- **Output**: Clasificación binaria (alto/bajo riesgo)
- **Learning Rate**: 0.01
- **Weight Decay**: 5e-4
- **Dropout**: 0.5
- **Época ideal**: 30-100 (según dataset)

#### Escape Route (Optimización de Rutas)
- **Arquitectura**: GCN Location
- **Input**: Características de ubicaciones (7 features)
- **Output**: Clasificación binaria (segura/insegura)
- **Learning Rate**: 0.01
- **Weight Decay**: 5e-4
- **Dropout**: 0.5
- **Época ideal**: 30-100 (según dataset)

### Tuning de Hiperparámetros

```powershell
# Entrenar con learning rate custom
python scripts/train_with_neo4j.py --model crime --epochs 200 --device cuda

# Para datasets grandes:
# - Aumentar epochs a 200-500
# - Usar learning rate 0.001-0.005
# - Aumentar batch size si hay VRAM disponible
# - Activar early stopping basado en validación
```

### Monitoreo de Entrenamiento

```python
# Logs se imprimen automáticamente con formato:
# Epoch 010 | Loss: 0.6587 | Train: 0.6357 | Val: 0.5000

# En PyTorch con TensorBoard (opcional):
pip install tensorboard
# Luego modificar scripts para usar SummaryWriter
```

---

## Verificación y Testing

### 1. Verificar Instalación Completa

```powershell
# Script de verificación
python -c "
import torch
from neo4j import GraphDatabase
from torch_geometric.data import Data
from src.utils.neo4j_data_fetcher import Neo4jDataFetcher
from src.models.oracle_net import OracleNet
from src.models.graphsage_model import create_graphsage_model

print('✓ PyTorch:', torch.__version__)
print('✓ CUDA:', 'Disponible' if torch.cuda.is_available() else 'No disponible')
print('✓ Neo4j driver: OK')
print('✓ PyG Data: OK')
print('✓ OracleNet: OK')
print('✓ GraphSAGE: OK')
print('\n[OK] Instalación completa!')
"
```

### 2. Verificar Conectividad Neo4j

```powershell
python -c "
from src.utils.neo4j_data_fetcher import Neo4jDataFetcher

fetcher = Neo4jDataFetcher(
    uri='bolt://localhost:7687',
    user='neo4j',
    password='minorityreport'
)

if fetcher.verify_connection():
    print('[OK] Neo4j accesible')
else:
    print('[ERROR] No se puede conectar a Neo4j')

fetcher.close()
"
```

### 3. Test de Entrenamiento Rápido

```powershell
# Entrenar 5 épocas para verificar que funciona
python scripts/train_with_neo4j.py --model crime --epochs 5

# Si completa sin errores, está todo OK
```

### 4. Verificar Modelos Guardados

```powershell
# Listar modelos
ls -la models/

# Cargar modelo y verificar forma
python -c "
import torch
model = torch.load('models/crime_prediction_best.pt')
print('Modelo cargado correctamente')
print('Parámetros:', sum(p.numel() for p in model.parameters()))
"
```

---

## Accesos y Puertos

| Servicio | URL | Credenciales | Puerto |
|----------|-----|--------------|--------|
| Neo4j Browser | http://localhost:7474 | neo4j / minorityreport | 7474 |
| Neo4j Bolt | bolt://localhost:7687 | neo4j / minorityreport | 7687 |
| OracleNet API | http://localhost:8001 | - | 8001 |
| Police GAN API | http://localhost:8002 | - | 8002 |

---

## Solución Rápida de Problemas Comunes

### "Docker no está ejecutándose"
```powershell
# Solución: Abrir Docker Desktop
# O verificar estado
docker ps
```

### "Neo4j no responde"
```powershell
# Ver logs
docker-compose logs neo4j

# Reiniciar
docker-compose restart neo4j
```

### "No hay CUDA disponible"
```powershell
# Verificar GPU
nvidia-smi

# Reinstalar PyTorch con CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### "Modelos con baja precisión"
```powershell
# Aumentar datos
python scripts/seed_neo4j.py --citizens 500

# Aumentar épocas
python scripts/train_with_neo4j.py --model both --epochs 200

# Mejorar features en seed_neo4j.py
```

---

## Recursos Adicionales

- **PyTorch Geometric Docs**: https://pytorch-geometric.readthedocs.io/
- **Neo4j Cypher Manual**: https://neo4j.com/docs/cypher-manual/
- **CUDA Toolkit**: https://developer.nvidia.com/cuda-toolkit
- **Repositorio**: https://github.com/diegosnchz/MinorityReport

---

**Última actualización**: 25 Enero 2026  
**Estado**: ✅ Operacional  
**Versión**: 1.0.0
