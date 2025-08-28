"""
Module HttpOperator - Opérateur pour les requêtes HTTP
"""

import requests
from typing import Optional, Dict, Any, Union
from .base_operator import BaseOperator


class HttpOperator(BaseOperator):
    """
    Opérateur pour effectuer des requêtes HTTP
    Utilise le Template Method Pattern hérité de BaseOperator
    """
    
    def __init__(self, task_id: str, dag_id: str, endpoint: str, 
                 method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                 data: Optional[Union[Dict, str]] = None, params: Optional[Dict] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        self.endpoint = endpoint
        self.method = method.upper()
        self.headers = headers or {}
        self.data = data
        self.params = params or {}
        
        # Configuration spécifique
        self.timeout = kwargs.get('timeout', 30)
        self.verify_ssl = kwargs.get('verify_ssl', True)
        self.expected_status_code = kwargs.get('expected_status_code', 200)
        
        # Résultats
        self.response = None
        self.status_code = None
        self.response_data = None
    
    def execute(self) -> bool:
        """Exécuter la requête HTTP"""
        try:
            # Rendu de l'endpoint avec le contexte
            rendered_endpoint = self.render_template(self.endpoint)
            
            self.logger.info(f"Exécution de la requête {self.method} vers: {rendered_endpoint}")
            
            # Préparation des paramètres
            rendered_headers = self._render_dict(self.headers)
            rendered_data = self._render_data()
            rendered_params = self._render_dict(self.params)
            
            # Exécution de la requête
            response = requests.request(
                method=self.method,
                url=rendered_endpoint,
                headers=rendered_headers,
                data=rendered_data,
                params=rendered_params,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            # Stockage des résultats
            self.response = response
            self.status_code = response.status_code
            
            # Gestion de la réponse
            if response.status_code == self.expected_status_code:
                self.logger.info(f"Requête HTTP réussie (status: {response.status_code})")
                try:
                    self.response_data = response.json()
                except:
                    self.response_data = response.text
                return True
            else:
                self.logger.error(f"Requête HTTP échouée (status: {response.status_code})")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout de la requête HTTP après {self.timeout} secondes")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Erreur de connexion HTTP vers {rendered_endpoint}")
            return False
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la requête HTTP: {str(e)}")
            return False
    
    def _render_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rendre un dictionnaire avec le contexte"""
        rendered = {}
        for key, value in data.items():
            if isinstance(value, str):
                rendered[key] = self.render_template(value)
            else:
                rendered[key] = value
        return rendered
    
    def _render_data(self) -> Optional[Union[Dict, str]]:
        """Rendre les données avec le contexte"""
        if self.data is None:
            return None
        
        if isinstance(self.data, str):
            return self.render_template(self.data)
        elif isinstance(self.data, dict):
            return self._render_dict(self.data)
        else:
            return self.data
    
    def get_http_info(self) -> Dict[str, Any]:
        """Obtenir les informations sur la requête HTTP"""
        return {
            'endpoint': self.endpoint,
            'rendered_endpoint': self.render_template(self.endpoint),
            'method': self.method,
            'headers': self.headers,
            'data': self.data,
            'params': self.params,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl,
            'expected_status_code': self.expected_status_code,
            'status_code': self.status_code,
            'response_data': self.response_data
        }
