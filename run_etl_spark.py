#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour exécution ETL Influenceurs YouTube
Compatible Airflow - Copie et exécution directe
"""

import subprocess
import sys
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_etl_influenceurs():
    """Copie et exécute le script ETL influenceurs"""
    
    logger.info("Démarrage ETL Influenceurs YouTube")
    
    try:
        # 1. Copie du script vers le conteneur Spark
        logger.info("Copie du script ETL vers le conteneur...")
        copy_cmd = [
            "docker", "cp", 
            "influenceurs_youtube_etl.py", 
            "datalake-spark-master:/spark/influenceurs_youtube_etl.py"
        ]
        subprocess.run(copy_cmd, check=True)
        logger.info("Script copié avec succès")
        
        # 2. Exécution du script ETL
        logger.info("Exécution du script ETL...")
        exec_cmd = [
            "docker", "exec", "datalake-spark-master",
            "bash", "-c", "cd /spark && /spark/bin/spark-submit influenceurs_youtube_etl.py"
        ]
        
        # Exécution avec streaming de la sortie
        result = subprocess.run(exec_cmd, check=True)
        logger.info("ETL exécuté avec succès")
        return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur subprocess: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return False

def main():
    """Point d'entrée principal"""
    success = run_etl_influenceurs()
    
    if success:
        logger.info("Pipeline ETL terminée avec succès")
        sys.exit(0)
    else:
        logger.error("Pipeline ETL échouée")
        sys.exit(1)

if __name__ == "__main__":
    main()
