"""
Module OperatorFactory - Factory Pattern pour créer des opérateurs
"""

from typing import Dict, Type, Any
from .base_operator import BaseOperator
from .python_operator import PythonOperator
from .bash_operator import BashOperator
from .http_operator import HttpOperator


class OperatorFactory:
    """
    Factory pour créer des opérateurs
    Utilise le Factory Pattern pour la création d'opérateurs
    """
    
    _operators: Dict[str, Type[BaseOperator]] = {
        'python': PythonOperator,
        'bash': BashOperator,
        'http': HttpOperator,
    }
    
    @classmethod
    def create_operator(cls, operator_type: str, task_id: str, dag_id: str, **kwargs) -> BaseOperator:
        """
        Créer un opérateur selon son type
        
        Args:
            operator_type: Type d'opérateur ('python', 'bash', 'http')
            task_id: ID de la tâche
            dag_id: ID du DAG
            **kwargs: Arguments spécifiques à l'opérateur
            
        Returns:
            Instance de l'opérateur
            
        Raises:
            ValueError: Si le type d'opérateur n'est pas supporté
        """
        if operator_type not in cls._operators:
            available_types = ', '.join(cls._operators.keys())
            raise ValueError(f"Type d'opérateur '{operator_type}' non supporté. Types disponibles: {available_types}")
        
        operator_class = cls._operators[operator_type]
        return operator_class(task_id, dag_id, **kwargs)
    
    @classmethod
    def register_operator(cls, operator_type: str, operator_class: Type[BaseOperator]):
        """
        Enregistrer un nouveau type d'opérateur
        
        Args:
            operator_type: Nom du type d'opérateur
            operator_class: Classe de l'opérateur
        """
        if not issubclass(operator_class, BaseOperator):
            raise ValueError("La classe d'opérateur doit hériter de BaseOperator")
        
        cls._operators[operator_type] = operator_class
    
    @classmethod
    def get_available_operators(cls) -> Dict[str, str]:
        """
        Obtenir la liste des opérateurs disponibles
        
        Returns:
            Dictionnaire {type: description}
        """
        return {
            'python': 'Exécute une fonction Python',
            'bash': 'Exécute une commande bash',
            'http': 'Effectue une requête HTTP'
        }
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> BaseOperator:
        """
        Créer un opérateur depuis une configuration
        
        Args:
            config: Configuration de l'opérateur
            
        Returns:
            Instance de l'opérateur
        """
        required_fields = ['type', 'task_id', 'dag_id']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Champ requis manquant: {field}")
        
        operator_type = config.pop('type')
        task_id = config.pop('task_id')
        dag_id = config.pop('dag_id')
        
        return cls.create_operator(operator_type, task_id, dag_id, **config)
