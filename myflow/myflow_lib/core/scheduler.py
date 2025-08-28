"""
Module Scheduler - Planificateur pour MyFlow
"""

from typing import List, Optional
from datetime import datetime
from .dag import DAG
from .task import Task, TaskState
from ..utils.logger import Logger


class Scheduler:
    """Planificateur qui orchestre l'exécution des DAGs"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = None  # Sera implémenté plus tard
        self.dags: List[DAG] = []
        self.is_running = False
        self.logger = Logger.get_instance()
    
    def add_dag(self, dag: DAG):
        """Ajouter un DAG au planificateur"""
        if not dag.validate():
            raise ValueError(f"DAG {dag.dag_id} n'est pas valide")
        
        self.dags.append(dag)
        self.logger.info(f"DAG {dag.dag_id} ajouté au planificateur")
    
    def run_dag(self, dag: DAG, parallel: bool = True) -> bool:
        """Exécuter un DAG complet"""
        self.logger.info(f"Début d'exécution du DAG {dag.dag_id}")
        
        if not dag.validate():
            self.logger.error(f"DAG {dag.dag_id} n'est pas valide")
            return False
        
        dag.print_status()
        
        # Exécution simple des tâches
        for task_id in dag.get_execution_order():
            task = dag.tasks[task_id]
            if task.can_run():
                success = task.run()
                if not success:
                    self.logger.error(f"Tâche {task_id} a échoué")
                    return False
        
        return True
    
    def get_dag_status(self, dag_id: str) -> Optional[dict]:
        """Obtenir le statut d'un DAG spécifique"""
        for dag in self.dags:
            if dag.dag_id == dag_id:
                return {
                    "dag_id": dag.dag_id,
                    "description": dag.description,
                    "start_date": dag.start_date,
                    "is_complete": dag.is_complete(),
                    "has_failures": dag.has_failures(),
                    "status_summary": dag.get_status_summary(),
                    "execution_order": dag.get_execution_order()
                }
        return None
