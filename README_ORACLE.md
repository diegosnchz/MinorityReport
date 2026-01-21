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

## Instalación

### 1. Instalar Dependencias

```bash
pip install torch>=2.0.0
pip install torch-geometric>=2.3.0
pip install networkx>=3.0
pip install numpy>=1.24.0
```

Para PyTorch Geometric, puede que necesites instalar dependencias adicionales:

```bash
# Para CUDA 11.8 (verifica tu versión con nvidia-smi)
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cu118.html
```

### 2. Verificar Instalación

```bash
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

## Uso

### Prueba Rápida (Smoke Test)

```bash
python oracle_net.py
```

Esto ejecutará una prueba rápida del modelo con un grafo sintético y mostrará:
- Configuración del dispositivo (GPU/CPU)
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

## Trabajo Futuro

- [ ] Implementar algoritmo A* modificado para pathfinding
- [ ] Integración directa con Neo4j para datos reales
- [ ] Reinforcement Learning para optimización dinámica de rutas
- [ ] Visualización interactiva de rutas de escape
- [ ] Multi-agent: Coordinación de múltiples ladrones
- [ ] Temporal GNN: Considerar patrones de vigilancia temporal

## Referencias

1. **Graph Convolutional Networks (GCN)**: Kipf & Welling (2016)
2. **Graph Attention Networks (GAT)**: Veličković et al. (2018)
3. **PyTorch Geometric**: Fey & Lenssen (2019)
4. **Generative Adversarial Networks**: Goodfellow et al. (2014)

## Licencia

Este es un proyecto educacional de demostración de GNN aplicado a grafos.

---

**Desarrollado por**: The Oracle  
**Proyecto**: Minority Report - Robbers Side  
**Framework**: PyTorch Geometric
