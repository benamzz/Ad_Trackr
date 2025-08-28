#!/usr/bin/env python3
"""
Script interactif pour récupérer les données Google Trends
et les stocker EN BRUT dans MongoDB (sans transformation)
VERSION OPTIMISÉE avec gestion intelligente des quotas
"""

import os
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from pymongo import MongoClient

# Configuration des délais et User-Agents
DELAY_MIN = 5  # Délai minimum entre requêtes (secondes)
DELAY_MAX = 12  # Délai maximum entre requêtes (secondes)
MAX_RETRIES = 3  # Nombre maximum de tentatives en cas d'erreur 429

# Rotation des User-Agents pour éviter la détection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_delay():
    """Génère un délai aléatoire pour éviter la détection"""
    return random.uniform(DELAY_MIN, DELAY_MAX)

def get_random_user_agent():
    """Retourne un User-Agent aléatoire"""
    return random.choice(USER_AGENTS)

def create_cache_key(keyword, geo, timeframe):
    """Crée une clé de cache unique pour un mot-clé"""
    cache_string = f"{keyword}_{geo}_{timeframe}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def check_cache_validity(cache_timestamp, max_age_hours=24):
    """Vérifie si le cache est encore valide"""
    if not cache_timestamp:
        return False
    
    cache_time = datetime.fromisoformat(cache_timestamp)
    max_age = timedelta(hours=max_age_hours)
    return datetime.now() - cache_time < max_age

def connect_mongodb():
    """Connexion à MongoDB"""
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:password123@mongodb:27017/ad_trackr?authSource=admin')
        print(f"🔗 Connexion à MongoDB...")
        
        client = MongoClient(mongo_uri)
        db = client.ad_trackr
        
        # Test de connexion
        client.admin.command('ping')
        print("✅ Connexion MongoDB réussie")
        return db
        
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        return None

def get_google_trends_optimized(keyword, geo='FR', timeframe='today 12-m'):
    """Récupère les données Google Trends avec gestion optimisée des quotas"""
    
    # Vérifier le cache d'abord
    cache_key = create_cache_key(keyword, geo, timeframe)
    cached_data = check_cached_data(keyword, geo, timeframe)
    
    if cached_data:
        print(f"✅ Données trouvées en cache (moins de 24h)")
        return cached_data
    
    # Si pas de cache, faire la requête avec retry
    for attempt in range(MAX_RETRIES):
        try:
            print(f"🔍 Tentative {attempt + 1}/{MAX_RETRIES} pour '{keyword}'...")
            
            # Délai intelligent avant la requête
            if attempt > 0:
                delay = get_random_delay() * (attempt + 1)  # Délai progressif
                print(f"⏰ Attente de {delay:.1f} secondes avant nouvelle tentative...")
                time.sleep(delay)
            
            # Initialiser PyTrends avec User-Agent aléatoire
            user_agent = get_random_user_agent()
            pytrends = TrendReq(
                hl='fr', 
                tz=360,
                user_agent=user_agent,
                retries=2,
                backoff_factor=0.1
            )
            
            # Construire la requête
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # Récupérer les données d'intérêt au fil du temps
            interest_over_time = pytrends.interest_over_time()
            
            if interest_over_time.empty:
                print("❌ Aucune donnée trouvée pour ce mot-clé")
                return None
            
            # Convertir en format JSON BRUT
            raw_data = []
            for index, row in interest_over_time.iterrows():
                raw_data.append({
                    'date': index.isoformat(),
                    'value': int(row[keyword])
                })
            
            # Structure BRUTE avec métadonnées de cache
            result = {
                'keyword': keyword,
                'geo': geo,
                'timeframe': timeframe,
                'ingestion_timestamp': datetime.now().isoformat(),
                'raw_data': raw_data,
                'source': 'google_trends_api',
                'cache_key': cache_key,
                'user_agent_used': user_agent,
                'attempt_number': attempt + 1
            }
            
            print(f"✅ Données brutes récupérées: {len(raw_data)} points de données")
            print(f"🔧 User-Agent utilisé: {user_agent[:50]}...")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                print(f"⚠️ Erreur 429 (quota dépassé) - Tentative {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    delay = get_random_delay() * (attempt + 2)  # Délai plus long
                    print(f"⏰ Attente de {delay:.1f} secondes avant nouvelle tentative...")
                    time.sleep(delay)
                else:
                    print("❌ Toutes les tentatives ont échoué. Quota dépassé.")
                    print("💡 Conseils:")
                    print("   • Attendez 2-3 heures")
                    print("   • Utilisez un mot-clé différent")
                    print("   • Vérifiez votre connexion internet")
                    return None
            else:
                print(f"❌ Erreur inattendue: {e}")
                return None
    
    return None

def check_cached_data(keyword, geo, timeframe):
    """Vérifie s'il existe des données en cache valides"""
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:password123@mongodb:27017/ad_trackr?authSource=admin')
        client = MongoClient(mongo_uri)
        db = client.ad_trackr
        
        # Chercher des données récentes pour ce mot-clé
        cache_age_hours = 24
        min_timestamp = datetime.now() - timedelta(hours=cache_age_hours)
        
        cached_doc = db.google_trends_raw.find_one({
            'keyword': keyword,
            'geo': geo,
            'timeframe': timeframe,
            'ingestion_timestamp': {'$gte': min_timestamp.isoformat()}
        })
        
        client.close()
        
        if cached_doc:
            print(f"📋 Données trouvées en cache pour '{keyword}' (moins de {cache_age_hours}h)")
            return cached_doc
        
        return None
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification du cache: {e}")
        return None

def save_raw_to_mongodb(db, raw_data):
    """Sauvegarde les données BRUTES dans MongoDB (sans transformation)"""
    try:
        collection = db.google_trends_raw
        
        # Supprimer les anciennes données pour ce mot-clé (optionnel)
        keyword = raw_data['keyword']
        result_delete = collection.delete_many({'keyword': keyword})
        if result_delete.deleted_count > 0:
            print(f"🗑️ Suppression de {result_delete.deleted_count} anciens enregistrements pour '{keyword}'")
        
        # Insérer les données EXACTEMENT comme reçues (UN seul document)
        result = collection.insert_one(raw_data)
        print(f"✅ Données BRUTES sauvegardées: 1 document inséré (ID: {result.inserted_id})")
        print(f"📦 Structure: keyword, geo, timeframe, raw_data[], ingestion_timestamp")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def display_raw_summary(raw_data):
    """Affiche un résumé des données BRUTES"""
    print("\n" + "="*50)
    print("📈 DONNÉES GOOGLE TRENDS - BRUTES")
    print("="*50)
    print(f"🔍 Mot-clé: {raw_data['keyword']}")
    print(f"🌍 Géographie: {raw_data['geo']}")
    print(f"📅 Période: {raw_data['timeframe']}")
    print(f"📊 Points de données: {len(raw_data['raw_data'])}")
    print(f"📥 Ingestion: {raw_data['ingestion_timestamp'][:19]}")
    
    # Afficher les métadonnées d'optimisation
    if 'attempt_number' in raw_data:
        print(f"🔄 Tentative: {raw_data['attempt_number']}")
    if 'user_agent_used' in raw_data:
        print(f"🔧 User-Agent: {raw_data['user_agent_used'][:30]}...")
    
    # Afficher quelques valeurs d'exemple
    data_points = raw_data['raw_data']
    if data_points:
        print(f"📈 Valeur max: {max(point['value'] for point in data_points)}")
        print(f"📉 Valeur min: {min(point['value'] for point in data_points)}")
        avg_value = sum(point['value'] for point in data_points) / len(data_points)
        print(f"📊 Valeur moyenne: {avg_value:.1f}")
        
        print(f"\n📅 Dernières valeurs (brutes):")
        for point in data_points[-5:]:  # 5 dernières
            date_obj = datetime.fromisoformat(point['date'])
            formatted_date = date_obj.strftime('%d/%m/%Y')
            print(f"   • {formatted_date}: {point['value']}")
    
    print("="*50)

def main():
    """Fonction principale interactive"""
    print("🚀 RÉCUPÉRATION GOOGLE TRENDS - DONNÉES BRUTES")
    print("="*50)
    print("📋 Mode: Stockage BRUT dans MongoDB (sans transformation)")
    print("🔄 Pipeline: API → MongoDB (RAW) → Spark (TRANSFORM) → HDFS (CLEAN)")
    print("⚡ Version: OPTIMISÉE avec gestion intelligente des quotas")
    print("💡 Fonctionnalités: Cache, délais intelligents, rotation User-Agents")
    
    # Connexion MongoDB
    db = connect_mongodb()
    if db is None:
        print("❌ Impossible de continuer sans MongoDB")
        return
    
    try:
        while True:
            print("\n" + "-"*30)
            
            # Demander le mot-clé à l'utilisateur
            keyword = input("🔍 Entrez le mot-clé à rechercher (ou 'quit' pour quitter): ").strip()
            
            if keyword.lower() in ['quit', 'exit', 'q']:
                print("👋 Au revoir!")
                break
            
            if not keyword:
                print("⚠️ Veuillez entrer un mot-clé valide")
                continue
            
            # Délai intelligent avant la requête
            delay = get_random_delay()
            print(f"⏰ Délai intelligent de {delay:.1f} secondes avant requête...")
            time.sleep(delay)
            
            # Récupérer les données Google Trends BRUTES (optimisé)
            raw_trends = get_google_trends_optimized(keyword)
            
            if raw_trends:
                # Afficher le résumé des données brutes
                display_raw_summary(raw_trends)
                
                # Sauvegarder les données BRUTES dans MongoDB
                success_mongo = save_raw_to_mongodb(db, raw_trends)
                
                if success_mongo:
                    print("✅ Données BRUTES disponibles dans MongoDB")
                    print("🚀 Prêtes pour traitement Spark → HDFS")
                
                # Demander si l'utilisateur veut continuer
                continue_search = input("\n🔄 Rechercher un autre mot-clé? (y/n): ").strip().lower()
                if continue_search not in ['y', 'yes', 'o', 'oui']:
                    print("👋 Au revoir!")
                    break
            else:
                print("❌ Échec de la récupération des données")
                
    except KeyboardInterrupt:
        print("\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main() 