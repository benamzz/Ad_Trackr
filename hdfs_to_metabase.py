#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour alimenter Metabase avec les données HDFS via Spark
"""

import sys
import logging
import time
import subprocess
from datetime import datetime

# Configuration des chemins Spark
sys.path.append('/spark/python')
sys.path.append('/spark/python/lib/py4j-0.10.9.5-src.zip')

from pyspark.sql import SparkSession
from pyspark.sql.functions import count, sum as spark_sum, avg, desc, current_timestamp
from pyspark.sql.types import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleHDFSToMetabase:
    def __init__(self):
        self.spark = None
        self.hdfs_path = "hdfs://namenode:9000/data/youtube"
        
        # Configuration PostgreSQL
        self.jdbc_url = "jdbc:postgresql://postgres:5432/metabase"
        self.jdbc_properties = {
            "user": "metabase",
            "password": "metabase123",
            "driver": "org.postgresql.Driver"
        }
    
    def setup_spark(self):
        """Initialise Spark avec PostgreSQL"""
        try:
            # Téléchargement du driver PostgreSQL
            logger.info("📦 Téléchargement du driver PostgreSQL...")
            subprocess.run([
                "wget", "-O", "/spark/jars/postgresql-42.6.0.jar",
                "https://jdbc.postgresql.org/download/postgresql-42.6.0.jar"
            ], check=True, capture_output=True)
            
            self.spark = SparkSession.builder \
                .appName("Simple_HDFS_to_Metabase") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
                .config("spark.jars", "/spark/jars/postgresql-42.6.0.jar") \
                .getOrCreate()
            
            logger.info("✅ Spark configuré avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur configuration Spark: {e}")
            return False
    
    def check_hdfs_data(self):
        """Vérifie la disponibilité des données HDFS"""
        try:
            # Test de lecture des données influenceurs
            df = self.spark.read.parquet(f"{self.hdfs_path}/influenceur")
            count = df.count()
            
            logger.info(f"✅ Données trouvées: {count} influenceurs")
            logger.info("📊 Aperçu des données:")
            df.select("influencer_name", "main_niche", "total_views", "engagement_rate") \
              .show(5, truncate=False)
            
            return True, df
        except Exception as e:
            logger.error(f"❌ Données HDFS non trouvées: {e}")
            return False, None
    
    def transfer_to_postgres(self, df):
        """Transfère les données vers PostgreSQL pour Metabase"""
        try:
            logger.info("🔄 Transfert des données vers PostgreSQL...")
            
            # Nettoyage et enrichissement des données
            df_clean = df.withColumn("import_date", current_timestamp()) \
                        .fillna(0, subset=["total_views", "engagement_rate", "total_videos"])
            
            # Transfer principal
            df_clean.write \
                .mode("overwrite") \
                .option("truncate", "true") \
                .jdbc(self.jdbc_url, "youtube_influencers", properties=self.jdbc_properties)
            
            logger.info("✅ Table 'youtube_influencers' créée")
            
            # Créer des vues analytics
            self._create_analytics_views(df_clean)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur transfert: {e}")
            return False
    
    def _create_analytics_views(self, df):
        """Crée des vues d'analyse pour faciliter l'utilisation dans Metabase"""
        try:
            # Stats par niche
            df_niche = df.groupBy("main_niche") \
                .agg(
                    count("*").alias("nombre_influenceurs"),
                    spark_sum("total_views").alias("total_vues"),
                    avg("engagement_rate").alias("engagement_moyen"),
                    avg("total_videos").alias("nb_videos_moyen")
                ) \
                .withColumn("created_at", current_timestamp())
            
            df_niche.write \
                .mode("overwrite") \
                .jdbc(self.jdbc_url, "analytics_par_niche", properties=self.jdbc_properties)
            
            # Top influenceurs
            df_top = df.orderBy(desc("total_views")) \
                .limit(50) \
                .withColumn("created_at", current_timestamp())
            
            df_top.write \
                .mode("overwrite") \
                .jdbc(self.jdbc_url, "top_influenceurs", properties=self.jdbc_properties)
            
            # Stats par tier d'influence
            df_tier = df.groupBy("influence_tier") \
                .agg(
                    count("*").alias("nombre_influenceurs"),
                    spark_sum("total_views").alias("total_vues"),
                    avg("engagement_rate").alias("engagement_moyen")
                ) \
                .withColumn("created_at", current_timestamp())
            
            df_tier.write \
                .mode("overwrite") \
                .jdbc(self.jdbc_url, "analytics_par_tier", properties=self.jdbc_properties)
            
            logger.info("✅ Vues analytics créées")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur création vues analytics: {e}")
    
    def verify_data(self):
        """Vérifie les données dans PostgreSQL"""
        try:
            # Vérification table principale
            df_check = self.spark.read.jdbc(self.jdbc_url, "youtube_influencers", properties=self.jdbc_properties)
            count = df_check.count()
            
            logger.info(f"✅ Vérification: {count} enregistrements dans PostgreSQL")
            
            # Aperçu des analytics
            df_niche = self.spark.read.jdbc(self.jdbc_url, "analytics_par_niche", properties=self.jdbc_properties)
            logger.info("📈 Statistiques par niche:")
            df_niche.select("main_niche", "nombre_influenceurs", "total_vues") \
                   .orderBy(desc("total_vues")) \
                   .show(10, truncate=False)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    def run(self):
        """Exécute le processus complet"""
        logger.info("🚀 DÉMARRAGE: HDFS → Metabase via Spark")
        logger.info("=" * 50)
        
        # Configuration Spark
        if not self.setup_spark():
            return False
        
        # Attente stabilisation des services
        logger.info("⏳ Attente stabilisation des services (30s)...")
        time.sleep(30)
        
        # Vérification données HDFS
        success, df = self.check_hdfs_data()
        if not success:
            logger.error("❌ Impossible de lire les données HDFS")
            return False
        
        # Transfert vers PostgreSQL
        if not self.transfer_to_postgres(df):
            return False
        
        # Vérification finale
        if not self.verify_data():
            return False
        
        # Informations de connexion
        logger.info("")
        logger.info("🎉 SUCCÈS! Données disponibles dans Metabase")
        logger.info("=" * 50)
        logger.info("📊 TABLES CRÉÉES:")
        logger.info("  • youtube_influencers    - Données principales")
        logger.info("  • analytics_par_niche    - Stats par niche")
        logger.info("  • analytics_par_tier     - Stats par tier")
        logger.info("  • top_influenceurs       - Top 50 influenceurs")
        logger.info("")
        logger.info("🔗 ACCÈS METABASE:")
        logger.info("  • URL: http://localhost:3000")
        logger.info("  • Type: PostgreSQL")
        logger.info("  • Host: postgres")
        logger.info("  • Port: 5432")
        logger.info("  • Database: metabase")
        logger.info("  • User: metabase")
        logger.info("  • Password: metabase123")
        
        self.spark.stop()
        return True

def main():
    """Point d'entrée principal"""
    logger.info("🔧 Initialisation du connecteur HDFS → Metabase")
    
    connector = SimpleHDFSToMetabase()
    success = connector.run()
    
    if success:
        logger.info("✅ Processus terminé avec succès")
        exit(0)
    else:
        logger.error("❌ Processus échoué")
        exit(1)

if __name__ == "__main__":
    main()
