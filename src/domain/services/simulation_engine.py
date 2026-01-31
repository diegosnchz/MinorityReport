"""
Service Port: SimulationEngine
Interfaz para motores de simulación de actividad criminal
"""

from abc import ABC, abstractmethod
from typing import Dict


class SimulationEngine(ABC):
    """
    Puerto para el motor de simulación.
    
    Define las operaciones para simular actividad criminal
    y generar visiones/predicciones de forma automática.
    """
    
    @abstractmethod
    async def run_step(self) -> Dict:
        """
        Ejecuta un 'tick' de la simulación.
        Retorna estadísticas del paso ejecutado.
        """
        pass
    
    @abstractmethod
    async def run_batch(self, steps: int) -> Dict:
        """
        Ejecuta múltiples pasos de simulación.
        """
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """
        Reinicia la simulación a estado inicial.
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """
        Verifica si la simulación está actualmente activa.
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas acumuladas de la simulación.
        """
        pass
