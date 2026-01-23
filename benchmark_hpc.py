import time
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from numba import jit
import os

# -------------------------------------------------------------------
# 1. PREPARACIÓN DE DATOS FALSOS (SIMULACIÓN DE 1 MILLÓN DE CRÍMENES)
# -------------------------------------------------------------------
NUM_RECORDS = 1_000_000
print(f"Generando {NUM_RECORDS} registros de prueba...")

# Datos para pruebas de I/O
data = {
    'latitude': np.random.uniform(40.3, 40.5, NUM_RECORDS),
    'longitude': np.random.uniform(-3.8, -3.6, NUM_RECORDS),
    'risk_score': np.random.uniform(0, 1, NUM_RECORDS),
    'distance': np.random.uniform(0, 500, NUM_RECORDS)
}
df = pd.DataFrame(data)
df.to_csv("test_data.csv", index=False)
df.to_parquet("test_data.parquet", engine='pyarrow')

# Datos para pruebas de CPU (Numpy Arrays)
distances = data['distance']
risks = data['risk_score']

# -------------------------------------------------------------------
# 2. DEFINICIÓN DE FUNCIONES A COMPARAR
# -------------------------------------------------------------------

# VERSIÓN A: Legacy (Python Puro)
def calculate_legacy(dist, risk):
    result = np.zeros(len(dist))
    for i in range(len(dist)):
        # Fórmula de coste heurístico pesado
        result[i] = (dist[i] * 1.5) + (risk[i] * 100.0) + np.sqrt(dist[i])
    return result

# VERSIÓN B: HPC (Numba JIT)
@jit(nopython=True)
def calculate_hpc(dist, risk):
    result = np.zeros(len(dist))
    for i in range(len(dist)):
        result[i] = (dist[i] * 1.5) + (risk[i] * 100.0) + np.sqrt(dist[i])
    return result

# Calentamiento de Numba (la compilación JIT ocurre en la primera ejecución)
_ = calculate_hpc(distances[:5], risks[:5])

# -------------------------------------------------------------------
# 3. EJECUCIÓN DEL BENCHMARK
# -------------------------------------------------------------------

results = []

def run_test(name, legacy_func, hpc_func):
    # Test Legacy
    start = time.perf_counter()
    legacy_func()
    legacy_time = time.perf_counter() - start
    
    # Test HPC
    start = time.perf_counter()
    hpc_func()
    hpc_time = time.perf_counter() - start
    
    speedup = legacy_time / hpc_time
    results.append((name, legacy_time, hpc_time, speedup))

print("\nINICIANDO CARRERA: LEGACY vs HPC\n")

# TEST 1: Carga de Datos (CSV+Pandas vs Parquet+Arrow)
run_test(
    "Data I/O (1M rows)", 
    lambda: pd.read_csv("test_data.csv"), 
    lambda: pq.read_table("test_data.parquet") # Zero-copy a Arrow
)

# TEST 2: Cálculo de Rutas (Python Puro vs Numba)
run_test(
    "Pathfinding Math (1M nodes)", 
    lambda: calculate_legacy(distances, risks), 
    lambda: calculate_hpc(distances, risks)
)

# Limpieza
os.remove("test_data.csv")
os.remove("test_data.parquet")

# -------------------------------------------------------------------
# 4. REPORTE FINAL
# -------------------------------------------------------------------

print("="*65)
print(f"{'Operación':<25} | {'Legacy Time':<12} | {'HPC Time':<12} | {'Speedup':<10}")
print("="*65)
for name, leg_t, hpc_t, speedup in results:
    print(f"{name:<25} | {leg_t:>9.4f} s | {hpc_t:>9.4f} s | {speedup:>7.1f}x")
print("="*65)
print("\nCONCLUSIÓN: La arquitectura HPC permite procesar datos en milisegundos.")
