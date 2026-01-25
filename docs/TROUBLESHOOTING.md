# Troubleshooting - Errores Encontrados y Soluciones

## Tabla de Contenidos
1. [Errores de Instalación](#errores-de-instalación)
2. [Errores de Docker y Neo4j](#errores-de-docker-y-neo4j)
3. [Errores de Python y PyTorch](#errores-de-python-y-pytorch)
4. [Errores de Entrenamiento](#errores-de-entrenamiento)
5. [Errores de Datos y Cypher](#errores-de-datos-y-cypher)
6. [Errores de CUDA y GPU](#errores-de-cuda-y-gpu)
7. [Errores de Performance](#errores-de-performance)

---

## Errores de Instalación

### Error 1: "Python no reconocido"
**Síntoma**: `'python' is not recognized as an internal or external command`

**Causa**: Python no está en PATH o no está instalado

**Soluciones**:
```powershell
# Opción 1: Usar python directamente (si instalaste Python 3.11)
python3 --version

# Opción 2: Verificar PATH
echo $env:PATH

# Opción 3: Reinstalar Python con "Add Python to PATH"
# Descargar desde https://www.python.org/downloads/
```

---

### Error 2: "No module named 'requirements.txt'"
**Síntoma**: `pip install -r config/requirements.txt` falla

**Causa**: Archivo requirements.txt no existe o está mal ubicado

**Soluciones**:
```powershell
# Verificar que estás en el directorio correcto
cd "D:\Repositorios Github\MinorityReport"

# Crear requirements.txt si no existe
pip freeze > config/requirements.txt

# O instalar paquetes manualmente
pip install torch==2.0.1 torch-geometric==2.7.0 neo4j pandas numpy
```

---

### Error 3: "ModuleNotFoundError: No module named 'torch'"
**Síntoma**: `ModuleNotFoundError: No module named 'torch'`

**Causa**: 
- PyTorch no instalado
- Virtual environment no activado
- Instalación incompleta

**Soluciones**:
```powershell
# Paso 1: Activar venv311
.\venv311\Scripts\Activate.ps1

# Paso 2: Reinstalar PyTorch
pip install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Paso 3: Verificar
python -c "import torch; print(torch.__version__)"

# Si sigue fallando, recrear venv
deactivate
rmdir venv311 /s /q
python -m venv venv311
.\venv311\Scripts\Activate.ps1
pip install -r config/requirements.txt
```

---

## Errores de Docker y Neo4j

### Error 4: "Docker daemon is not running"
**Síntoma**: 
```
error during connect: This error may indicate the docker daemon is not running
```

**Causa**: Docker Desktop no está ejecutándose

**Soluciones**:
```powershell
# Solución 1: Abrir Docker Desktop (GUI)
# Buscar "Docker Desktop" en Windows y ejecutar

# Solución 2: Iniciar desde línea de comandos (si está instalado como servicio)
Start-Service Docker

# Solución 3: Verificar instalación
docker --version
docker ps
```

---

### Error 5: "Cannot connect to Neo4j on localhost:7687"
**Síntoma**: 
```
Couldn't connect to localhost:7687
Connection to [::1]:7687 closed with incomplete handshake response
```

**Causa**: 
- Neo4j no ha iniciado completamente
- Puerto 7687 no está expuesto
- Neo4j container crashed

**Soluciones**:
```powershell
# Opción 1: Esperar más tiempo (Neo4j tarda 30-60s en iniciar)
Start-Sleep -Seconds 60
docker ps

# Opción 2: Ver logs para errores
docker-compose logs neo4j | Select-Object -Last 50

# Opción 3: Reiniciar Neo4j
docker-compose restart neo4j
Start-Sleep -Seconds 30

# Opción 4: Limpiar e iniciar desde cero
docker-compose down -v
docker-compose up neo4j -d
Start-Sleep -Seconds 60

# Opción 5: Verificar puerto
netstat -an | Select-String "7687"
```

---

### Error 6: "docker-compose command not found"
**Síntoma**: `docker-compose: command not found`

**Causa**: docker-compose no instalado o no en PATH

**Soluciones**:
```powershell
# Opción 1: Usar 'docker compose' (versión más nueva)
docker compose up neo4j -d

# Opción 2: Instalar docker-compose
pip install docker-compose

# Opción 3: Descargar ejecutable desde GitHub
# https://github.com/docker/compose/releases
```

---

### Error 7: "Volume persistently busy or locked"
**Síntoma**: `Error response from daemon: ... device or resource busy`

**Causa**: Volumen Docker en uso, permisos insuficientes

**Soluciones**:
```powershell
# Opción 1: Forzar limpieza
docker-compose down -v --remove-orphans

# Opción 2: Limpiar todo
docker container prune -f
docker volume prune -f

# Opción 3: Ejecutar como administrador (Windows)
# Click derecho en PowerShell > "Run as administrator"
```

---

## Errores de Python y PyTorch

### Error 8: "NumPy compatibility error"
**Síntoma**: 
```
can't convert np.ndarray of type numpy.object_
The only supported types are: float64, float32, float16, complex64, complex128, int64, int32, int16, int8, uint8, and bool.
```

**Causa**: NumPy 2.x incompatible con extensiones precompiladas de PyTorch

**Soluciones**:
```powershell
# Solución: Downgrade NumPy a versión compatible
pip install "numpy<2.0"

# Verificar
python -c "import numpy; print(numpy.__version__)"

# Si sigue fallando, reinstalar torch-scatter
pip uninstall torch-scatter -y
pip install torch-scatter -f https://data.pyg.org/whl/torch_2.0.0+cu118.html
```

---

### Error 9: "ImportError: cannot import name X from Y"
**Síntoma**: `ImportError: cannot import name 'create_graphsage_model' from 'src.models'`

**Causa**: 
- Archivo falta o está mal ubicado
- Python path no configurado correctamente
- Circular import

**Soluciones**:
```powershell
# Opción 1: Agregar proyecto al PYTHONPATH
$env:PYTHONPATH = "D:\Repositorios Github\MinorityReport"

# Opción 2: Verificar que archivos existen
Test-Path "src\models\graphsage_model.py"
Test-Path "src\models\oracle_net.py"
Test-Path "src\utils\neo4j_data_fetcher.py"

# Opción 3: Ejecutar desde directorio raíz del proyecto
cd "D:\Repositorios Github\MinorityReport"
python scripts\train_with_neo4j.py
```

---

### Error 10: "Tensor dimension mismatch"
**Síntoma**: 
```
RuntimeError: The shape of the mask [200] at index 0 does not match the shape of the indexed tensor [746, 1]
```

**Causa**: Shape del tensor output no coincide con máscara de nodos

**Soluciones**:
```python
# Problema típico: Modelo retorna shape incorrecta
# out.shape = [num_edges, 1] en lugar de [num_nodes, num_classes]

# Solución: Verificar forward() del modelo
# Cambiar de edge prediction a node classification
out = model(data.x, data.edge_index)  # Debe ser [num_nodes, num_classes]

# Usar máscara correcta
loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
```

---

## Errores de Entrenamiento

### Error 11: "CUDA out of memory"
**Síntoma**: 
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Causa**: 
- Dataset o batch size demasiado grande
- VRAM insuficiente
- Memory leak en el código

**Soluciones**:
```powershell
# Opción 1: Usar CPU en lugar de GPU
python scripts/train_with_neo4j.py --model crime --device cpu

# Opción 2: Reducir número de ciudadanos
python scripts/seed_neo4j.py --citizens 100  # En lugar de 200

# Opción 3: Reducir tamaño del modelo
# Modificar hidden_channels en script de entrenamiento
model = SimpleGCN(
    in_channels=data.x.shape[1],
    hidden_channels=32,  # Reducir de 64
    out_channels=num_classes
)

# Opción 4: Limpiar CUDA cache
python -c "import torch; torch.cuda.empty_cache()"

# Opción 5: Monitorear uso de VRAM
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits -l 1
```

---

### Error 12: "Training stuck / muy lento"
**Síntoma**: Entrenamiento avanza muy lentamente o se congela

**Causa**: 
- Usando CPU en lugar de GPU (cuando GPU disponible)
- Queries Neo4j ineficientes
- Memory leak

**Soluciones**:
```powershell
# Opción 1: Verificar que CUDA se usa
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Opción 2: Monitorear GPU
nvidia-smi -l 1  # Actualiza cada segundo

# Opción 3: Reducir dataset para pruebas rápidas
python scripts/seed_neo4j.py --citizens 50

# Opción 4: Usar device explícitamente
python scripts/train_with_neo4j.py --model crime --epochs 5 --device cuda
```

---

### Error 13: "Model accuracy muy baja o no mejora"
**Síntoma**: Validación accuracy se queda en 50% o no mejora después de épocas

**Causa**: 
- Dataset desbalanceado
- Features insuficientes
- Learning rate inapropiado
- Arquitectura modelo muy simple

**Soluciones**:
```python
# Opción 1: Aumentar complejidad del modelo
class BetterGCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)  # Agregar capa
        self.conv3 = GCNConv(hidden_channels, out_channels)
    
    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        x = F.relu(self.conv2(x, edge_index))
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv3(x, edge_index)
        return x

# Opción 2: Aumentar datos
python scripts/seed_neo4j.py --citizens 500

# Opción 3: Ajustar learning rate
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)  # Más bajo = aprendizaje lento pero estable

# Opción 4: Agregar más features en seed_neo4j.py
citizen = {
    "id": i,
    "name": f"{nombre} {apellido}",
    "embedding": [random.gauss(0, 0.5) for _ in range(32)],  # Más features
    "crime_count": random.randint(0, 10),
    "arrest_count": random.randint(0, 5),
    # ... más propiedades
}
```

---

## Errores de Datos y Cypher

### Error 14: "Only directed relationships are supported in CREATE"
**Síntoma**: 
```
Neo.ClientError.Statement.SyntaxError: Only directed relationships are supported in CREATE
"CREATE (c1)-[:INTERACTS_WITH]-(c2)"
```

**Causa**: Usar `-` (sin dirección) en CREATE, que no es permitido en Neo4j 5.x

**Solución**:
```cypher
# ❌ INCORRECTO
CREATE (c1)-[:INTERACTS_WITH]-(c2)

# ✅ CORRECTO (usar ->)
CREATE (c1)-[:INTERACTS_WITH]->(c2)
CREATE (c2)-[:INTERACTS_WITH]->(c1)  # Para bidireccional

# ✅ O en MATCH (aquí sí se permite -)
MATCH (c1)-[:INTERACTS_WITH]-(c2) RETURN c1, c2
```

---

### Error 15: "Property not found in database"
**Síntoma**: 
```
WARNING: One of the property names in your query is not available
missing property name is: risk_seed
```

**Causa**: La propiedad no existe en la base de datos con ese nombre exacto

**Soluciones**:
```cypher
# Verificar qué propiedades tiene cada nodo
MATCH (c:Citizen) RETURN DISTINCT keys(c) LIMIT 1

# Usar coalesce para propiedades opcionales
MATCH (c:Citizen)
RETURN c.id, 
       coalesce(c.riskSeed, c.risk_seed, 0.5) as risk_score

# O renombrar propiedades con SET
MATCH (c:Citizen) WHERE c.risk_seed IS NOT NULL SET c.riskSeed = c.risk_seed
```

---

### Error 16: "No data returned from Neo4j"
**Síntoma**: 
```
ERROR: Failed to fetch citizen graph: No citizens found!
```

**Causa**: Base de datos está vacía

**Soluciones**:
```powershell
# Opción 1: Poblar base de datos
python scripts/seed_neo4j.py --citizens 200

# Opción 2: Verificar conexión
python -c "
from src.utils.neo4j_data_fetcher import Neo4jDataFetcher
f = Neo4jDataFetcher()
f.verify_connection()
f.close()
"

# Opción 3: Ver datos en Neo4j Browser
# http://localhost:7474
# MATCH (n) RETURN COUNT(n)
```

---

## Errores de CUDA y GPU

### Error 17: "NVIDIA driver not loaded / CUDA not available"
**Síntoma**: 
```
CUDA is not available even though nvidia-smi works
```

**Causa**: 
- NVIDIA drivers desactualizados
- PyTorch no compilado para la versión CUDA instalada
- Incompatibilidad de versiones

**Soluciones**:
```powershell
# Opción 1: Actualizar drivers NVIDIA
# https://www.nvidia.com/Download/driverDetails.aspx

# Opción 2: Verificar versión CUDA
nvidia-smi
# Buscar "CUDA Version: X.X" en la salida

# Opción 3: Reinstalar PyTorch con la versión correcta
# Para CUDA 11.8
pip uninstall torch -y
pip install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Para CUDA 12.1
pip install torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Opción 4: Verificar CUDA funciona
python -c "
import torch
print('CUDA Available:', torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    z = torch.matmul(x, y)
    print('CUDA Computation: OK')
"
```

---

### Error 18: "NVIDIA GeForce GPU detected but not supported"
**Síntoma**: GPU no se usa aunque nvidia-smi la detecta

**Causa**: GPU muy antigua o sin soporte para CUDA compute capability requerido

**Soluciones**:
```powershell
# Opción 1: Verificar compute capability
python -c "
import torch
if torch.cuda.is_available():
    props = torch.cuda.get_device_properties(0)
    print(f'Compute Capability: {props.major}.{props.minor}')
"

# Opción 2: Usar PyTorch compilado con soporte para GPUs antiguas
# (Esto es avanzado, mejor usar CPU en su lugar)

# Opción 3: Simplemente usar CPU
python scripts/train_with_neo4j.py --model crime --device cpu
```

---

## Errores de Performance

### Error 19: "Script runs but produces poor results"
**Síntoma**: Entrenamiento completa pero accuracy es baja (30-40%)

**Causa**: 
- Dataset muy pequeño
- Clase desbalanceada
- Features no correlacionadas con target

**Análisis**:
```python
# Verificar balance de clases
import torch
from src.utils.neo4j_data_fetcher import Neo4jDataFetcher

fetcher = Neo4jDataFetcher()
data = fetcher.get_pyg_data()

unique, counts = torch.unique(data.y, return_counts=True)
for cls, cnt in zip(unique, counts):
    print(f"Clase {cls}: {cnt} muestras ({100*cnt/len(data.y):.1f}%)")

fetcher.close()
```

**Soluciones**:
- Aumentar dataset: `python scripts/seed_neo4j.py --citizens 1000`
- Mejorar features en script de seed
- Usar data augmentation
- Usar class weights si hay desbalance

---

### Error 20: "Memory leak - RAM usage keeps growing"
**Síntoma**: RAM se llena progresivamente durante entrenamiento

**Causa**: 
- No liberar memoria entre épocas
- Acumular tensores en memoria
- Logging ineficiente

**Soluciones**:
```python
# Agregar en loop de entrenamiento
for epoch in range(num_epochs):
    # ... entrenamiento ...
    
    # Limpiar cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Limpiar variables globales si es necesario
    import gc
    gc.collect()
```

---

## Checklist de Diagnóstico

Si tu problema no está listado, sigue este checklist:

```powershell
# 1. Verificar instalación
python --version
pip list | Select-String "torch|neo4j|pandas"

# 2. Verificar conectividad
docker ps
docker-compose logs neo4j | Select-Object -Last 20

# 3. Verificar base de datos
python -c "from src.utils.neo4j_data_fetcher import Neo4jDataFetcher; f = Neo4jDataFetcher(); print(f.verify_connection()); f.close()"

# 4. Verificar GPU (si aplica)
nvidia-smi

# 5. Run test rápido
python scripts/train_with_neo4j.py --model crime --epochs 5 --device cuda

# Si todo pasa, problema está en configuración específica
```

---

## Contacto y Reporte de Bugs

Si encuentras un error no listado aquí:

1. **Replicar error**: Proporciona pasos exactos
2. **Stack trace completo**: Copia el error completo
3. **Información del sistema**:
   ```powershell
   python --version
   pip list
   nvidia-smi
   docker-compose --version
   ```
4. **Crear issue**: https://github.com/diegosnchz/MinorityReport/issues

---

**Última actualización**: 25 Enero 2026  
**Versión**: 1.0.0  
**Errores documentados**: 20
