"""
Module executors de MyFlow - Strategy Pattern pour les exécuteurs
"""

from .sequential_executor import SequentialExecutor
from .parallel_executor import ParallelExecutor

__all__ = ["SequentialExecutor", "ParallelExecutor"]
