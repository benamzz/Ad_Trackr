"""
Module BaseOperator - Classe de base pour tous les opérateurs
"""

from typing import Any, Dict, Optional
from ..core.task import Task
from ..utils.logger import Logger


class BaseOperator(Task):
    """
    Classe de base pour tous les opérateurs
    Hérite de Task et ajoute des fonctionnalités spécifiques aux opérateurs
    """
    
    def __init__(self, task_id: str, dag_id: str, **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        self.logger = Logger.get_instance()
        
        # Configuration spécifique aux opérateurs
        self.operator_type = self.__class__.__name__
        self.parameters = kwargs.get('parameters', {})
        self.resources = kwargs.get('resources', {})
        self.pool = kwargs.get('pool', 'default_pool')
        self.priority_weight = kwargs.get('priority_weight', 1)
        self.weight_rule = kwargs.get('weight_rule', 'downstream')
        
        # Configuration de retry spécifique
        self.retry_exponential_backoff = kwargs.get('retry_exponential_backoff', False)
        self.retry_jitter = kwargs.get('retry_jitter', False)
    
    def pre_execute(self) -> bool:
        """Pré-exécution spécifique aux opérateurs"""
        self.logger.info(f"Pré-exécution de l'opérateur {self.operator_type}: {self.task_id}")
        
        # Vérification des ressources
        if not self._check_resources():
            self.logger.error(f"Ressources insuffisantes pour {self.task_id}")
            return False
        
        return super().pre_execute()
    
    def post_execute(self, success: bool) -> bool:
        """Post-exécution spécifique aux opérateurs"""
        if success:
            self.logger.info(f"Opérateur {self.operator_type} terminé avec succès: {self.task_id}")
        else:
            self.logger.error(f"Opérateur {self.operator_type} échoué: {self.task_id}")
        
        return super().post_execute(success)
    
    def _check_resources(self) -> bool:
        """Vérifier la disponibilité des ressources"""
        # Implémentation basique - peut être étendue
        return True
    
    def get_operator_info(self) -> Dict[str, Any]:
        """Obtenir les informations spécifiques à l'opérateur"""
        base_info = self.get_status_info()
        base_info.update({
            'operator_type': self.operator_type,
            'parameters': self.parameters,
            'resources': self.resources,
            'pool': self.pool,
            'priority_weight': self.priority_weight,
            'weight_rule': self.weight_rule
        })
        return base_info
    
    def render_template(self, template: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Rendre un template avec le contexte
        Implémentation basique - peut être étendue avec Jinja2
        """
        if context is None:
            context = {}
        
        # Ajouter les paramètres de l'opérateur au contexte
        context.update(self.parameters)
        context.update({
            'task_id': self.task_id,
            'dag_id': self.dag_id,
            'operator_type': self.operator_type
        })
        
        # Rendu simple (peut être amélioré avec Jinja2)
        try:
            return template.format(**context)
        except KeyError as e:
            self.logger.warning(f"Variable manquante dans le template: {e}")
            return template
