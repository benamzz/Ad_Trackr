"""
Module DAG - Utilise le Builder Pattern pour la construction des DAGs
"""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from .task import Task, TaskState
from ..utils.logger import Logger


class DAGBuilder:
    """
    Builder Pattern pour la construction des DAGs
    Permet une construction fluide et configurable
    """
    
    def __init__(self, dag_id: str):
        self.dag_id = dag_id
        self.description = ""
        self.start_date = datetime.now()
        self.tasks: Dict[str, Task] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.tags: List[str] = []
        self.schedule_interval = None
        self.max_active_runs = 1
        self.catchup = False
    
    def set_description(self, description: str) -> 'DAGBuilder':
        """Définir la description du DAG"""
        self.description = description
        return self
    
    def set_start_date(self, start_date: datetime) -> 'DAGBuilder':
        """Définir la date de début"""
        self.start_date = start_date
        return self
    
    def set_schedule_interval(self, interval: timedelta) -> 'DAGBuilder':
        """Définir l'intervalle de planification"""
        self.schedule_interval = interval
        return self
    
    def set_max_active_runs(self, max_runs: int) -> 'DAGBuilder':
        """Définir le nombre maximum d'exécutions actives"""
        self.max_active_runs = max_runs
        return self
    
    def set_catchup(self, catchup: bool) -> 'DAGBuilder':
        """Définir si le DAG doit rattraper les exécutions manquées"""
        self.catchup = catchup
        return self
    
    def add_tag(self, tag: str) -> 'DAGBuilder':
        """Ajouter un tag au DAG"""
        self.tags.append(tag)
        return self
    
    def add_task(self, task: Task) -> 'DAGBuilder':
        """Ajouter une tâche au DAG"""
        if task.task_id in self.tasks:
            raise ValueError(f"Tâche {task.task_id} existe déjà dans le DAG {self.dag_id}")
        
        self.tasks[task.task_id] = task
        self.task_dependencies[task.task_id] = []
        return self
    
    def add_dependency(self, upstream_task_id: str, downstream_task_id: str) -> 'DAGBuilder':
        """Ajouter une dépendance entre deux tâches"""
        if upstream_task_id not in self.tasks:
            raise ValueError(f"Tâche upstream {upstream_task_id} n'existe pas")
        if downstream_task_id not in self.tasks:
            raise ValueError(f"Tâche downstream {downstream_task_id} n'existe pas")
        
        upstream_task = self.tasks[upstream_task_id]
        downstream_task = self.tasks[downstream_task_id]
        
        downstream_task.add_dependency(upstream_task)
        self.task_dependencies[downstream_task_id].append(upstream_task_id)
        
        return self
    
    def build(self) -> 'DAG':
        """Construire le DAG final"""
        return DAG(
            dag_id=self.dag_id,
            description=self.description,
            start_date=self.start_date,
            tasks=self.tasks,
            task_dependencies=self.task_dependencies,
            tags=self.tags,
            schedule_interval=self.schedule_interval,
            max_active_runs=self.max_active_runs,
            catchup=self.catchup
        )


class DAG:
    """
    Représente un DAG (Directed Acyclic Graph) de tâches
    Utilise le Builder Pattern pour la construction
    """
    
    def __init__(self, dag_id: str, description: str = "", start_date: Optional[datetime] = None,
                 tasks: Optional[Dict[str, Task]] = None, task_dependencies: Optional[Dict[str, List[str]]] = None,
                 tags: Optional[List[str]] = None, schedule_interval: Optional[timedelta] = None,
                 max_active_runs: int = 1, catchup: bool = False):
        self.dag_id = dag_id
        self.description = description
        self.start_date = start_date or datetime.now()
        self.tasks: Dict[str, Task] = tasks or {}
        self.task_dependencies: Dict[str, List[str]] = task_dependencies or {}
        self.tags: List[str] = tags or []
        self.schedule_interval = schedule_interval
        self.max_active_runs = max_active_runs
        self.catchup = catchup
        self.logger = Logger.get_instance()
        
        # Métadonnées
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
    
    @classmethod
    def builder(cls, dag_id: str) -> DAGBuilder:
        """Factory method pour créer un builder de DAG"""
        return DAGBuilder(dag_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """Obtenir les tâches prêtes à être exécutées"""
        ready_tasks = []
        
        for task in self.tasks.values():
            if task.state == TaskState.PENDING and task.can_run():
                ready_tasks.append(task)
        
        return ready_tasks
    
    def get_failed_tasks(self) -> List[Task]:
        """Obtenir les tâches qui ont échoué"""
        return [task for task in self.tasks.values() if task.state == TaskState.FAILED]
    
    def get_successful_tasks(self) -> List[Task]:
        """Obtenir les tâches qui ont réussi"""
        return [task for task in self.tasks.values() if task.state == TaskState.SUCCESS]
    
    def get_retry_tasks(self) -> List[Task]:
        """Obtenir les tâches en retry"""
        return [task for task in self.tasks.values() if task.state == TaskState.RETRY]
    
    def is_complete(self) -> bool:
        """Vérifier si toutes les tâches sont terminées (succès ou échec)"""
        for task in self.tasks.values():
            if task.state in [TaskState.PENDING, TaskState.RUNNING, TaskState.RETRY]:
                return False
        return True
    
    def has_failures(self) -> bool:
        """Vérifier s'il y a des échecs dans le DAG"""
        return len(self.get_failed_tasks()) > 0
    
    def get_execution_order(self) -> List[str]:
        """Obtenir l'ordre d'exécution des tâches (tri topologique)"""
        # Algorithme de tri topologique
        in_degree = {task_id: 0 for task_id in self.tasks.keys()}
        
        # Calculer les degrés entrants
        for task_id, deps in self.task_dependencies.items():
            in_degree[task_id] = len(deps)
        
        # Trouver les tâches sans dépendances
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Réduire les degrés des tâches dépendantes
            for task_id, deps in self.task_dependencies.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return result
    
    def validate(self) -> bool:
        """Valider le DAG (vérifier qu'il n'y a pas de cycles)"""
        try:
            execution_order = self.get_execution_order()
            if len(execution_order) != len(self.tasks):
                self.logger.error("DAG contient des cycles!")
                return False
            
            self.logger.info(f"DAG {self.dag_id} validé avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la validation du DAG: {str(e)}")
            return False
    
    def get_status_summary(self) -> Dict[str, int]:
        """Obtenir un résumé des états des tâches"""
        summary = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "retry": 0
        }
        
        for task in self.tasks.values():
            summary[task.state.value] += 1
        
        return summary
    
    def print_status(self):
        """Afficher le statut du DAG"""
        summary = self.get_status_summary()
        self.logger.info(f"=== Statut du DAG {self.dag_id} ===")
        for state, count in summary.items():
            if count > 0:
                self.logger.info(f"{state.capitalize()}: {count}")
        
        execution_order = self.get_execution_order()
        self.logger.info(f"Ordre d'exécution: {' -> '.join(execution_order)}")
    
    def reset(self):
        """Réinitialiser toutes les tâches du DAG"""
        for task in self.tasks.values():
            task.state = TaskState.PENDING
            task.start_time = None
            task.end_time = None
            task.retry_count = 0
        self.logger.info(f"DAG {self.dag_id} réinitialisé")
    
    def get_metadata(self) -> Dict[str, any]:
        """Obtenir les métadonnées du DAG"""
        return {
            "dag_id": self.dag_id,
            "description": self.description,
            "start_date": self.start_date,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "tags": self.tags,
            "schedule_interval": self.schedule_interval,
            "max_active_runs": self.max_active_runs,
            "catchup": self.catchup,
            "task_count": len(self.tasks),
            "dependency_count": sum(len(deps) for deps in self.task_dependencies.values())
        }
