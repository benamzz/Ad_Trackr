"""
Module SequentialExecutor - Exécution séquentielle des tâches
"""

from typing import List
from ..core.task import Task
from ..utils.logger import Logger


class SequentialExecutor:
    """Exécuteur séquentiel pour les tâches"""
    
    def __init__(self):
        self.logger = Logger.get_instance()
    
    def execute_tasks(self, tasks: List[Task]) -> List[bool]:
        """Exécuter les tâches séquentiellement"""
        results = []
        for task in tasks:
            result = task.run()
            results.append(result)
        return results
