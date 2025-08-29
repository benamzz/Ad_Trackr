#!/usr/bin/env python3
"""
🎬 YouTube Data Extractor vers MongoDB
Pipeline d'extraction de données YouTube avec stockage dans MongoDB
pour traitement ultérieur avec Spark
"""

import requests
import json
from datetime import datetime
import time
import pymongo
from pymongo import MongoClient
import logging
import os
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YouTubeToMongoExtractor:
    def __init__(self, api_key: str, mongo_uri: str = "mongodb://mongo:27017/"):
        """
        Extracteur YouTube vers MongoDB
        
        Args:
            api_key: Clé API YouTube Data v3
            mongo_uri: URI de connexion MongoDB
        """
        self.api_key = api_key
        self.mongo_uri = mongo_uri
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Connexion MongoDB
        try:
            self.mongo_client = MongoClient(mongo_uri)
            self.db = self.mongo_client.datalake
            self.raw_data_collection = self.db.raw_data
            self.api_logs_collection = self.db.api_logs
            logger.info("✅ Connexion MongoDB établie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MongoDB: {e}")
            raise
            
    def log_api_call(self, endpoint: str, status: str, records_count: int = 0, error: Optional[str] = None):
        """Log des appels API"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "endpoint": endpoint,
            "status": status,
            "records_count": records_count,
            "error": error,
            "source": "youtube_api"
        }
        self.api_logs_collection.insert_one(log_entry)
        
    def save_raw_data(self, data: List[Dict], data_type: str, metadata: Optional[Dict] = None):
        """
        Sauvegarde des données brutes dans MongoDB
        
        Args:
            data: Données à sauvegarder
            data_type: Type de données (videos, channels, etc.)
            metadata: Métadonnées additionnelles
        """
        try:
            documents = []
            timestamp = datetime.utcnow()
            
            for item in data:
                doc = {
                    "timestamp": timestamp,
                    "data_type": data_type,
                    "source": "youtube_api",
                    "processed": False,
                    "raw_data": item,
                    "metadata": metadata or {}
                }
                documents.append(doc)
            
            if documents:
                result = self.raw_data_collection.insert_many(documents)
                logger.info(f"✅ {len(result.inserted_ids)} documents {data_type} sauvegardés dans MongoDB")
                return len(result.inserted_ids)
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde MongoDB: {e}")
            raise
            
    def get_top_videos(self, max_results: int = 50, region_code: str = "US") -> List[Dict]:
        """Récupère les vidéos populaires"""
        url = f"{self.base_url}/videos"
        params = {
            'part': 'snippet,statistics,contentDetails',
            'chart': 'mostPopular',
            'maxResults': max_results,
            'regionCode': region_code,
            'key': self.api_key
        }
        
        try:
            logger.info(f"🌍 Récupération TOP {max_results} vidéos ({region_code})...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('items', [])
            
            # Sauvegarde dans MongoDB
            metadata = {
                "extraction_type": "top_videos",
                "region_code": region_code,
                "max_results": max_results
            }
            
            count = self.save_raw_data(videos, "videos", metadata)
            self.log_api_call("videos/mostPopular", "success", count)
            
            logger.info(f"✅ {len(videos)} vidéos sauvegardées dans MongoDB")
            return videos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API YouTube: {e}")
            self.log_api_call("videos/mostPopular", "error", 0, str(e))
            return []
            
    def get_channel_details(self, channel_ids: List[str]) -> List[Dict]:
        """Récupère les détails des chaînes"""
        if not channel_ids:
            return []
            
        url = f"{self.base_url}/channels"
        params = {
            'part': 'snippet,statistics,brandingSettings',
            'id': ','.join(channel_ids[:50]),  # Max 50 IDs par requête
            'key': self.api_key
        }
        
        try:
            logger.info(f"📺 Récupération détails de {len(channel_ids)} chaînes...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            channels = data.get('items', [])
            
            # Sauvegarde dans MongoDB
            metadata = {
                "extraction_type": "channel_details",
                "channel_count": len(channel_ids)
            }
            
            count = self.save_raw_data(channels, "channels", metadata)
            self.log_api_call("channels", "success", count)
            
            logger.info(f"✅ {len(channels)} chaînes sauvegardées dans MongoDB")
            return channels
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API YouTube channels: {e}")
            self.log_api_call("channels", "error", 0, str(e))
            return []
            
    def search_videos_by_keywords(self, keywords: List[str], max_results: int = 25) -> List[Dict]:
        """Recherche de vidéos par mots-clés"""
        all_videos = []
        
        for keyword in keywords:
            url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'q': keyword,
                'type': 'video',
                'maxResults': max_results,
                'order': 'relevance',
                'key': self.api_key
            }
            
            try:
                logger.info(f"🔍 Recherche vidéos pour: '{keyword}'...")
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                videos = data.get('items', [])
                
                # Ajout du mot-clé dans les métadonnées
                for video in videos:
                    video['search_keyword'] = keyword
                
                all_videos.extend(videos)
                
                # Sauvegarde dans MongoDB
                metadata = {
                    "extraction_type": "search_videos",
                    "search_keyword": keyword,
                    "max_results": max_results
                }
                
                count = self.save_raw_data(videos, "search_videos", metadata)
                self.log_api_call("search", "success", count)
                
                logger.info(f"✅ {len(videos)} vidéos trouvées pour '{keyword}'")
                
                # Respect des limites de l'API
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Erreur recherche '{keyword}': {e}")
                self.log_api_call("search", "error", 0, str(e))
                continue
                
        return all_videos
        
    def run_full_extraction(self, 
                          top_videos_count: int = 50,
                          search_keywords: Optional[List[str]] = None,
                          region_codes: List[str] = ["US", "FR"]):
        """
        Lance une extraction complète
        
        Args:
            top_videos_count: Nombre de top vidéos par région
            search_keywords: Liste des mots-clés à rechercher
            region_codes: Codes des régions à analyser
        """
        logger.info("🚀 Début de l'extraction YouTube vers MongoDB")
        
        total_videos = 0
        total_channels = 0
        channel_ids = set()
        
        # 1. Extraction des top vidéos par région
        for region in region_codes:
            videos = self.get_top_videos(top_videos_count, region)
            total_videos += len(videos)
            
            # Collecte des IDs de chaînes
            for video in videos:
                channel_id = video.get('snippet', {}).get('channelId')
                if channel_id:
                    channel_ids.add(channel_id)
                    
        # 2. Recherche par mots-clés
        if search_keywords:
            search_videos = self.search_videos_by_keywords(search_keywords)
            total_videos += len(search_videos)
            
            # Collecte des IDs de chaînes des résultats de recherche
            for video in search_videos:
                channel_id = video.get('snippet', {}).get('channelId')
                if channel_id:
                    channel_ids.add(channel_id)
                    
        # 3. Extraction des détails des chaînes
        if channel_ids:
            channel_list = list(channel_ids)
            # Traitement par chunks de 50 (limite API)
            for i in range(0, len(channel_list), 50):
                chunk = channel_list[i:i+50]
                channels = self.get_channel_details(chunk)
                total_channels += len(channels)
                time.sleep(0.1)  # Respect des limites API
                
        logger.info(f"🎉 Extraction terminée: {total_videos} vidéos, {total_channels} chaînes")
        return {
            "total_videos": total_videos,
            "total_channels": total_channels,
            "timestamp": datetime.utcnow()
        }

def main():
    """Point d'entrée principal"""
    # Configuration
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:password123@mongo:27017/')
    
    if not API_KEY or API_KEY == "AIzaSyDummy_Key_Replace_With_Real_One":
        logger.warning("⚠️ YOUTUBE_API_KEY non définie ou clé de test - Utilisation de données de démonstration")
        insert_demo_data(MONGO_URI)
        return
    
    # Mots-clés de recherche pour l'analyse des influenceurs
    SEARCH_KEYWORDS = [
        "influencer marketing",
        "brand collaboration", 
        "sponsored content",
        "product review",
        "unboxing",
        "lifestyle vlog",
        "tech review",
        "beauty tutorial",
        "gaming highlights",
        "travel vlog"
    ]
    
    try:
        # Initialisation de l'extracteur
        extractor = YouTubeToMongoExtractor(API_KEY, MONGO_URI)
        
        # Lancement de l'extraction
        results = extractor.run_full_extraction(
            top_videos_count=50,
            search_keywords=SEARCH_KEYWORDS,
            region_codes=["US", "FR", "GB", "DE", "JP"]
        )
        
        logger.info(f"✅ Extraction réussie: {results}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction: {e}")
        raise


def insert_demo_data(mongo_uri: str):
    """Insérer des données de démonstration YouTube dans MongoDB"""
    try:
        client = MongoClient(mongo_uri)
        db = client['datalake']
        
        # Nettoyer les anciennes données
        db.youtube_channels.delete_many({})
        db.raw_data.delete_many({"data_type": "channels"})
        
        # Données de démonstration d'influenceurs YouTube
        demo_channels = [
            {
                "channel_id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
                "title": "PewDiePie",
                "description": "Gaming and entertainment content creator",
                "custom_url": "@PewDiePie",
                "published_at": "2010-04-29T10:54:00Z",
                "country": "SE",
                "default_language": "en",
                "subscriber_count": 111000000,
                "view_count": 29000000000,
                "video_count": 4500,
                "keywords": "gaming,entertainment,comedy,reaction,minecraft",
                "topic_categories": "Gaming|Entertainment",
                "topic_ids": "gaming,entertainment",
                "privacy_status": "public",
                "is_linked": True,
                "made_for_kids": False,
                "subscriber_tier": "100M+",
                "extraction_timestamp": datetime.now().isoformat(),
                "source": "demo_data"
            },
            {
                "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
                "title": "MrBeast",
                "description": "Amazing videos, challenges and philanthropy",
                "custom_url": "@MrBeast",
                "published_at": "2012-02-20T00:00:00Z",
                "country": "US",
                "default_language": "en",
                "subscriber_count": 200000000,
                "view_count": 35000000000,
                "video_count": 800,
                "keywords": "challenge,money,entertainment,viral,philanthropy",
                "topic_categories": "Entertainment|Lifestyle",
                "topic_ids": "entertainment,lifestyle",
                "privacy_status": "public",
                "is_linked": True,
                "made_for_kids": False,
                "subscriber_tier": "100M+",
                "extraction_timestamp": datetime.now().isoformat(),
                "source": "demo_data"
            },
            {
                "channel_id": "UCBJycsmduvYEL83R_U4JriQ",
                "title": "Marques Brownlee",
                "description": "Technology reviews and news",
                "custom_url": "@mkbhd",
                "published_at": "2008-03-21T00:00:00Z",
                "country": "US",
                "default_language": "en",
                "subscriber_count": 18000000,
                "view_count": 4000000000,
                "video_count": 1500,
                "keywords": "tech,review,smartphone,car,tesla,apple",
                "topic_categories": "Technology|Science",
                "topic_ids": "technology,science",
                "privacy_status": "public",
                "is_linked": True,
                "made_for_kids": False,
                "subscriber_tier": "10M+",
                "extraction_timestamp": datetime.now().isoformat(),
                "source": "demo_data"
            },
            {
                "channel_id": "UCsooa4yRKGN_zEE8iknghZA",
                "title": "T-Series",
                "description": "Music and Entertainment",
                "custom_url": "@TSeries",
                "published_at": "2006-03-13T00:00:00Z",
                "country": "IN",
                "default_language": "hi",
                "subscriber_count": 245000000,
                "view_count": 240000000000,
                "video_count": 20000,
                "keywords": "music,bollywood,hindi,entertainment",
                "topic_categories": "Music|Entertainment",
                "topic_ids": "music,entertainment",
                "privacy_status": "public",
                "is_linked": True,
                "made_for_kids": False,
                "subscriber_tier": "100M+",
                "extraction_timestamp": datetime.now().isoformat(),
                "source": "demo_data"
            },
            {
                "channel_id": "UCddiUEpeqJcYeBxX1IVBKvQ",
                "title": "Kurzgesagt – In a Nutshell",
                "description": "Science and philosophy videos",
                "custom_url": "@kurzgesagt",
                "published_at": "2013-07-09T00:00:00Z",
                "country": "DE",
                "default_language": "en",
                "subscriber_count": 21000000,
                "view_count": 2500000000,
                "video_count": 180,
                "keywords": "science,education,philosophy,animation",
                "topic_categories": "Education|Science",
                "topic_ids": "education,science",
                "privacy_status": "public",
                "is_linked": True,
                "made_for_kids": False,
                "subscriber_tier": "10M+",
                "extraction_timestamp": datetime.now().isoformat(),
                "source": "demo_data"
            }
        ]
        
        # Insertion dans la collection youtube_channels (format simplifié)
        db.youtube_channels.insert_many(demo_channels)
        
        # Insertion dans raw_data (format MongoDB pipeline)
        raw_documents = []
        timestamp = datetime.now()
        
        for channel in demo_channels:
            doc = {
                "timestamp": timestamp,
                "data_type": "channels",
                "source": "youtube_api_demo",
                "processed": False,
                "raw_data": channel,
                "metadata": {
                    "extraction_type": "demo_data",
                    "total_channels": len(demo_channels)
                }
            }
            raw_documents.append(doc)
        
        db.raw_data.insert_many(raw_documents)
        
        # Mise à jour du statut de traitement
        db.processing_status.insert_one({
            "timestamp": timestamp,
            "status": "extraction_complete",
            "source": "demo_data",
            "records_count": len(demo_channels),
            "data_type": "youtube_channels"
        })
        
        logger.info(f"✅ {len(demo_channels)} chaînes de démonstration insérées dans MongoDB")
        logger.info("📋 Collections créées: youtube_channels, raw_data, processing_status")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'insertion des données de démonstration: {str(e)}")
        raise

if __name__ == "__main__":
    main()
