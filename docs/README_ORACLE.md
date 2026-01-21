# OracleNet - The Oracle's Escape Route Optimizer 🔮

## Descripción General

**OracleNet** es un modelo de Inteligencia Artificial basado en Graph Neural Networks (GNN) diseñado para el lado de los ladrones en "Minority Report - Robbers Side". Su objetivo es calcular rutas de escape óptimas en una ciudad vigilada por policía predictiva.

## Arquitectura del Modelo

### 1. GCN (Graph Convolutional Network)
**Propósito**: Comprensión del contexto del vecindario

Las capas GCN permiten que cada nodo (intersección) entienda el nivel de peligro agregando información de sus vecinos:

```
h^(l+1) = σ(D^(-1/2) A D^(-1/2) h^(l) W^(l))
```

Donde:
- `h^(l)`: Features del nodo en capa l
- `A`: Matriz de adyacencia
- `D`: Matriz de grado
- `W^(l)`: Matriz de pesos entrenables
- `σ`: Función de activación (ReLU)

### 2. GAT (Graph Attention Network)
**Propósito**: Ponderación inteligente de rutas usando mecanismo de atención

GAT usa **atención multi-cabeza** para aprender qué conexiones son más seguras:

#### Mecanismo de Atención (α):

1. **Transformación Lineal**:
   ```
   h'_i = W · h_i
   ```

2. **Score de Atención**:
   ```
   e_ij = LeakyReLU(a^T [W h_i || W h_j])
   ```

3. **Normalización Softmax**:
   ```
   α_ij = softmax_j(e_ij) = exp(e_ij) / Σ_k exp(e_ik)
   ```

4. **Agregación Ponderada**:
   ```
   h'_i = σ(Σ_j α_ij W h_j)
   ```

**Interpretación en nuestro contexto**:
- `α_ij` alto → La calle de i a j es **SEGURA** (bajo riesgo policial)
- `α_ij` bajo → La calle de i a j es **PELIGROSA** (alto riesgo)

### 3. Edge Scoring Network
**Propósito**: Cálculo de seguridad por arista

Toma los embeddings de nodos procesados y calcula un score de seguridad [0, 1] para cada arista:
- **0**: Ruta muy peligrosa (alta presencia policial)
- **1**: Ruta muy segura (baja presencia policial, buena cobertura)

## Entrada y Salida del Modelo

### Input
- **Matriz de Adyacencia** (`edge_index`): [2, num_edges]
- **Features de Nodos** (`x`): [num_nodes, num_features]
  - Feature 0: Nivel de presencia policial (0-1)
  - Feature 1: Tipo de nodo (0=calle, 1=callejón, 2=edificio, 3=parque)
  - Feature 2: Nivel de iluminación
  - Feature 3: Densidad de población
  - Features 4+: Otras características

### Output
- **Safety Scores** por arista: [num_edges, 1]
  - Valores en [0, 1]
  - Indica la probabilidad de que una ruta sea segura
- **Attention Weights** (opcional): Pesos de atención de GAT para análisis

## Configuración Hardware

### GPU Recomendada: NVIDIA Quadro K4200 4GB

Basado en las especificaciones del sistema:
- **GPU**: NVIDIA Quadro K4200 4GB
- **RAM**: 32 GB
- **CPU**: Intel Xeon E5-1620 v3 @ 3.50GHz

**Recomendación**: ✅ **Usar GPU para entrenamiento**

#### ¿Por qué GPU?
1. **Paralelización Masiva**: GNNs involucran muchas operaciones de álgebra lineal (multiplicaciones de matrices) que se benefician enormemente de la paralelización de GPU
2. **Eficiencia en Grafos Medianos**: Con 4GB VRAM, la Quadro K4200 puede manejar eficientemente grafos de:
   - 100-300 nodos por batch
   - 300-900 aristas por batch
3. **Speedup Esperado**: 5-10x más rápido que CPU para modelos GNN de este tamaño

#### Comparación Estimada (100 epochs):
- **CPU**: ~15-20 minutos
- **GPU**: ~2-4 minutos
- **CPU**: ~2-3 minutos (en equipos modernos)

## Instalación

### 0. Requisitos de Python

**IMPORTANTE**: Se recomienda Python 3.11 o 3.12 para mejor compatibilidad con PyTorch.

Si usas Python 3.14, el modelo funcionará en CPU (sin problemas).

**Instalación rápida** (Windows):
```powershell
# 1. Crea el entorno virtual con Python 3.11
py -3.11 -m venv venv311

# 2. Activa
.\venv311\Scripts\Activate.ps1

# 3. Instala dependencias
pip install --upgrade pip
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
pip install torch-geometric neo4j networkx numpy pandas matplotlib seaborn tqdm scipy scikit-learn
```

### 1. Auto-detección de Device (GPU/CPU)

El código **detecta automáticamente** la mejor opción:
- **GPU CUDA** (NVIDIA) si está disponible
- **GPU MPS** (Apple Metal) si está disponible  
- **CPU** como fallback universal

No necesitas hacer nada especial, el modelo se configurará solo.

### 2. Verificar Instalación

```bash
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

O ejecuta el test de device:
```bash
python device_utils.py
```

## Uso

### Prueba Rápida (Smoke Test)

```bash
python oracle_net.py
```

Esto ejecutará una prueba rápida del modelo con un grafo sintético y mostrará:
- Configuración del dispositivo (GPU/CPU, con detalles)

- Estadísticas del modelo (parámetros)
- Análisis de seguridad de rutas
- Top 5 rutas más seguras y peligrosas

### Entrenamiento Completo

```bash
python train_oracle.py
```

Esto:
1. Generará grafos sintéticos de ciudades con diferentes niveles de vigilancia
2. Entrenará OracleNet por 200 épocas
3. Guardará el mejor modelo en `oracle_net_best.pth`
4. Ejecutará una simulación de escape al final

### Uso Programático

```python
from oracle_net import create_oracle_net
import torch

# Crear modelo
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = create_oracle_net(num_features=16, device=device)

# Preparar datos (ejemplo)
x = torch.randn(50, 16, device=device)  # 50 nodos, 16 features
edge_index = torch.randint(0, 50, (2, 150), device=device)  # 150 aristas

# Inferencia
model.eval()
with torch.no_grad():
    safety_scores, attention_weights = model(x, edge_index, return_attention=True)

# Analizar resultados
safe_routes = (safety_scores > 0.7).sum().item()
print(f"Rutas seguras encontradas: {safe_routes}")
```

## Componentes Técnicos Detallados

### 1. Transformación Lineal
Cada capa GNN aplica una transformación lineal paramétrica a los features:
```python
self.gcn1 = GCNConv(in_channels, hidden_channels)  # W · x
```

### 2. Función de Activación
Se usan diferentes funciones según la capa:
- **ReLU**: En capas GCN → `F.relu(x)`
- **ELU**: En capas GAT → `F.elu(x)` (mejor para gradientes en GAT)
- **Sigmoid**: En output final → `torch.sigmoid(x)` (score 0-1)

### 3. Normalización Softmax
En GAT, los scores de atención se normalizan usando softmax:
```python
α_ij = exp(e_ij) / Σ_k exp(e_ik)
```
Esto asegura que Σ_j α_ij = 1 (distribución de probabilidad)

### 4. Atención Multi-Cabeza
OracleNet usa 4 cabezas de atención en GAT:
```python
self.gat1 = GATConv(hidden_channels, hidden_channels // num_heads, heads=4)
```

Cada cabeza aprende diferentes aspectos de seguridad:
- Cabeza 1: Nivel policial
- Cabeza 2: Cobertura/ocultación
- Cabeza 3: Densidad de escape
- Cabeza 4: Rutas alternativas

Las salidas se concatenan: `[head1 || head2 || head3 || head4]`

## Estructura del Código

```
MinorityReport/
├── oracle_net.py           # Definición del modelo OracleNet
├── train_oracle.py         # Script de entrenamiento
├── models.py               # GAN para policía (Generator + Discriminator)
├── train.py                # Entrenamiento del GAN policial
├── gossip_protocol.py      # Protocolo de sincronización distribuida
├── neo4j_integration.cypher # Queries para Neo4j
├── architecture_design.md  # Diseño arquitectónico general
├── requirements.txt        # Dependencias Python
└── README_ORACLE.md        # Esta documentación
```

## Flujo de Datos

```
┌─────────────────────────────────────────────────────┐
│  Neo4j Database                                     │
│  - Nodos: Ubicaciones con features                 │
│  - Aristas: Calles con propiedades                 │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  Graph Data (PyTorch Geometric)                     │
│  - x: [num_nodes, 16]                              │
│  - edge_index: [2, num_edges]                      │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  OracleNet (GCN + GAT)                             │
│                                                     │
│  [Input] → [GCN Layer 1] → [GCN Layer 2]          │
│         → [GAT Layer 1] → [GAT Layer 2]           │
│         → [Edge Scorer] → [Output]                │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  Safety Scores per Edge                             │
│  - [num_edges, 1] tensor                           │
│  - Values in [0, 1]                                │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  Pathfinding Algorithm (A* modificado)             │
│  - Input: start_node, end_node, safety_scores     │
│  - Output: Optimal escape route                    │
└─────────────────────────────────────────────────────┘
```

## Analogía: Generador vs Discriminador (GAN)

El proyecto incluye dos "cerebros" de IA que compiten:

### 👮 El Discriminador (La Policía)
- **Archivo**: `models.py` - clase `Discriminator`
- **Modelo**: GAT (Graph Attention Network)
- **Objetivo**: Detectar patrones criminales en el grafo
- **Output**: Probabilidad de amenaza por nodo

### 🎭 El Generador (El Falsificador/Criminal)
- **Archivo**: `models.py` - clase `Generator`
- **Modelo**: GraphSAGE
- **Objetivo**: Generar patrones que engañen al Discriminador
- **Output**: Embeddings sintéticos de "comportamiento criminal"

### 🔮 El Oráculo (El Escape Artist)
- **Archivo**: `oracle_net.py` - clase `OracleNet`
- **Modelo**: GCN + GAT (híbrido)
- **Objetivo**: Encontrar rutas seguras evitando la vigilancia
- **Output**: Scores de seguridad por arista

## Entrenamiento Adversarial (GAN para contexto)

Aunque OracleNet no es parte del GAN, el sistema completo usa entrenamiento adversarial:

```python
# Discriminador aprende a detectar crímenes
d_loss = -[log D(real) + log(1 - D(fake))]

# Generador aprende a engañar
g_loss = -log D(G(z))
```

El Oráculo aprovecha que el Discriminador (policía) tiene sesgos y puntos ciegos.

## Métricas de Rendimiento

Durante el entrenamiento se monitorean:

1. **Train Loss**: Binary Cross Entropy en conjunto de entrenamiento
2. **Validation Loss**: BCE en conjunto de validación
3. **Validation Accuracy**: Precisión en clasificación de aristas (safe vs dangerous)
4. **Learning Rate**: Ajustado automáticamente con ReduceLROnPlateau

## Gestión Automática de GPU/CPU (device_utils.py)

### 🎯 Auto-Detección de Dispositivo

OracleNet incluye un módulo inteligente (`device_utils.py`) que **detecta y selecciona automáticamente** el mejor dispositivo:

```python
from device_utils import get_device, print_device_info

# Auto-detección: GPU CUDA → GPU MPS → CPU
device = get_device()
print_device_info()  # Muestra información detallada del dispositivo
```

### Orden de Prioridad

1. **GPU CUDA** (NVIDIA) - Más rápido, si está disponible
2. **GPU MPS** (Apple Metal Performance Shaders) - Para Macs con Apple Silicon
3. **CPU** - Compatible con cualquier sistema

### ¿Cómo Funciona?

```python
# En oracle_net.py y train_oracle.py
device = get_device()  # Automático

# O specificar explícitamente
device = get_device(force_cpu=True)  # Fuerza CPU

# O via variable de entorno
import os
os.environ['FORCE_CPU'] = 'true'
device = get_device()  # Respeta la variable
```

### Funciones Disponibles en device_utils.py

| Función | Descripción | Ejemplo |
|---------|-------------|---------|
| `get_device()` | Detecta mejor dispositivo | `dev = get_device()` |
| `get_device(force_cpu=True)` | Fuerza uso de CPU | `dev = get_device(force_cpu=True)` |
| `is_cuda_available()` | Verifica CUDA disponible | `if is_cuda_available(): ...` |
| `get_device_info()` | Dict con detalles del device | `info = get_device_info()` |
| `print_device_info()` | Imprime información formateada | `print_device_info()` |
| `empty_cuda_cache()` | Libera memoria de GPU | `empty_cuda_cache()` |

### Información del Device

```python
from device_utils import print_device_info

print_device_info()
```

Salida típica:
```
=== Device Configuration ===
Device: cuda (NVIDIA GPU)
GPU Name: NVIDIA GeForce RTX 3090
CUDA Capability: 8.6
Total VRAM: 24 GB
Allocated Memory: 2.1 GB
Reserved Memory: 3.0 GB
Available Memory: 21.9 GB

PyTorch Version: 2.0.1
CUDA Version: 11.8
cuDNN Version: 8.6
```

### Comportamiento Automático en Scripts

#### oracle_net.py
```python
device = get_device()  # Automático
model = create_oracle_net(num_features=16, device=device)
print_device_info()  # Muestra configuración

# Modelo listo en GPU/CPU según disponibilidad
```

#### train_oracle.py
```python
device = get_device()  # Automático
model = train_oracle_net(num_epochs=200, device=device)
# Entrenamiento 5-10x más rápido en GPU si está disponible
```

### Casos de Uso

#### 🖥️ Desarrollador con GPU NVIDIA
```powershell
python oracle_net.py      # Usa GPU automáticamente (2-4 min para entrenamiento)
```

#### 💻 Desarrollador sin GPU (MacBook, laptops, etc.)
```bash
python oracle_net.py      # Usa CPU automáticamente (fallback transparente)
```

#### 🔧 Forzar CPU (para debugging)
```powershell
$env:FORCE_CPU = 'true'
python oracle_net.py      # Usa CPU incluso si GPU está disponible
```

### Optimizaciones Automáticas

- **GPU**: Modelos cargados directamente en VRAM
- **CPU**: Modelos en RAM, operaciones optimizadas con MKL
- **Fallback**: Si GPU falla, automáticamente intenta CPU

### Compatibilidad Hardware

#### ✅ GPU Soportadas
- NVIDIA: GeForce RTX (cualquier serie), Tesla, Quadro (Compute Capability ≥ 5.0)
- Apple: Mac M1/M2/M3 con MPS
- AMD: ROCm (experimental)

#### ❌ GPU No Soportadas
- NVIDIA Quadro K4200 (Kepler, Compute Cap 3.0) - **Usará CPU automáticamente**
- GPU antiguas (pre-2012)
- Intel Arc (parcial)

### Rendimiento Esperado

| Device | 100 Epochs | 200 Epochs |
|--------|-----------|-----------|
| GPU NVIDIA RTX 3090 | 1-2 min | 2-4 min |
| GPU NVIDIA Quadro P6000 | 2-4 min | 5-8 min |
| CPU Intel Xeon E5 (8c) | 15-20 min | 30-40 min |
| CPU Apple M1/M3 | 5-10 min | 10-20 min |

**Nota**: Quadro K4200 en nuestro sistema usará CPU como fallback (no GPU).

## Nuevas Características: GraphSAGE con Mini-batch Training

### 🚀 GraphSAGE Implementation (NUEVO)

Se ha implementado GraphSAGE con soporte completo para:

#### 1. **Mini-batch Gradient Descent**
- Entrenamiento con lotes muy pequeños (batch_size: 16-32)
- Uso de `NeighborLoader` de PyTorch Geometric
- Reducción de memoria para grafos grandes

#### 2. **Neighbor Sampling**
- Muestreo de vecinos por capa: `[10, 5]`
- Escalabilidad mejorada para grafos muy grandes
- Entrenamiento eficiente sin cargar todo el grafo en memoria

#### 3. **Múltiples Métodos de Agregación**
- **Mean**: Agregación promedio (similar a GCN)
- **LSTM**: Agregación secuencial con LSTM
- **Pooling**: Max pooling element-wise

#### 4. **Soporte de Clustering**
- Clustering suave con asignaciones aprendibles
- Aprendizaje de estructura jerárquica
- Regularización de entropía

#### 5. **Archivos Nuevos**
- `graphsage_model.py`: Implementación de modelos GraphSAGE
- `train_graphsage_minibatch.py`: Script de entrenamiento con mini-batch
- `test_graphsage.py`: Tests de validación
- `GRAPHSAGE_README.md`: Documentación detallada

#### Uso Rápido

```python
from train_graphsage_minibatch import train_graphsage_minibatch

# Entrenar con mini-batch y neighbor sampling
model = train_graphsage_minibatch(
    aggregator='mean',      # o 'lstm', 'pool'
    num_epochs=100,
    batch_size=32,          # Lotes pequeños
    num_neighbors=[10, 5],  # Muestreo de vecinos
    learning_rate=0.01
)
```

Ver `GRAPHSAGE_README.md` para más detalles.

## Trabajo Futuro

- [x] ~~GraphSAGE con mini-batch training y neighbor sampling~~
- [x] ~~Múltiples métodos de agregación (mean, LSTM, pooling)~~
- [x] ~~Clustering support~~
- [ ] Implementar algoritmo A* modificado para pathfinding
- [ ] Integración directa con Neo4j para datos reales
- [ ] Reinforcement Learning para optimización dinámica de rutas
- [ ] Visualización interactiva de rutas de escape
- [ ] Multi-agent: Coordinación de múltiples ladrones
- [ ] Temporal GNN: Considerar patrones de vigilancia temporal

## Referencias

1. **Graph Convolutional Networks (GCN)**: Kipf & Welling (2016)
2. **Graph Attention Networks (GAT)**: Veličković et al. (2018)
3. **GraphSAGE**: Hamilton et al. "Inductive Representation Learning on Large Graphs" (NeurIPS 2017)
4. **PyTorch Geometric**: Fey & Lenssen (2019)
5. **Generative Adversarial Networks**: Goodfellow et al. (2014)
6. **GraphSAGE Tutorial**: https://mlabonne.github.io/blog/posts/2022-04-06-GraphSAGE.html

## Licencia

Este es un proyecto educacional de demostración de GNN aplicado a grafos.

---

**Desarrollado por**: The Oracle  
**Proyecto**: Minority Report - Robbers Side  
**Framework**: PyTorch Geometric
