"""
Module PythonOperator - Opérateur pour exécuter des fonctions Python
"""

from typing import Callable, Any, Optional, Dict
from .base_operator import BaseOperator


class PythonOperator(BaseOperator):
    """
    Opérateur pour exécuter une fonction Python
    Utilise le Template Method Pattern hérité de BaseOperator
    """
    
    def __init__(self, task_id: str, dag_id: str, python_callable: Callable, 
                 *args, **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        self.python_callable = python_callable
        self.args = args
        self.kwargs = kwargs
        
        # Validation
        if not callable(python_callable):
            raise ValueError("python_callable doit être une fonction callable")
    
    def execute(self) -> bool:
        """Exécuter la fonction Python"""
        try:
            self.logger.info(f"Exécution de la fonction {self.python_callable.__name__}")
            
            # Rendu des arguments si nécessaire
            rendered_args = self._render_args()
            rendered_kwargs = self._render_kwargs()
            
            # Exécution de la fonction
            result = self.python_callable(*rendered_args, **rendered_kwargs)
            
            # Stockage du résultat
            self.result = result
            
            self.logger.info(f"Fonction {self.python_callable.__name__} exécutée avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur dans la fonction {self.python_callable.__name__}: {str(e)}")
            return False
    
    def _render_args(self) -> tuple:
        """Rendre les arguments avec le contexte"""
        rendered_args = []
        for arg in self.args:
            if isinstance(arg, str):
                rendered_args.append(self.render_template(arg))
            else:
                rendered_args.append(arg)
        return tuple(rendered_args)
    
    def _render_kwargs(self) -> Dict[str, Any]:
        """Rendre les arguments nommés avec le contexte"""
        rendered_kwargs = {}
        for key, value in self.kwargs.items():
            if isinstance(value, str):
                rendered_kwargs[key] = self.render_template(value)
            else:
                rendered_kwargs[key] = value
        return rendered_kwargs
    
    def get_callable_info(self) -> Dict[str, Any]:
        """Obtenir les informations sur la fonction callable"""
        return {
            'function_name': self.python_callable.__name__,
            'function_module': self.python_callable.__module__,
            'function_doc': self.python_callable.__doc__,
            'args_count': len(self.args),
            'kwargs_count': len(self.kwargs),
            'result': getattr(self, 'result', None)
        }
