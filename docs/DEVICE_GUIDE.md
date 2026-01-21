# Device Management Guide - GPU/CPU Auto-Detection

## Quick Start

### Check Your Device Configuration
```powershell
# Activar entorno
.\venv311\Scripts\Activate.ps1

# Verificar device
python -c "from device_utils import print_device_info; print_device_info()"
```

### Run Oracle Test
```powershell
python oracle_net.py
```
**Output**: Automáticamente detecta GPU si está disponible, de lo contrario usa CPU.

### Run Training
```powershell
python train_oracle.py
```
**Output**: Training con GPU (2-4 min) o CPU (15-30 min) según hardware.

---

## How It Works

### Auto-Detection Order
1. ✅ Check if CUDA (NVIDIA GPU) is available
2. ✅ Check if MPS (Apple GPU) is available  
3. ✅ Fallback to CPU (always works)

### No Configuration Needed!
El código detecta automáticamente. No necesitas hacer nada especial:

```python
# oracle_net.py - Línea clave
device = get_device()  # Automático ✨

# train_oracle.py - Línea clave
device = get_device()  # Automático ✨
```

---

## Environment Variables

### Force CPU (para debugging)
```powershell
$env:FORCE_CPU = 'true'
python oracle_net.py

# Desactivar
Remove-Item env:FORCE_CPU
```

### Force UTF-8 Output (Windows)
```powershell
$env:PYTHONIOENCODING = 'utf-8'
python oracle_net.py
```

---

## Troubleshooting

### ❓ "CUDA not available" pero tengo GPU
```powershell
# Verificar drivers NVIDIA
nvidia-smi

# Verificar PyTorch
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name())"
```

**Solución**: Instala/actualiza NVIDIA drivers desde [nvidia.com](https://www.nvidia.com/Download/driverDetails.aspx)

### ❓ GPU lenta comparada con CPU
**Posibles causas**:
1. Grafo muy pequeño (overhead de transferencia de datos)
2. GPU memoria limitada (frecuentes transfers CPU-GPU)
3. GPU antigua (compute capability baja)

**Solución**: GPU es ventajosa para grafos grandes (>1000 nodos). Para grafos pequeños (<100 nodos), CPU puede ser más rápido.

### ❓ "Out of Memory" en GPU
```powershell
$env:FORCE_CPU = 'true'
python train_oracle.py  # Usar CPU
```

O reducir batch_size en `train_oracle.py`:
```python
num_graphs_per_epoch = 25  # Reducir de 50 a 25
```

### ❓ Code runs muy lento
```powershell
# Verificar qué device se está usando
python -c "from device_utils import get_device, get_device_info; \
           d = get_device(); \
           print(f'Device: {d}'); \
           print(get_device_info())"

# Si CPU:
# - Upgrade hardware (GPU) para mejor rendimiento
# - O optimizar código (batch_size, num_epochs)
```

---

## Device Functions Reference

### `get_device(force_cpu=False)`
**Purpose**: Get best available device  
**Returns**: `torch.device` object

```python
from device_utils import get_device

# Auto-detect
device = get_device()

# Force CPU
device = get_device(force_cpu=True)
```

### `is_cuda_available()`
**Purpose**: Check if CUDA is available  
**Returns**: Boolean

```python
from device_utils import is_cuda_available

if is_cuda_available():
    print("GPU available!")
else:
    print("Using CPU")
```

### `get_device_info()`
**Purpose**: Get detailed device information  
**Returns**: Dictionary with device metadata

```python
from device_utils import get_device_info

info = get_device_info()
print(f"Device: {info['device_type']}")
print(f"Device Name: {info['device_name']}")
print(f"CUDA Available: {info['cuda_available']}")
```

### `print_device_info()`
**Purpose**: Pretty-print device information  
**Returns**: None (prints to stdout)

```python
from device_utils import print_device_info

print_device_info()
# Output:
# === Device Configuration ===
# Device: cuda (NVIDIA GPU)
# GPU Name: RTX 3090
# ...
```

### `empty_cuda_cache()`
**Purpose**: Free unused GPU memory  
**Returns**: None

```python
from device_utils import empty_cuda_cache

# After training or large inference
empty_cuda_cache()
```

---

## Integration in Your Code

### Simple Case: Auto-detect
```python
from device_utils import get_device
import torch

device = get_device()  # No arguments needed
model = MyModel().to(device)
data = data.to(device)

# Train/Inference
output = model(data)
```

### Advanced Case: With Options
```python
from device_utils import get_device, get_device_info, empty_cuda_cache
import torch

# Get device with options
device = get_device(force_cpu=False)

# Print device info
device_info = get_device_info()
print(f"Using {device_info['device_name']}")

# Create model
model = MyModel().to(device)

# Training loop
for epoch in range(100):
    output = model(data.to(device))
    # ... training code ...
    
# Clean up
empty_cuda_cache()
```

---

## Performance Comparison

### Actual Results from Current System

**System**: Windows 10, Quadro K4200 (4GB), Intel Xeon E5-1620 v3

```
OracleNet Smoke Test (50 nodes, 150 edges):
- Device Detection: ✅ CPU (GPU incompatible)
- Model Parameters: 18,401
- Safety Scores: Calculated and analyzed
- Execution Time: ~500ms

OracleNet Training (200 epochs):
- Device: CPU
- Time: 2.14 minutes
- Final Accuracy: 69.67%
- Best Val Loss: 0.3737
- Status: ✅ SUCCESS
```

---

## Docker Support

### GPU-Enabled Docker (if available)

`Dockerfile` already configured with:
- Base: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04`
- PyTorch with CUDA support

```powershell
# Build
docker build -t oracle-net .

# Run with GPU
docker run --gpus all oracle-net python oracle_net.py

# Run with CPU only
docker run oracle-net python oracle_net.py
```

See `DOCKER_README.md` and `docker-compose.yml` for details.

---

## Summary

✅ **Device auto-detection is built-in**  
✅ **No configuration needed for GPU/CPU**  
✅ **Automatic fallback to CPU if GPU unavailable**  
✅ **All code works on any hardware**  
✅ **GPU makes training 5-10x faster (when available)**

**Your system**: Using CPU (Quadro K4200 not compatible with PyTorch 2.0+ CUDA wheels)  
**Training speed**: ~2.14 minutes for 200 epochs (CPU)  
**Status**: ✅ All systems operational

---

*For more details, see README_ORACLE.md section "Gestión Automática de GPU/CPU"*
