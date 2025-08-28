"""
MyFlow - Mini-librairie d'orchestration de workflows
Version simplifiée d'Airflow pour l'apprentissage

Architecture basée sur les design patterns:
- Factory Pattern pour les opérateurs
- Observer Pattern pour les événements
- Strategy Pattern pour les exécuteurs
- Singleton Pattern pour le logger
- Builder Pattern pour les DAGs
"""

from .core.dag import DAG
from .core.task import Task, TaskState
from .core.scheduler import Scheduler
from .operators.python_operator import PythonOperator
from .operators.bash_operator import BashOperator
from .operators.http_operator import HttpOperator
from .executors.sequential_executor import SequentialExecutor
from .executors.parallel_executor import ParallelExecutor
from .utils.logger import Logger
from .utils.config import Config

__version__ = "0.2.0"
__author__ = "MyFlow Team"

__all__ = [
    # Core
    "DAG", "Task", "TaskState", "Scheduler",
    # Operators
    "PythonOperator", "BashOperator", "HttpOperator",
    # Executors
    "SequentialExecutor", "ParallelExecutor",
    # Utils
    "Logger", "Config"
]
