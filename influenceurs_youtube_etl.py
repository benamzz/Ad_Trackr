#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Spark - Analyse des Influenceurs YouTube depuis les données vidéos
Extraction et agrégation des données d'influenceurs à partir des vidéos YouTube
Structure optimisée pour recherche par nom, niche, localisation, etc.
"""

import os
import sys
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pymongo import MongoClient
import logging
import warnings
import json
warnings.filterwarnings('ignore')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeInfluencersETL:
    def __init__(self):
        """Initialisation de la classe ETL"""
        self.spark = None
        self.client = None
        
        # Configuration des chemins HDFS optimisés pour la recherche
        self.HDFS_BASE_PATH = "/data/youtube"
        self.DATA_PATHS = {
            "influenceurs": "/data/youtube/influenceur",  # Table principale des influenceurs
            "metadata": "/data/youtube/metadata",         # Métadonnées techniques
            "niches": "/data/youtube/reference/niches",   # Index des niches
            "geo": "/data/youtube/reference/geo"          # Index géographique
        }

    def init_spark_session(self):
        """Configuration de l'environnement Spark"""
        try:
            logger.info("Configuration de l'environnement Spark...")
            
            self.spark = SparkSession.builder \
                .appName("YouTubeInfluencersFromVideos") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.hadoop.fs.defaultFS", "hdfs://datalake-namenode:9000") \
                .config("spark.mongodb.input.uri", "mongodb://datalake-mongo:27017/datalake.raw_data") \
                .config("spark.mongodb.output.uri", "mongodb://datalake-mongo:27017/datalake.raw_data") \
                .getOrCreate()

            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info("Spark Session initialisée")
            logger.info("Connexion HDFS: " + str(self.spark.conf.get('spark.hadoop.fs.defaultFS')))
            
            return True
            
        except Exception as e:
            logger.error("Erreur initialisation Spark: " + str(e))
            return False

    def test_mongodb_connection(self):
        """Test de connexion MongoDB"""
        try:
            logger.info("Test de connexion MongoDB...")
            
            self.client = MongoClient('mongodb://admin:password123@datalake-mongo:27017/', authSource='admin')
            db = self.client.datalake
            collection = db.raw_data
            
            mongo_count = collection.count_documents({})
            logger.info("MongoDB connecté: " + str(mongo_count) + " documents trouvés")
            
            if mongo_count > 0:
                sample_doc = collection.find_one()
                logger.info("Structure détectée: données de vidéos YouTube")
                return True
            else:
                logger.warning("Aucune donnée dans MongoDB")
                return False
                
        except Exception as e:
            logger.error("Erreur connexion MongoDB: " + str(e))
            return False

    def extract_video_data_from_mongodb(self):
        """Extraction des données vidéos depuis MongoDB"""
        logger.info("Extraction des données vidéos depuis MongoDB...")
        
        try:
            if self.client:
                db = self.client.datalake
                collection = db.raw_data
                
                mongo_docs = list(collection.find({}))
                logger.info(str(len(mongo_docs)) + " documents vidéos récupérés")
                
                if mongo_docs:
                    # Traitement des données vidéos YouTube
                    processed_videos = []
                    
                    for doc in mongo_docs:
                        try:
                            if 'raw_data' in doc and isinstance(doc['raw_data'], dict):
                                raw_data = doc['raw_data']
                                
                                # Extraction des données de la vidéo avec gestion robuste des types
                                video_record = {
                                    '_id': str(doc['_id']),
                                    'timestamp': str(doc.get('timestamp', '')),
                                    'data_type': str(doc.get('data_type', '')),
                                    'source': str(doc.get('source', '')),
                                    'video_id': str(raw_data.get('id', '')),
                                    'kind': str(raw_data.get('kind', '')),
                                    'etag': str(raw_data.get('etag', ''))
                                }
                                
                                # Extraction du snippet (métadonnées de la vidéo)
                                if 'snippet' in raw_data and isinstance(raw_data['snippet'], dict):
                                    snippet = raw_data['snippet']
                                    video_record.update({
                                        'video_title': snippet.get('title', ''),
                                        'video_description': snippet.get('description', ''),
                                        'channel_id': snippet.get('channelId', ''),
                                        'channel_title': snippet.get('channelTitle', ''),
                                        'published_at': snippet.get('publishedAt', ''),
                                        'category_id': snippet.get('categoryId', ''),
                                        'default_language': snippet.get('defaultLanguage', ''),
                                        'default_audio_language': snippet.get('defaultAudioLanguage', ''),
                                        'tags': str(snippet.get('tags', [])),
                                        'live_broadcast_content': snippet.get('liveBroadcastContent', '')
                                    })
                                    
                                    # Extraction des thumbnails
                                    if 'thumbnails' in snippet:
                                        thumbnails = snippet['thumbnails']
                                        if 'high' in thumbnails:
                                            video_record['thumbnail_url'] = thumbnails['high'].get('url', '')
                                
                                # Extraction des statistiques avec gestion sécurisée des types
                                if 'statistics' in raw_data and isinstance(raw_data['statistics'], dict):
                                    stats = raw_data['statistics']
                                    try:
                                        video_record.update({
                                            'view_count': int(str(stats.get('viewCount', 0)).replace(',', '')),
                                            'like_count': int(str(stats.get('likeCount', 0)).replace(',', '')),
                                            'comment_count': int(str(stats.get('commentCount', 0)).replace(',', '')),
                                            'favorite_count': int(str(stats.get('favoriteCount', 0)).replace(',', ''))
                                        })
                                    except (ValueError, TypeError):
                                        video_record.update({
                                            'view_count': 0,
                                            'like_count': 0,
                                            'comment_count': 0,
                                            'favorite_count': 0
                                        })
                                
                                # Extraction des détails de contenu
                                if 'contentDetails' in raw_data and isinstance(raw_data['contentDetails'], dict):
                                    content = raw_data['contentDetails']
                                    video_record.update({
                                        'duration': content.get('duration', ''),
                                        'dimension': content.get('dimension', ''),
                                        'definition': content.get('definition', ''),
                                        'caption': content.get('caption', ''),
                                        'licensed_content': content.get('licensedContent', False)
                                    })
                                
                                # Ajout de métadonnées
                                if 'metadata' in doc and isinstance(doc['metadata'], dict):
                                    metadata = doc['metadata']
                                    video_record.update({
                                        'extraction_method': metadata.get('extraction_method', ''),
                                        'api_version': metadata.get('api_version', ''),
                                        'request_id': metadata.get('request_id', '')
                                    })
                                
                                processed_videos.append(video_record)
                                
                        except Exception as e:
                            logger.warning("Erreur traitement document: " + str(e))
                            continue
                    
                    logger.info(str(len(processed_videos)) + " vidéos traitées avec succès")
                    
                    # Conversion en DataFrame Spark
                    if processed_videos:
                        df_videos = self.spark.createDataFrame(processed_videos)
                        logger.info("DataFrame créé: " + str(df_videos.count()) + " lignes")
                        
                        # Affichage de la structure
                        logger.info("Aperçu des données vidéos:")
                        df_videos.select("video_id", "channel_title", "video_title", "view_count", "like_count").show(5, truncate=False)
                        
                        return df_videos
                    else:
                        raise Exception("Aucune vidéo traitée")
                else:
                    raise Exception("Aucune donnée MongoDB")
            else:
                raise Exception("Client MongoDB non initialisé")
                
        except Exception as e:
            logger.error("Erreur extraction vidéos: " + str(e))
            return None

    def aggregate_influencers_from_videos(self, df_videos):
        """Agrégation des données par influenceur depuis les vidéos"""
        logger.info("Agrégation des données par influenceur...")
        
        try:
            # Nettoyage des données
            df_clean = df_videos.filter(
                (col("channel_id") != "") & 
                (col("channel_title") != "") &
                (col("view_count") >= 0)
            )
            
            logger.info("Données nettoyées: " + str(df_clean.count()) + " vidéos valides")
            
            # Agrégation par chaîne/influenceur
            df_influencers = df_clean.groupBy("channel_id", "channel_title") \
                .agg(
                    # Métriques de base
                    count("video_id").alias("total_videos"),
                    sum("view_count").alias("total_views"),
                    sum("like_count").alias("total_likes"),
                    sum("comment_count").alias("total_comments"),
                    avg("view_count").alias("avg_views_per_video"),
                    avg("like_count").alias("avg_likes_per_video"),
                    
                    # Dernière activité
                    max("published_at").alias("last_video_date"),
                    min("published_at").alias("first_video_date"),
                    
                    # Métadonnées pour recherche
                    collect_set("category_id").alias("video_categories"),
                    collect_set("default_language").alias("languages"),
                    collect_set("tags").alias("all_tags"),
                    
                    # Échantillons de contenu
                    collect_list("video_title").alias("video_titles_sample"),
                    collect_list("video_id").alias("video_ids"),
                    
                    # Qualité du contenu
                    max("view_count").alias("max_views_video"),
                    min("view_count").alias("min_views_video"),
                    avg("comment_count").alias("avg_engagement_rate")
                ) \
                .withColumn("etl_timestamp", current_timestamp()) \
                .withColumn("data_source", lit("youtube_videos_api"))

            # Calcul des métriques dérivées
            df_influencers = df_influencers \
                .withColumn("engagement_rate", 
                           when(col("total_views") > 0, 
                                col("total_likes") / col("total_views") * 100).otherwise(0)) \
                .withColumn("consistency_score",
                           when(col("total_videos") >= 100, 5)
                           .when(col("total_videos") >= 50, 4)
                           .when(col("total_videos") >= 20, 3)
                           .when(col("total_videos") >= 10, 2)
                           .otherwise(1)) \
                .withColumn("influence_tier",
                           when(col("total_views") >= 100000000, "Mega Influencer")
                           .when(col("total_views") >= 10000000, "Macro Influencer")
                           .when(col("total_views") >= 1000000, "Mid-tier Influencer")
                           .when(col("total_views") >= 100000, "Micro Influencer")
                           .otherwise("Nano Influencer"))

            # Extraction et normalisation des niches
            df_influencers = self.extract_niches_from_tags(df_influencers)
            
            logger.info("Influenceurs agrégés: " + str(df_influencers.count()) + " chaînes")
            
            # Aperçu des résultats
            logger.info("Top 5 influenceurs par vues totales:")
            df_influencers.select("channel_title", "total_videos", "total_views", "engagement_rate", "influence_tier") \
                         .orderBy(desc("total_views")) \
                         .show(5, truncate=False)
            
            return df_influencers
            
        except Exception as e:
            logger.error("Erreur agrégation influenceurs: " + str(e))
            return None

    def extract_niches_from_tags(self, df_influencers):
        """Extraction et classification des niches depuis les tags"""
        logger.info("Classification des niches...")
        
        # Dictionnaire de classification des niches
        niche_keywords = {
            "Gaming": ["gaming", "game", "esports", "minecraft", "fortnite", "gamer", "gameplay", "xbox", "playstation", "nintendo"],
            "Music": ["music", "song", "artist", "album", "concert", "musician", "singer", "rap", "rock", "pop"],
            "Tech": ["technology", "tech", "review", "smartphone", "computer", "gadget", "software", "hardware", "coding"],
            "Lifestyle": ["lifestyle", "vlog", "daily", "routine", "fashion", "beauty", "health", "fitness", "travel"],
            "Education": ["education", "tutorial", "learning", "course", "lesson", "how to", "explain", "science"],
            "Entertainment": ["entertainment", "comedy", "funny", "show", "movie", "series", "reaction", "meme"],
            "Sports": ["sports", "football", "basketball", "soccer", "fitness", "workout", "gym", "training"],
            "Food": ["food", "cooking", "recipe", "restaurant", "chef", "cuisine", "baking", "kitchen"],
            "Business": ["business", "entrepreneur", "startup", "finance", "money", "investment", "marketing"],
            "News": ["news", "politics", "current events", "breaking", "report", "journalism", "analysis"]
        }
        
        # UDF pour classifier les niches
        def classify_niche(tags_list):
            if not tags_list:
                return "Other"
            
            # Conversion en string et normalisation
            all_tags = " ".join([str(tag).lower() for tag in tags_list if tag])
            
            # Score par niche
            niche_scores = {}
            for niche, keywords in niche_keywords.items():
                # Comptage des mots-clés trouvés
                score = 0
                for keyword in keywords:
                    if keyword in all_tags:
                        score += 1
                
                if score > 0:
                    niche_scores[niche] = score
            
            # Retourner la niche avec le score le plus élevé
            if niche_scores:
                best_niche = sorted(niche_scores.items(), key=lambda x: x[1], reverse=True)[0][0]
                return best_niche
            else:
                return "Other"
        
        classify_niche_udf = udf(classify_niche, StringType())
        
        # Application de la classification
        df_with_niches = df_influencers.withColumn("main_niche", classify_niche_udf(col("all_tags")))
        
        # Ajout de sous-niches pour recherche avancée
        df_with_niches = df_with_niches \
            .withColumn("searchable_keywords", 
                       concat_ws(" ", col("channel_title"), col("main_niche"), 
                                array_join(col("all_tags"), " "))) \
            .withColumn("content_language", 
                       when(size(col("languages")) > 0, col("languages")[0]).otherwise("unknown"))
        
        logger.info("Classification des niches terminée")
        
        # Statistiques par niche
        niche_stats = df_with_niches.groupBy("main_niche") \
                                   .agg(count("*").alias("influencer_count"),
                                        avg("total_views").alias("avg_total_views")) \
                                   .orderBy(desc("influencer_count"))
        
        logger.info("Répartition par niche:")
        niche_stats.show(10)
        
        return df_with_niches

    def create_search_optimized_tables(self, df_influencers):
        """Création des tables optimisées pour la recherche"""
        logger.info("Création des tables optimisées pour la recherche...")
        
        # Table principale des influenceurs (optimisée pour recherche par nom)
        df_main = df_influencers.select(
            col("channel_id").alias("influencer_id"),
            col("channel_title").alias("influencer_name"),
            col("main_niche"),
            col("influence_tier"),
            col("total_videos"),
            col("total_views"),
            col("total_likes"),
            col("engagement_rate"),
            col("consistency_score"),
            col("avg_views_per_video"),
            col("content_language"),
            col("last_video_date"),
            col("first_video_date"),
            col("searchable_keywords"),
            col("etl_timestamp")
        )
        
        # Table des métadonnées (données techniques et détaillées)
        df_metadata = df_influencers.select(
            col("channel_id").alias("influencer_id"),
            col("channel_title").alias("influencer_name"),
            col("video_categories"),
            col("languages"),
            col("all_tags"),
            col("video_titles_sample"),
            col("video_ids"),
            col("max_views_video"),
            col("min_views_video"),
            col("avg_engagement_rate"),
            col("data_source"),
            col("etl_timestamp").alias("extraction_date")
        )
        
        # Index des niches (pour recherche par catégorie)
        df_niches = df_influencers.groupBy("main_niche") \
                                 .agg(
                                     count("*").alias("total_influencers"),
                                     sum("total_views").alias("total_niche_views"),
                                     avg("engagement_rate").alias("avg_niche_engagement"),
                                     collect_list("channel_title").alias("top_influencers"),
                                     collect_list("channel_id").alias("influencer_ids")
                                 ) \
                                 .withColumn("niche_id", monotonically_increasing_id()) \
                                 .withColumn("created_at", current_timestamp())
        
        # Index géographique (par langue de contenu)
        df_geo = df_influencers.groupBy("content_language", "main_niche") \
                              .agg(
                                  count("*").alias("influencer_count"),
                                  sum("total_views").alias("total_market_reach"),
                                  avg("engagement_rate").alias("avg_engagement"),
                                  collect_list("channel_title").alias("influencers_in_market")
                              ) \
                              .withColumn("geo_market_id", monotonically_increasing_id()) \
                              .withColumn("analysis_date", current_date())
        
        logger.info("Tables optimisées créées")
        
        # Aperçu des tables
        logger.info("Table principale - Top influenceurs:")
        df_main.orderBy(desc("total_views")).show(5, truncate=False)
        
        logger.info("Index des niches:")
        df_niches.orderBy(desc("total_influencers")).show(5, truncate=False)
        
        return df_main, df_metadata, df_niches, df_geo

    def save_to_hdfs_optimized(self, df_main, df_metadata, df_niches, df_geo):
        """Sauvegarde optimisée dans HDFS avec partitioning pour recherche rapide"""
        logger.info("Sauvegarde optimisée dans HDFS...")
        
        try:
            # 1. Table principale des influenceurs (partitionnée par niche et tier)
            logger.info("Sauvegarde table principale des influenceurs...")
            df_main.coalesce(10) \
                   .write \
                   .mode("overwrite") \
                   .partitionBy("main_niche", "influence_tier") \
                   .parquet(self.DATA_PATHS["influenceurs"])
            
            logger.info("Table influenceurs sauvegardée: " + self.DATA_PATHS["influenceurs"])
            
            # 2. Métadonnées détaillées (partitionnées par date d'extraction)
            logger.info("Sauvegarde métadonnées...")
            df_metadata.withColumn("extraction_date", date_format(col("extraction_date"), "yyyy-MM-dd")) \
                       .coalesce(5) \
                       .write \
                       .mode("overwrite") \
                       .partitionBy("extraction_date") \
                       .parquet(self.DATA_PATHS["metadata"])
            
            logger.info("Métadonnées sauvegardées: " + self.DATA_PATHS["metadata"])
            
            # 3. Index des niches
            logger.info("Sauvegarde index des niches...")
            df_niches.coalesce(2) \
                     .write \
                     .mode("overwrite") \
                     .parquet(self.DATA_PATHS["niches"])
            
            logger.info("Index niches sauvegardé: " + self.DATA_PATHS["niches"])
            
            # 4. Index géographique/linguistique
            logger.info("Sauvegarde index géographique...")
            df_geo.coalesce(3) \
                  .write \
                  .mode("overwrite") \
                  .partitionBy("content_language") \
                  .parquet(self.DATA_PATHS["geo"])
            
            logger.info("Index géographique sauvegardé: " + self.DATA_PATHS["geo"])
            
            # Création des vues SQL pour requêtes optimisées
            logger.info("Création des vues SQL...")
            df_main.createOrReplaceTempView("influenceurs_search")
            df_metadata.createOrReplaceTempView("influenceurs_metadata")
            df_niches.createOrReplaceTempView("niches_index")
            df_geo.createOrReplaceTempView("geo_markets")
            
            logger.info("Vues SQL créées pour recherches optimisées")
            
            return True
            
        except Exception as e:
            logger.error("Erreur sauvegarde HDFS: " + str(e))
            return False

    def validate_search_capabilities(self):
        """Validation des capacités de recherche"""
        logger.info("Test des capacités de recherche...")
        
        try:
            # Test 1: Recherche par nom d'influenceur
            logger.info("Test 1: Recherche par nom d'influenceur")
            search_by_name = self.spark.sql("""
                SELECT influencer_name, main_niche, total_views, engagement_rate
                FROM influenceurs_search 
                WHERE LOWER(influencer_name) LIKE '%tech%' 
                ORDER BY total_views DESC 
                LIMIT 5
            """)
            search_by_name.show(truncate=False)
            
            # Test 2: Recherche par niche
            logger.info("Test 2: Top influenceurs Gaming")
            gaming_influencers = self.spark.sql("""
                SELECT influencer_name, total_videos, total_views, engagement_rate
                FROM influenceurs_search 
                WHERE main_niche = 'Gaming' 
                ORDER BY total_views DESC 
                LIMIT 5
            """)
            gaming_influencers.show(truncate=False)
            
            # Test 3: Recherche par niveau d'influence
            logger.info("Test 3: Macro Influencers")
            macro_influencers = self.spark.sql("""
                SELECT influencer_name, main_niche, total_views, influence_tier
                FROM influenceurs_search 
                WHERE influence_tier = 'Macro Influencer'
                ORDER BY engagement_rate DESC 
                LIMIT 5
            """)
            macro_influencers.show(truncate=False)
            
            # Test 4: Statistiques par niche
            logger.info("Test 4: Statistiques par niche")
            niche_stats = self.spark.sql("""
                SELECT main_niche, total_influencers, avg_niche_engagement
                FROM niches_index 
                ORDER BY total_influencers DESC
            """)
            niche_stats.show()
            
            return True
            
        except Exception as e:
            logger.error("Erreur validation recherche: " + str(e))
            return False

    def generate_search_documentation(self):
        """Génération de documentation pour les recherches"""
        logger.info("Génération de la documentation de recherche...")
        
        doc = """
        =======================================================
        DOCUMENTATION - RECHERCHE D'INFLUENCEURS YOUTUBE
        =======================================================
        
        TABLES DISPONIBLES:
        
        1. INFLUENCEURS PRINCIPAUX (/data/youtube/influenceur)
           - Partitionnées par: main_niche, influence_tier
           - Colonnes clés: influencer_name, total_views, engagement_rate
           
        2. MÉTADONNÉES (/data/youtube/metadata)
           - Partitionnées par: extraction_date
           - Contient: tags, catégories, échantillons de vidéos
           
        3. INDEX NICHES (/data/youtube/reference/niches)
           - Statistiques par niche
           - Top influenceurs par catégorie
           
        4. INDEX GÉOGRAPHIQUE (/data/youtube/reference/geo)
           - Partitionné par: content_language
           - Marchés par langue et niche
        
        NOTE: Les données vidéos brutes ne sont PAS sauvegardées 
              pour économiser l'espace de stockage HDFS.
        
        EXEMPLES DE REQUÊTES:
        
        # Recherche par nom:
        SELECT * FROM influenceurs_search 
        WHERE LOWER(IGN) LIKE '%keyword%'
        
        # Recherche par niche:
        SELECT * FROM influenceurs_search 
        WHERE main_niche = 'Gaming'
        
        # Top influenceurs par engagement:
        SELECT * FROM influenceurs_search 
        ORDER BY engagement_rate DESC LIMIT 10
        
        # Recherche par mots-clés:
        SELECT * FROM influenceurs_search 
        WHERE searchable_keywords LIKE '%keyword%'
        """
        
        logger.info(doc)

    def cleanup(self):
        """Nettoyage des ressources"""
        logger.info("Nettoyage des ressources...")
        
        if self.spark:
            self.spark.stop()
            logger.info("Session Spark fermée")
        
        if self.client:
            self.client.close()
            logger.info("Connexion MongoDB fermée")

    def run_full_etl_pipeline(self):
        """Exécution complète de la pipeline ETL optimisée pour les influenceurs"""
        logger.info("DÉMARRAGE DE LA PIPELINE ETL INFLUENCEURS YOUTUBE")
        logger.info("Extraction depuis données vidéos + Optimisation recherche")
        logger.info("============================================================")
        
        start_time = datetime.now()
        
        try:
            # 1. Configuration Spark
            if not self.init_spark_session():
                return False
            
            # 2. Test connexion MongoDB
            if not self.test_mongodb_connection():
                return False
            
            # 3. Extraction des données vidéos
            df_videos = self.extract_video_data_from_mongodb()
            if df_videos is None:
                return False
            
            # 4. Agrégation par influenceur
            df_influencers = self.aggregate_influencers_from_videos(df_videos)
            if df_influencers is None:
                return False
            
            # 5. Création des tables optimisées pour recherche
            df_main, df_metadata, df_niches, df_geo = self.create_search_optimized_tables(df_influencers)
            
            # 6. Sauvegarde optimisée dans HDFS (sans vidéos brutes)
            if not self.save_to_hdfs_optimized(df_main, df_metadata, df_niches, df_geo):
                return False
            
            # 7. Test des capacités de recherche
            if not self.validate_search_capabilities():
                return False
            
            # 8. Documentation
            self.generate_search_documentation()
            
            # Statistiques finales
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            logger.info("============================================================")
            logger.info("PIPELINE ETL INFLUENCEURS TERMINÉE AVEC SUCCÈS!")
            logger.info("Temps d'exécution: " + str(execution_time) + " secondes")
            logger.info("Données sauvegardées dans: " + str(self.HDFS_BASE_PATH))
            logger.info("Structure optimisée pour recherche par:")
            logger.info("  - Nom d'influenceur")
            logger.info("  - Niche de contenu") 
            logger.info("  - Niveau d'influence")
            logger.info("  - Langue de contenu")
            logger.info("  - Mots-clés de contenu")
            logger.info("PRÊT POUR RECHERCHES ET ANALYSES BI!")
            
            return True
            
        except Exception as e:
            logger.error("Erreur dans la pipeline ETL: " + str(e))
            return False
        
        finally:
            self.cleanup()

def main():
    """Point d'entrée principal"""
    etl = YouTubeInfluencersETL()
    success = etl.run_full_etl_pipeline()
    
    if success:
        logger.info("Script terminé avec succès")
        sys.exit(0)
    else:
        logger.error("Script terminé avec des erreurs")
        sys.exit(1)

if __name__ == "__main__":
    main()
