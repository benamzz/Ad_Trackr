#!/usr/bin/env python3
"""
🧪 Test du script Spark MongoDB → HDFS Complet
Exécute le script complet dans le conteneur Spark Master
"""

import subprocess
import logging
import sys
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_spark_etl():
    """Test du script ETL complet dans le conteneur Spark"""
    logger.info("🎯 TEST SCRIPT ETL COMPLET - EXÉCUTION DANS CONTENEUR SPARK")
    logger.info("=" * 60)
    
    try:
        # 1. Vérification des services Docker
        logger.info("🔍 Vérification des services...")
        
        # MongoDB
        mongo_check = subprocess.run(
            "docker exec datalake-mongo mongosh -u admin -p password123 --authenticationDatabase admin --eval 'db.runCommand(\"ping\")' --quiet",
            shell=True, capture_output=True, text=True
        )
        if mongo_check.returncode != 0:
            logger.error("❌ MongoDB non accessible")
            return False
        logger.info("✅ MongoDB accessible")
        
        # HDFS
        hdfs_check = subprocess.run(
            "docker exec datalake-namenode hdfs dfsadmin -report",
            shell=True, capture_output=True, text=True
        )
        if hdfs_check.returncode != 0:
            logger.error("❌ HDFS non accessible")
            return False
        logger.info("✅ HDFS accessible")
        
        # Spark Master
        spark_check = subprocess.run(
            "docker exec datalake-spark-master ps aux | grep -q 'Master'",
            shell=True, capture_output=True, text=True
        )
        if spark_check.returncode != 0:
            logger.error("❌ Spark Master non accessible")
            return False
        logger.info("✅ Spark Master accessible")
        
        # 2. Copie du script dans le conteneur Spark
        logger.info("📁 Copie du script ETL complet dans le conteneur...")
        
        copy_script = subprocess.run(
            "docker cp mongo_to_hdfs_spark_complete.py datalake-spark-master:/spark/",
            shell=True, capture_output=True, text=True
        )
        
        if copy_script.returncode != 0:
            logger.error(f"❌ Erreur copie script: {copy_script.stderr}")
            return False
        logger.info("✅ Script ETL copié dans le conteneur")
        
        # 3. Installation des dépendances dans le conteneur
        logger.info("📦 Vérification/Installation des dépendances...")
        
        # Installation de PyMongo
        install_pymongo = subprocess.run(
            "docker exec datalake-spark-master pip install pymongo",
            shell=True, capture_output=True, text=True
        )
        if install_pymongo.returncode == 0:
            logger.info("✅ PyMongo installé/vérifié")
        else:
            logger.warning(f"⚠️ Avertissement PyMongo: {install_pymongo.stderr}")
        
        # 4. Vérification des données MongoDB
        logger.info("📊 Vérification des données source...")
        count_result = subprocess.run(
            "docker exec datalake-mongo mongosh -u admin -p password123 --authenticationDatabase admin datalake --eval 'db.raw_data.countDocuments()' --quiet",
            shell=True, capture_output=True, text=True
        )
        
        if count_result.returncode == 0:
            try:
                doc_count = int(count_result.stdout.strip())
                logger.info(f"📊 Documents dans MongoDB: {doc_count}")
                if doc_count == 0:
                    logger.warning("⚠️ Aucune donnée dans MongoDB - Le script utilisera des données de démo")
                else:
                    logger.info("✅ Données réelles disponibles dans MongoDB")
            except ValueError:
                logger.warning("⚠️ Impossible de compter les documents MongoDB")
        else:
            logger.warning("⚠️ Erreur accès MongoDB")
        
        # 5. Exécution du script ETL complet dans le conteneur
        logger.info("⚡ LANCEMENT DU SCRIPT ETL COMPLET...")
        logger.info("🎯 Reproduction fidèle du notebook YouTube ETL Pipeline")
        start_time = datetime.now()
        
        spark_execution = subprocess.run(
            "docker exec datalake-spark-master python /spark/mongo_to_hdfs_spark_complete.py",
            shell=True, capture_output=True, text=True, timeout=1800  # 30 minutes timeout
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 6. Analyse des résultats
        if spark_execution.returncode == 0:
            logger.info(f"✅ Script ETL COMPLET terminé en {execution_time:.2f}s")
            logger.info("📄 OUTPUT DU SCRIPT:")
            print("=" * 60)
            print(spark_execution.stdout)
            print("=" * 60)
            
            # Vérification détaillée HDFS
            logger.info("🔍 Vérification détaillée des données HDFS...")
            
            # Liste des répertoires créés
            hdfs_structure = subprocess.run(
                "docker exec datalake-namenode hdfs dfs -ls -R /data/youtube/",
                shell=True, capture_output=True, text=True
            )
            
            if hdfs_structure.returncode == 0:
                logger.info("✅ Structure HDFS complète créée:")
                print(hdfs_structure.stdout)
                
                # Vérification des fichiers Parquet
                logger.info("📊 Vérification des fichiers de données...")
                
                # Données principales
                main_data_check = subprocess.run(
                    "docker exec datalake-namenode hdfs dfs -count /data/youtube/influenceur",
                    shell=True, capture_output=True, text=True
                )
                if main_data_check.returncode == 0:
                    logger.info("✅ Données principales sauvegardées")
                    logger.info(f"📄 {main_data_check.stdout.strip()}")
                
                # Métadonnées
                metadata_check = subprocess.run(
                    "docker exec datalake-namenode hdfs dfs -count /data/youtube/metadata",
                    shell=True, capture_output=True, text=True
                )
                if metadata_check.returncode == 0:
                    logger.info("✅ Métadonnées sauvegardées")
                    logger.info(f"📄 {metadata_check.stdout.strip()}")
                
            else:
                logger.warning("⚠️ Impossible de lister la structure HDFS complète")
            
            # Test de lecture des données sauvegardées
            logger.info("🔍 Test de lecture des données depuis HDFS...")
            read_test = subprocess.run(
                "docker exec datalake-spark-master python -c \"from pyspark.sql import SparkSession; spark = SparkSession.builder.appName('ReadTest').config('spark.hadoop.fs.defaultFS', 'hdfs://datalake-namenode:9000').getOrCreate(); df = spark.read.parquet('/data/youtube/influenceur'); print(f'Lignes lues: {df.count()}'); spark.stop()\"",
                shell=True, capture_output=True, text=True, timeout=120
            )
            
            if read_test.returncode == 0:
                logger.info("✅ Test de lecture HDFS réussi:")
                logger.info(f"📊 {read_test.stdout.strip()}")
            else:
                logger.warning(f"⚠️ Erreur test de lecture: {read_test.stderr}")
            
            return True
            
        else:
            logger.error("❌ Échec du script ETL complet")
            logger.error("📄 ERREUR:")
            print("=" * 60)
            print(spark_execution.stderr)
            print("=" * 60)
            logger.error("📄 OUTPUT PARTIEL:")
            print(spark_execution.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Timeout du script ETL (30 minutes)")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

def main():
    """Point d'entrée principal"""
    success = test_complete_spark_etl()
    
    if success:
        print("\n" + "="*60)
        print("🎉 TEST ETL COMPLET RÉUSSI!")
        print("="*60)
        print("🌐 Interfaces de vérification:")
        print("   • HDFS NameNode: http://localhost:9870")
        print("   • Spark Master: http://localhost:8086")
        print("   • MongoDB Express: http://localhost:8082")
        print("   • Jupyter Lab: http://localhost:8888")
        print("\n📁 Données disponibles dans HDFS:")
        print("   • /data/youtube/influenceur/ (partitionné)")
        print("   • /data/youtube/metadata/")
        print("   • /data/youtube/influenceur/niche_reference/")
        print("   • /data/youtube/influenceur/geo_reference/")
        print("\n✅ Pipeline Data Lakehouse opérationnelle!")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ TEST ETL COMPLET ÉCHOUÉ!")
        print("="*60)
        print("💡 Actions de débogage:")
        print("   1. Vérifiez les logs: docker-compose logs [service]")
        print("   2. Vérifiez l'espace disque: docker system df")
        print("   3. Redémarrez les services: docker-compose restart")
        print("   4. Vérifiez la connectivité réseau des conteneurs")
        sys.exit(1)

if __name__ == "__main__":
    main()
