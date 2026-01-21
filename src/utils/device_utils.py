"""
Device Utilities - GPU/CPU Support for MinorityReport

Proporciona funciones para detectar y configurar automáticamente el dispositivo
más eficiente (GPU si está disponible, CPU como fallback).

Soporta:
- NVIDIA CUDA
- Apple Metal Performance Shaders (MPS)
- CPU (fallback universal)
"""

import torch
import os


def get_device(force_cpu: bool = False) -> torch.device:
    """
    Obtiene el mejor dispositivo disponible para entrenamiento.
    Prioriza GPU si está disponible, fallback automático a CPU.
    
    Args:
        force_cpu: Si True, fuerza el uso de CPU incluso si GPU está disponible
    
    Returns:
        torch.device: Dispositivo a usar (cuda, mps, o cpu)
    """
    # Respetar variable de entorno
    if os.environ.get('FORCE_CPU', '').lower() == 'true':
        force_cpu = True
    
    if force_cpu:
        device = torch.device('cpu')
        print(f"[Device] CPU forzado")
        return device
    
    # Prioridad: CUDA > MPS (Apple) > CPU
    if torch.cuda.is_available():
        device = torch.device('cuda')
        try:
            gpu_name = torch.cuda.get_device_name(0)
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9  # type: ignore[misc]
            print(f"[Device] GPU CUDA detectada: {gpu_name} ({total_memory:.2f} GB)")
        except Exception as e:
            print(f"[Device] GPU CUDA detectada (pero hubo error al leer propiedades: {e})")
        return device
    
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():  # type: ignore
        device = torch.device('mps')
        print(f"[Device] Apple Metal Performance Shaders (MPS) disponible")
        return device
    
    else:
        device = torch.device('cpu')
        print(f"[Device] GPU no disponible, usando CPU")
        return device


def is_cuda_available() -> bool:
    """Retorna True si CUDA está disponible y funcional."""
    if not torch.cuda.is_available():
        return False
    try:
        # Verificar que realmente funciona
        _ = torch.zeros(1, device='cuda')  # Test tensor
        return True
    except:
        return False


def get_device_info() -> dict[str, str | bool | float | None]:
    """
    Retorna información detallada sobre el dispositivo disponible.
    
    Returns:
        dict con keys: device, device_name, is_gpu, total_memory (GB), pytorch_version, cuda_version
    """
    device = get_device()
    info: dict[str, str | bool | float | None] = {
        'device': str(device),
        'pytorch_version': torch.__version__,
        'device_name': 'CPU',
        'is_gpu': False,
        'total_memory_gb': None,
        'cuda_version': None,
    }
    
    if device.type == 'cuda':
        info['is_gpu'] = True
        info['device_name'] = torch.cuda.get_device_name(0)  # type: ignore[misc]
        info['total_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / 1e9  # type: ignore[misc]
        info['cuda_version'] = torch.version.cuda
    elif device.type == 'mps':
        info['is_gpu'] = True
        info['device_name'] = 'Apple Metal Performance Shaders'
    
    return info


def print_device_info():
    """Imprime información del dispositivo de forma legible."""
    info = get_device_info()
    print("\n" + "=" * 70)
    print("Device Information")
    print("=" * 70)
    print(f"Device: {info['device']}")
    print(f"Device Name: {info['device_name']}")
    print(f"Is GPU: {info['is_gpu']}")
    if info['total_memory_gb']:
        print(f"Total Memory: {info['total_memory_gb']:.2f} GB")
    if info['cuda_version']:
        print(f"CUDA Version: {info['cuda_version']}")
    print(f"PyTorch Version: {info['pytorch_version']}")
    print("=" * 70 + "\n")


def empty_cuda_cache():
    """Libera memoria caché de CUDA si está disponible."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("[Device] CUDA cache limpiado")


if __name__ == "__main__":
    # Test del módulo
    print_device_info()
    
    # Test de crear un tensor
    device = get_device()
    test_tensor = torch.randn(10, 10, device=device)
    print(f"✓ Test tensor creado en {device}: shape {test_tensor.shape}")
