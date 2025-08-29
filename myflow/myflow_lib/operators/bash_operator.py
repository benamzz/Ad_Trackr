"""
Module BashOperator - Opérateur pour exécuter des commandes bash
"""

import subprocess
from typing import Optional, Dict, Any
from .base_operator import BaseOperator


class BashOperator(BaseOperator):
    """
    Opérateur pour exécuter une commande bash
    Utilise le Template Method Pattern hérité de BaseOperator
    """
    
    def __init__(self, task_id: str, dag_id: str, bash_command: str, 
                 env: Optional[Dict[str, str]] = None, cwd: Optional[str] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        self.bash_command = bash_command
        self.env = env or {}
        self.cwd = cwd
        self.output = None
        self.return_code = None
        
        # Configuration spécifique
        self.timeout = kwargs.get('timeout', 300)
        self.shell = kwargs.get('shell', True)
    
    def execute(self) -> bool:
        """Exécuter la commande bash"""
        try:
            # Rendu de la commande avec le contexte
            rendered_command = self.render_template(self.bash_command)
            
            self.logger.info(f"Exécution de la commande: {rendered_command}")
            
            # Préparation de l'environnement
            env = self._prepare_environment()
            
            # Exécution de la commande
            result = subprocess.run(
                rendered_command,
                shell=self.shell,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=self.cwd
            )
            
            # Stockage des résultats
            self.return_code = result.returncode
            self.output = result.stdout
            self.error_output = result.stderr
            
            # Gestion des résultats
            if result.returncode == 0:
                self.logger.info(f"Commande bash exécutée avec succès")
                if result.stdout:
                    self.logger.info(f"Sortie: {result.stdout}")
                return True
            else:
                self.logger.error(f"Commande bash échouée avec le code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Erreurs: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout de la commande bash après {self.timeout} secondes")
            return False
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de l'exécution bash: {str(e)}")
            return False
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Préparer l'environnement pour l'exécution"""
        import os
        env = os.environ.copy()
        env.update(self.env)
        return env
    
    def get_command_info(self) -> Dict[str, Any]:
        """Obtenir les informations sur la commande"""
        return {
            'bash_command': self.bash_command,
            'rendered_command': self.render_template(self.bash_command),
            'env': self.env,
            'cwd': self.cwd,
            'timeout': self.timeout,
            'shell': self.shell,
            'return_code': self.return_code,
            'output': self.output,
            'error_output': getattr(self, 'error_output', None)
        }
