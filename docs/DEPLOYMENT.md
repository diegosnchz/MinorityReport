# 🚀 Guía de Despliegue - MinorityReport OracleNet

Esta guía te ayudará a desplegar OracleNet con soporte GPU completo.

## 📋 Requisitos Previos

- ✅ Windows 10/11
- ✅ NVIDIA GPU (Quadro K4200 o superior)
- ✅ 8GB+ RAM
- ✅ 10GB espacio en disco

## 🎯 Opción 1: Despliegue Local (RECOMENDADO)

### Instalación Automática

Ejecuta el script de setup que instalará Python 3.11 y todas las dependencias:

```powershell
# En PowerShell (como Administrador)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
cd C:\Users\Techie3\Documents\GitHub\MinorityReport
.\setup_environment.ps1
```

El script hará:
1. ✅ Verificar/instalar Python 3.11
2. ✅ Crear entorno virtual `venv311`
3. ✅ Instalar PyTorch con CUDA 11.8
4. ✅ Instalar PyTorch Geometric con GPU support
5. ✅ Instalar todas las dependencias
6. ✅ Verificar que GPU esté disponible

### Instalación Manual (Alternativa)

Si prefieres instalación paso a paso:

```powershell
# 1. Descargar e instalar Python 3.11
# https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# 2. Crear entorno virtual
py -3.11 -m venv venv311

# 3. Activar entorno
.\venv311\Scripts\Activate.ps1

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar PyTorch con CUDA
python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==0.2.0 --index-url https://download.pytorch.org/whl/cu118

# 6. Instalar PyTorch Geometric
pip install torch-geometric
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.1+cu118.html

# 7. Instalar dependencias del proyecto
pip install neo4j networkx numpy pandas matplotlib seaborn tqdm
```

### Verificar Instalación

```powershell
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

Deberías ver:
```
CUDA: True
GPU: NVIDIA Quadro K4200
```

### Ejecutar OracleNet

```powershell
# Test rápido
python oracle_net.py

# Entrenar modelo
python train_oracle.py

# Entrenar GraphSAGE
python train_graphsage_minibatch.py
```

---

## 🐳 Opción 2: Despliegue con Docker + GPU

### Requisitos Adicionales

1. **Docker Desktop** instalado
2. **NVIDIA Container Toolkit** configurado

### Instalar NVIDIA Container Toolkit

```powershell
# En PowerShell como Administrador

# 1. Instalar WSL2 (si no lo tienes)
wsl --install

# 2. Instalar Docker Desktop
# https://www.docker.com/products/docker-desktop/

# 3. Habilitar GPU support en Docker Desktop
# Settings > Resources > WSL Integration > Enable "Ubuntu"

# 4. En WSL2 Ubuntu:
wsl
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Desplegar con Docker Compose

```powershell
# En PowerShell (directorio del proyecto)

# Construir y levantar servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f oracle-net

# Verificar GPU en container
docker exec oracle-net python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Entrenar modelo en Docker
docker exec oracle-net python train_oracle.py

# Detener servicios
docker-compose down
```

### Acceder a Neo4j Browser

Una vez levantado Docker:
- URL: http://localhost:7474
- Usuario: `neo4j`
- Password: `minorityreport`

---

## 📊 Pruebas de Rendimiento

### Test de GPU vs CPU

```powershell
# Activar entorno
.\venv311\Scripts\Activate.ps1

# Benchmark
python benchmark_protocols.py
```

### Métricas Esperadas (Quadro K4200)

| Configuración | Tiempo (100 epochs) | Speedup |
|---------------|---------------------|---------|
| CPU Only      | ~15-20 min          | 1x      |
| GPU (K4200)   | ~2-4 min            | 5-10x   |

---

## 🔧 Solución de Problemas

### Error: "CUDA not available"

```powershell
# Verificar driver NVIDIA
nvidia-smi

# Si no funciona, reinstalar drivers:
# https://www.nvidia.com/Download/index.aspx
```

### Error: "torch-scatter no encontrado"

```powershell
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.0.1+cu118.html
```

### Error: "Permission Denied" en PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker: GPU no detectada

```bash
# En WSL2
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Si no funciona, reinstalar NVIDIA Container Toolkit
```

---

## 📚 Próximos Pasos

1. ✅ Ejecutar smoke test: `python oracle_net.py`
2. ✅ Entrenar modelo: `python train_oracle.py`
3. ✅ Ver resultados en Neo4j: http://localhost:7474
4. ✅ Explorar notebooks interactivos (si instalaste Jupyter)

---

## 🆘 Soporte

Si encuentras problemas:

1. Verifica logs: `docker-compose logs oracle-net`
2. Revisa configuración GPU: `nvidia-smi`
3. Consulta [README_ORACLE.md](README_ORACLE.md) para detalles del modelo

---

**¡Listo! Ahora tienes OracleNet corriendo con GPU completo.** 🎉
