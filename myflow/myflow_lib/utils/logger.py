"""
Module Logger - Utilise le Singleton Pattern
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class Logger:
    """
    Logger singleton pour MyFlow
    Utilise le Singleton Pattern pour garantir une seule instance
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger("myflow")
            self.logger.setLevel(logging.INFO)
            
            # Créer un handler console si pas déjà présent
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            
            Logger._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """Méthode de classe pour obtenir l'instance singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_level(self, level: str):
        """Définir le niveau de log"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    def info(self, message: str, task_id: Optional[str] = None):
        """Log un message d'information"""
        prefix = f"[{task_id}] " if task_id else ""
        self.logger.info(f"{prefix}{message}")
    
    def error(self, message: str, task_id: Optional[str] = None):
        """Log un message d'erreur"""
        prefix = f"[{task_id}] " if task_id else ""
        self.logger.error(f"{prefix}{message}")
    
    def warning(self, message: str, task_id: Optional[str] = None):
        """Log un message d'avertissement"""
        prefix = f"[{task_id}] " if task_id else ""
        self.logger.warning(f"{prefix}{message}")
    
    def debug(self, message: str, task_id: Optional[str] = None):
        """Log un message de debug"""
        prefix = f"[{task_id}] " if task_id else ""
        self.logger.debug(f"{prefix}{message}")
    
    def critical(self, message: str, task_id: Optional[str] = None):
        """Log un message critique"""
        prefix = f"[{task_id}] " if task_id else ""
        self.logger.critical(f"{prefix}{message}")
    
    def add_file_handler(self, filename: str):
        """Ajouter un handler de fichier"""
        file_handler = logging.FileHandler(filename)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Obtenir le logger Python standard"""
        return self.logger
