"""
Module Config - Configuration centralisée avec validation
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ExecutorConfig:
    """Configuration pour les exécuteurs"""
    max_workers: int = 4
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5


@dataclass
class LoggingConfig:
    """Configuration pour le logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = False
    file_path: str = "myflow.log"
    console_enabled: bool = True


@dataclass
class DAGConfig:
    """Configuration pour les DAGs"""
    default_max_retries: int = 0
    default_retry_delay: int = 1
    validation_enabled: bool = True
    auto_reset_on_failure: bool = False


@dataclass
class Config:
    """
    Configuration centralisée pour MyFlow
    Utilise le pattern de configuration par environnement
    """
    executor: ExecutorConfig = field(default_factory=ExecutorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    dag: DAGConfig = field(default_factory=DAGConfig)
    
    # Configuration spécifique à l'environnement
    environment: str = "development"
    debug: bool = False
    
    def __post_init__(self):
        """Initialisation post-création"""
        self._load_from_environment()
        self._validate_config()
    
    def _load_from_environment(self):
        """Charger la configuration depuis les variables d'environnement"""
        # Configuration de l'exécuteur
        self.executor.max_workers = int(os.getenv('MYFLOW_MAX_WORKERS', self.executor.max_workers))
        self.executor.timeout = int(os.getenv('MYFLOW_TIMEOUT', self.executor.timeout))
        self.executor.retry_attempts = int(os.getenv('MYFLOW_RETRY_ATTEMPTS', self.executor.retry_attempts))
        self.executor.retry_delay = int(os.getenv('MYFLOW_RETRY_DELAY', self.executor.retry_delay))
        
        # Configuration du logging
        self.logging.level = os.getenv('MYFLOW_LOG_LEVEL', self.logging.level)
        self.logging.file_enabled = os.getenv('MYFLOW_LOG_FILE', 'false').lower() == 'true'
        self.logging.file_path = os.getenv('MYFLOW_LOG_FILE_PATH', self.logging.file_path)
        
        # Configuration des DAGs
        self.dag.default_max_retries = int(os.getenv('MYFLOW_DEFAULT_MAX_RETRIES', self.dag.default_max_retries))
        self.dag.default_retry_delay = int(os.getenv('MYFLOW_DEFAULT_RETRY_DELAY', self.dag.default_retry_delay))
        self.dag.validation_enabled = os.getenv('MYFLOW_VALIDATION_ENABLED', 'true').lower() == 'true'
        
        # Configuration générale
        self.environment = os.getenv('MYFLOW_ENVIRONMENT', self.environment)
        self.debug = os.getenv('MYFLOW_DEBUG', 'false').lower() == 'true'
    
    def _validate_config(self):
        """Valider la configuration"""
        if self.executor.max_workers <= 0:
            raise ValueError("max_workers doit être positif")
        
        if self.executor.timeout <= 0:
            raise ValueError("timeout doit être positif")
        
        if self.executor.retry_attempts < 0:
            raise ValueError("retry_attempts ne peut pas être négatif")
        
        if self.dag.default_max_retries < 0:
            raise ValueError("default_max_retries ne peut pas être négatif")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir la configuration en dictionnaire"""
        return {
            'executor': {
                'max_workers': self.executor.max_workers,
                'timeout': self.executor.timeout,
                'retry_attempts': self.executor.retry_attempts,
                'retry_delay': self.executor.retry_delay
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_enabled': self.logging.file_enabled,
                'file_path': self.logging.file_path,
                'console_enabled': self.logging.console_enabled
            },
            'dag': {
                'default_max_retries': self.dag.default_max_retries,
                'default_retry_delay': self.dag.default_retry_delay,
                'validation_enabled': self.dag.validation_enabled,
                'auto_reset_on_failure': self.dag.auto_reset_on_failure
            },
            'environment': self.environment,
            'debug': self.debug
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Créer une configuration depuis un dictionnaire"""
        config = cls()
        
        if 'executor' in config_dict:
            executor_config = config_dict['executor']
            config.executor = ExecutorConfig(**executor_config)
        
        if 'logging' in config_dict:
            logging_config = config_dict['logging']
            config.logging = LoggingConfig(**logging_config)
        
        if 'dag' in config_dict:
            dag_config = config_dict['dag']
            config.dag = DAGConfig(**dag_config)
        
        if 'environment' in config_dict:
            config.environment = config_dict['environment']
        
        if 'debug' in config_dict:
            config.debug = config_dict['debug']
        
        config._validate_config()
        return config


# Instance globale de configuration
config = Config()
