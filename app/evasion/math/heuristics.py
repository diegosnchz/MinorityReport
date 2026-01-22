from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_heuristic_cost(
    distance: float, 
    risk_score: float, 
    agent_fatigue: float, 
    terrain_multiplier: float
) -> float:
    """
    Función de coste heurístico compilada con Numba JIT.
    Evita el overhead de Python en cálculos masivos (ej: A* sobre toda Madrid).
    """
    # Lógica personalizada súper rápida
    score = (distance * terrain_multiplier) + (risk_score * 100.0) + (agent_fatigue * 5.0)
    return score

@jit(nopython=True)
def batch_cost_processing(
    distances: np.ndarray, 
    risks: np.ndarray, 
    fatigues: np.ndarray, 
    multipliers: np.ndarray
) -> np.ndarray:
    """
    Procesamiento por lotes (SIMD) usando Numba.
    Acelera el cálculo de Minority Report que en Pandas sería 100x más lento.
    """
    n = distances.shape[0]
    out = np.empty(n, dtype=np.float64)
    for i in range(n):
        out[i] = (distances[i] * multipliers[i]) + (risks[i] * 100.0) + (fatigues[i] * 5.0)
    return out

# Explicación para el usuario:
# En Pandas puro, `df.apply(lambda x: ...)` es interpretado línea a línea.
# Con Numba, este bucle se traduce a código máquina nativo (LLVM).
