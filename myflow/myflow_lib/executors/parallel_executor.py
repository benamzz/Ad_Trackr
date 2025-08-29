"""
Module ParallelExecutor - Exécution parallèle des tâches
"""

from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core.task import Task
from ..utils.logger import Logger


class ParallelExecutor:
    """Exécuteur parallèle pour les tâches"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.logger = Logger.get_instance()
    
    def execute_tasks(self, tasks: List[Task]) -> List[bool]:
        """Exécuter les tâches en parallèle"""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(task.run): task for task in tasks}
            for future in as_completed(future_to_task):
                result = future.result()
                results.append(result)
        return results
