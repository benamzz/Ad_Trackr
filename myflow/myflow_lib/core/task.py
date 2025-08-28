"""
Module Task - Classe abstraite de base pour toutes les tâches
Utilise le Template Method Pattern
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from ..utils.logger import Logger


class TaskState(Enum):
    """États possibles d'une tâche"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class Task(ABC):
    """
    Classe abstraite de base pour toutes les tâches
    Utilise le Template Method Pattern pour définir le flux d'exécution
    """
    
    def __init__(self, task_id: str, dag_id: str, **kwargs):
        self.task_id = task_id
        self.dag_id = dag_id
        self.state = TaskState.PENDING
        self.dependencies: List['Task'] = []
        self.dependents: List['Task'] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.logs: List[str] = []
        self.retry_count = 0
        self.max_retries = kwargs.get('max_retries', 0)
        self.retry_delay = kwargs.get('retry_delay', 1)
        self.logger = Logger.get_instance()
        
        # Configuration spécifique à la tâche
        self.config = kwargs
    
    def add_dependency(self, task: 'Task'):
        """Ajouter une dépendance à cette tâche"""
        if task not in self.dependencies:
            self.dependencies.append(task)
            task.dependents.append(self)
            self.logger.info(f"Dépendance ajoutée: {task.task_id} -> {self.task_id}")
    
    def can_run(self) -> bool:
        """Vérifier si toutes les dépendances sont satisfaites"""
        return all(dep.state == TaskState.SUCCESS for dep in self.dependencies)
    
    def should_skip(self) -> bool:
        """Vérifier si la tâche doit être ignorée"""
        return any(dep.state == TaskState.FAILED for dep in self.dependencies)
    
    def should_retry(self) -> bool:
        """Vérifier si la tâche doit être retentée"""
        return (self.state == TaskState.FAILED and 
                self.retry_count < self.max_retries)
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Méthode abstraite à implémenter par les sous-classes
        Retourne True si succès, False sinon
        """
        pass
    
    def pre_execute(self) -> bool:
        """
        Hook pour les actions avant l'exécution
        Peut être surchargée par les sous-classes
        """
        self.logger.info(f"Pré-exécution de la tâche {self.task_id}")
        return True
    
    def post_execute(self, success: bool) -> bool:
        """
        Hook pour les actions après l'exécution
        Peut être surchargée par les sous-classes
        """
        if success:
            self.logger.info(f"Post-exécution réussie de la tâche {self.task_id}")
        else:
            self.logger.error(f"Post-exécution échouée de la tâche {self.task_id}")
        return True
    
    def run(self) -> bool:
        """
        Template Method - Définit le flux d'exécution standard
        """
        # Vérifications préalables
        if self.should_skip():
            self.state = TaskState.SKIPPED
            self.logger.info(f"Tâche {self.task_id} ignorée (dépendance échouée)")
            return True
        
        if not self.can_run():
            self.logger.warning(f"Tâche {self.task_id} ne peut pas s'exécuter (dépendances non satisfaites)")
            return False
        
        # Boucle de retry
        while True:
            try:
                # Pré-exécution
                if not self.pre_execute():
                    self.state = TaskState.FAILED
                    return False
                
                # Exécution principale
                self.state = TaskState.RUNNING
                self.start_time = datetime.now()
                
                self.logger.info(f"Début d'exécution de la tâche {self.task_id}")
                
                success = self.execute()
                
                # Post-exécution
                self.post_execute(success)
                
                # Gestion du résultat
                if success:
                    self.state = TaskState.SUCCESS
                    self.logger.info(f"Tâche {self.task_id} terminée avec succès")
                else:
                    if self.should_retry():
                        self.retry_count += 1
                        self.state = TaskState.RETRY
                        self.logger.warning(f"Tâche {self.task_id} échouée, retry {self.retry_count}/{self.max_retries}")
                        import time
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.state = TaskState.FAILED
                        self.logger.error(f"Tâche {self.task_id} a échoué définitivement")
                
                self.end_time = datetime.now()
                return success
                
            except Exception as e:
                if self.should_retry():
                    self.retry_count += 1
                    self.state = TaskState.RETRY
                    self.logger.warning(f"Exception dans la tâche {self.task_id}, retry {self.retry_count}/{self.max_retries}: {str(e)}")
                    import time
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.state = TaskState.FAILED
                    self.end_time = datetime.now()
                    self.logger.error(f"Erreur dans la tâche {self.task_id}: {str(e)}")
                    return False
    
    def get_duration(self) -> Optional[float]:
        """Obtenir la durée d'exécution en secondes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def get_status_info(self) -> Dict[str, Any]:
        """Obtenir les informations de statut de la tâche"""
        return {
            "task_id": self.task_id,
            "dag_id": self.dag_id,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": [dep.task_id for dep in self.dependencies],
            "dependents": [dep.task_id for dep in self.dependents]
        }
