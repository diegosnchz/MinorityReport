# 🔮 OracleNet - Guía de Inicio Rápido

## ¡Bienvenido al lado de los ladrones! 🎭

Esta guía te ayudará a empezar con **OracleNet**, el modelo de IA que calcula rutas de escape óptimas.

---

## 🚀 Inicio Rápido (Docker - Recomendado)

### 1. Levantar todo el sistema

```bash
# Clonar el repositorio
git clone https://github.com/diegosnchz/MinorityReport.git
cd MinorityReport

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f oracle-net
```

### 2. Acceder a Neo4j

Abre tu navegador en: http://localhost:7474

- **Usuario**: `neo4j`
- **Contraseña**: `minorityreport`

### 3. Ver la ciudad de ejemplo

En el Neo4j Browser, ejecuta:

```cypher
// Ver todas las ubicaciones
MATCH (n:Location) RETURN n

// Ver conexiones (calles)
MATCH (a)-[r:CONNECTED_TO]->(b) RETURN a, r, b
```

### 4. Entrenar OracleNet

```bash
# El modelo ya está entrenando automáticamente
# Para ver el progreso:
docker-compose logs -f oracle-net

# O entrena manualmente:
docker-compose exec oracle-net python train_oracle.py
```

---

## 💻 Inicio sin Docker (Local)

### 1. Instalar dependencias

```bash
# Instalar PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar otras dependencias
pip install -r requirements.txt
```

### 2. Smoke test del modelo

```bash
python oracle_net.py
```

Deberías ver:

```
======================================================================
OracleNet - The Oracle: Robber's Escape Route Optimizer
======================================================================

🖥️  Device: cuda  # o cpu

📊 Graph Stats:
   Nodes (intersections): 50
   Edges (streets): 150

✨ OracleNet initialized successfully!
======================================================================
```

### 3. Entrenar el modelo

```bash
python train_oracle.py
```

---

## 🕸️ Gossip vs Mesh: ¿Cuál usar?

### Ejecutar benchmark

```bash
# Con Docker
docker-compose run --rm benchmark

# Sin Docker
python benchmark_protocols.py
```

### Resultados esperados

```
📊 MESH vs GOSSIP - Comparative Analysis
┌─────────────────────┬──────────────────────┬──────────────────────┐
│ Característica      │ Mesh Network         │ Gossip Protocol      │
├─────────────────────┼──────────────────────┼──────────────────────┤
│ Convergencia        │ Rápida (determinista)│ Lenta (probabilística│
│ Escalabilidad       │ Limitada (<1000)     │ Excelente (>10k)     │
└─────────────────────┴──────────────────────┴──────────────────────┘

🎯 RECOMMENDATION FOR MINORITY REPORT:
   ✅ HYBRID APPROACH is recommended
      - Use Mesh for critical zones (downtown, ~50 nodes)
      - Use Gossip for peripheral zones (~200+ nodes)
```

### Cambiar protocolo

Edita `docker-compose.yml`:

```yaml
# Para usar Gossip (por defecto)
gossip-network:
  command: python gossip_protocol.py

# Para usar Mesh
# Descomenta la sección mesh-network
```

---

## 📚 Documentación Completa

- **README_ORACLE.md** - Arquitectura del modelo, matemática de atención
- **DOCKER_README.md** - Deployment, troubleshooting
- **architecture_design.md** - Diseño general del proyecto

---

## 🎯 Casos de Uso

### 1. Calcular ruta de escape

```python
from oracle_net import create_oracle_net
import torch

# Crear modelo
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = create_oracle_net(num_features=16, device=device)

# Cargar modelo entrenado
checkpoint = torch.load('oracle_net_best.pth', map_location=device)
model.load_state_dict(checkpoint['model_state_dict'])

# Preparar grafo de ciudad
x = torch.randn(50, 16, device=device)  # 50 nodos, 16 features
edge_index = torch.randint(0, 50, (2, 150), device=device)  # 150 calles

# Calcular scores de seguridad
model.eval()
with torch.no_grad():
    safety_scores, attention_weights = model(x, edge_index, return_attention=True)

# Las rutas más seguras
top_safe_routes = safety_scores.topk(5)
print(f"Top 5 rutas seguras: {top_safe_routes}")
```

### 2. Integración con Neo4j

```python
from neo4j_oracle_integration import Neo4jOracleIntegration

# Conectar a Neo4j
integration = Neo4jOracleIntegration(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="minorityreport"
)

# Calcular rutas de escape
routes = integration.calculate_escape_routes(
    start_location="Downtown Plaza",
    end_location="Warehouse District",
    top_k=5
)

for i, (path, safety) in enumerate(routes, 1):
    print(f"Ruta {i}: {path} (Safety: {safety:.2%})")
```

### 3. Simulación de red distribuida

```bash
# Gossip Protocol
python gossip_protocol.py

# Mesh Network
python mesh_network.py

# Benchmark
python benchmark_protocols.py
```

---

## 🐛 Troubleshooting

### "CUDA not available"

```bash
# Verifica GPU
nvidia-smi

# Si no tienes GPU, el modelo usa CPU automáticamente
# Es ~5x más lento pero funciona perfectamente
```

### "Connection refused to Neo4j"

```bash
# Asegúrate que Neo4j esté corriendo
docker-compose ps neo4j

# Si no está corriendo
docker-compose up -d neo4j

# Espera ~30 segundos para que inicie
```

### "Module not found: torch_geometric"

```bash
# Instala PyTorch Geometric
pip install torch-geometric

# Si falla, instala dependencias primero
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
```

---

## 📞 Soporte

Si tienes problemas:

1. **Revisa logs**: `docker-compose logs oracle-net`
2. **Verifica servicios**: `docker-compose ps`
3. **Consulta documentación**: README_ORACLE.md, DOCKER_README.md
4. **Issues en GitHub**: Abre un issue en el repositorio

---

## 🎓 Próximos Pasos

Una vez que OracleNet esté funcionando:

1. **Integra con tu frontend** - Los scores están en Neo4j
2. **Ajusta hiperparámetros** - Edita `train_oracle.py`
3. **Agrega más features** - Modifica los features de nodos
4. **Implementa pathfinding** - Usa NetworkX o A*
5. **Multi-agente** - Coordina múltiples ladrones

---

## ⚖️ Hardware Recommendations

### Para Entrenamiento

| Hardware | Training Time (200 epochs) | Recomendado |
|----------|---------------------------|-------------|
| **Quadro K4200 4GB** | ~2-4 min | ✅ Sí |
| CPU Xeon E5-1620 | ~15-20 min | ⚠️ Funcional |
| RTX 3060 12GB | ~1-2 min | ✅ Excelente |
| CPU i7/i9 moderno | ~10-15 min | ✅ Aceptable |

### Para Inferencia

Cualquier hardware moderno funciona bien. Inferencia es muy rápida (<10ms por grafo).

---

## 🏆 Features Implementadas

✅ GCN + GAT modelo híbrido  
✅ Entrenamiento con GPU  
✅ Integración Neo4j  
✅ Docker deployment  
✅ Gossip Protocol  
✅ Mesh Network  
✅ Benchmark comparativo  
✅ Documentación completa  
✅ Type hints en todo el código  
✅ 0 vulnerabilidades de seguridad (CodeQL)  

---

**¡Disfruta calculando rutas de escape! 🏃‍♂️💨**

**The Oracle** 🔮
