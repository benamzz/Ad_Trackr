#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour exécution ETL Influenceurs YouTube depuis le conteneur myflow
"""

import os
import logging
import subprocess

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_etl_influenceurs():
    """Exécute le script ETL influenceurs directement depuis le conteneur myflow"""
    
    logger.info("Démarrage ETL Influenceurs YouTube")
    
    try:
        # Vérifier que le script ETL existe
        script_path = "/app/influenceurs_youtube_etl.py"
        if not os.path.exists(script_path):
            logger.error(f"Le script ETL est introuvable: {script_path}")
            return False
        
        # Exécution du script ETL via Spark-submit
        logger.info("Exécution du script ETL via Spark-submit...")
        spark_master_url = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
        
        # Vérifier si nous sommes dans un conteneur Spark ou local
        if os.path.exists("/opt/bitnami/spark/bin/spark-submit"):
            # Dans un conteneur Spark
            exec_cmd = [
                "/opt/bitnami/spark/bin/spark-submit",
                "--master", spark_master_url,
                "--packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1",
                script_path
            ]
        else:
            # Dans le conteneur myflow, utiliser pyspark directement
            logger.info("Exécution directe avec pyspark...")
            exec_cmd = ["python", script_path]
        
        # Exécution avec streaming de la sortie
        result = subprocess.run(exec_cmd, check=True, text=True)
        logger.info("ETL exécuté avec succès")
        return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution du script ETL: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return False

def main():
    """Point d'entrée principal"""
    success = run_etl_influenceurs()
    
    if success:
        logger.info("Pipeline ETL terminée avec succès")
        exit(0)
    else:
        logger.error("Pipeline ETL échouée")
        exit(1)

if __name__ == "__main__":
    main()
