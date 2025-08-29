"""
Module YouTubeOperator - Opérateur pour l'extraction YouTube
"""

import os
import sys
import subprocess
from typing import Optional, Dict, Any
from .base_operator import BaseOperator


class YouTubeExtractorOperator(BaseOperator):
    """
    Opérateur pour extraire les données YouTube et les envoyer vers MongoDB
    """
    
    def __init__(self, task_id: str, dag_id: str, 
                 youtube_api_key: Optional[str] = None,
                 mongo_uri: Optional[str] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        self.youtube_api_key = youtube_api_key or os.getenv('YOUTUBE_API_KEY')
        
        # Configuration MongoDB adaptée pour Docker
        if mongo_uri is None:
            mongo_host = os.getenv("MONGO_HOST", "mongo")
            mongo_port = os.getenv("MONGO_PORT", "27017")
            mongo_user = os.getenv("MONGO_USER", "admin")
            mongo_password = os.getenv("MONGO_PASSWORD", "password123")
            self.mongo_uri = f'mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/'
        else:
            self.mongo_uri = mongo_uri
        
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY doit être fournie")
    
    def execute(self) -> bool:
        """Exécuter l'extraction YouTube"""
        try:
            self.logger.info("Démarrage de l'extraction YouTube vers MongoDB")
            
            # Chemin vers le script d'extraction
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'youtube_extractor_to_mongo.py')
            
            if not os.path.exists(script_path):
                self.logger.error(f"Script d'extraction non trouvé: {script_path}")
                return False
            
            # Préparation de l'environnement
            env = os.environ.copy()
            env['YOUTUBE_API_KEY'] = self.youtube_api_key
            env['MONGO_URI'] = self.mongo_uri
            
            # Exécution du script
            cmd = [sys.executable, script_path]
            self.logger.info(f"Exécution de la commande: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Extraction YouTube terminée avec succès")
                if result.stdout:
                    self.logger.info(f"Sortie: {result.stdout}")
                return True
            else:
                self.logger.error(f"Erreur lors de l'extraction: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout lors de l'extraction YouTube")
            return False
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de l'extraction: {str(e)}")
            return False


class SparkETLOperator(BaseOperator):
    """
    Opérateur pour l'ETL Spark (MongoDB vers HDFS)
    """
    
    def __init__(self, task_id: str, dag_id: str,
                 spark_master: Optional[str] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        self.spark_master = spark_master or os.getenv('SPARK_MASTER_URL', 'spark://spark-master:7077')
    
    def execute(self) -> bool:
        """Exécuter l'ETL Spark"""
        try:
            self.logger.info("Démarrage de l'ETL Spark (MongoDB vers HDFS)")
            
            # Chemin vers le script ETL
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'run_etl_spark.py')
            
            if not os.path.exists(script_path):
                self.logger.error(f"Script ETL non trouvé: {script_path}")
                return False
            
            # Exécution du script ETL
            cmd = [sys.executable, script_path]
            self.logger.info(f"Exécution de la commande: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("ETL Spark terminé avec succès")
                if result.stdout:
                    self.logger.info(f"Sortie: {result.stdout}")
                return True
            else:
                self.logger.error(f"Erreur lors de l'ETL: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout lors de l'ETL Spark")
            return False
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ETL: {str(e)}")
            return False


class MongoDBHealthCheckOperator(BaseOperator):
    """
    Opérateur pour vérifier la santé de MongoDB
    """
    
    def __init__(self, task_id: str, dag_id: str,
                 mongo_uri: Optional[str] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        # Configuration MongoDB adaptée pour Docker
        if mongo_uri is None:
            mongo_host = os.getenv("MONGO_HOST", "mongo")
            mongo_port = os.getenv("MONGO_PORT", "27017")
            mongo_user = os.getenv("MONGO_USER", "admin")
            mongo_password = os.getenv("MONGO_PASSWORD", "password123")
            self.mongo_uri = f'mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/'
        else:
            self.mongo_uri = mongo_uri
    
    def execute(self) -> bool:
        """Vérifier la connexion MongoDB"""
        try:
            import pymongo
            
            self.logger.info("Vérification de la connexion MongoDB")
            
            client = pymongo.MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            client.server_info()  # Force la connexion
            client.close()
            
            self.logger.info("✅ MongoDB accessible")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ MongoDB non accessible: {str(e)}")
            return False


class HDFSHealthCheckOperator(BaseOperator):
    """
    Opérateur pour vérifier la santé de HDFS
    """
    
    def __init__(self, task_id: str, dag_id: str,
                 hdfs_namenode: Optional[str] = None,
                 **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        
        # Configuration HDFS adaptée pour Docker
        if hdfs_namenode is None:
            hdfs_host = os.getenv("HDFS_HOST", "namenode")
            hdfs_port = os.getenv("HDFS_PORT", "9870")
            self.hdfs_namenode = f'http://{hdfs_host}:{hdfs_port}'
        else:
            # Ensure the URL uses the WebHDFS protocol (http://)
            raw_url = hdfs_namenode
            if raw_url.startswith('hdfs://'):
                self.hdfs_namenode = raw_url.replace('hdfs://', 'http://').replace(':9000', ':9870')
            else:
                self.hdfs_namenode = raw_url
    
    def execute(self) -> bool:
        """Vérifier la connexion HDFS"""
        try:
            from hdfs import InsecureClient
            
            self.logger.info("Vérification de la connexion HDFS")
            
            # Initialiser le client HDFS
            client = InsecureClient(self.hdfs_namenode, user='root')
            
            # Tester la connexion en listant le répertoire racine
            root_files = client.list('/')
            self.logger.info(f"✅ HDFS accessible. Contenu du répertoire racine: {root_files}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la vérification HDFS: {str(e)}")
            return False
