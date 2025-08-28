#!/usr/bin/env python3
"""
Script SÉCURISÉ pour 30-50 mots-clés YouTube - Anti-429 optimisé
STRATÉGIE: Requêtes séquentielles intelligentes avec gestion adaptative
"""

import os
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from pymongo import MongoClient

# Configuration SÉCURISÉE anti-429
DELAY_MIN = 12  # Délai minimum augmenté
DELAY_MAX = 20  # Délai maximum augmenté
DELAY_AFTER_ERROR = 60  # 1 minute après erreur 429
MAX_RETRIES = 5  # Plus de tentatives
BATCH_PAUSE_EVERY = 10  # Pause longue tous les 10 mots-clés
BATCH_PAUSE_DURATION = 120  # 2 minutes de pause

# Pool User-Agents étendu pour rotation maximale
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0'
]

# Géolocalisations
AVAILABLE_GEOS = {
    'FR': 'France', 'US': 'États-Unis', 'GB': 'Royaume-Uni', 'DE': 'Allemagne',
    'ES': 'Espagne', 'IT': 'Italie', 'CA': 'Canada', 'AU': 'Australie',
    'JP': 'Japon', 'BR': 'Brésil', 'IN': 'Inde', 'CN': 'Chine', '': 'Mondial'
}

# Catégories YouTube prédéfinies
YOUTUBE_CATEGORIES = {
    'gaming': ['gaming', 'esport', 'minecraft', 'fortnite', 'valorant', 'league of legends'],
    'beauty': ['makeup', 'skincare', 'beauty haul', 'cosmetics', 'tutorial makeup', 'beauté'],
    'tech': ['tech review', 'smartphone', 'laptop', 'AI', 'technologie', 'innovation'],
    'fitness': ['fitness', 'workout', 'sport', 'musculation', 'yoga', 'running'],
    'food': ['recette', 'cooking', 'food', 'cuisine', 'chef', 'gastronomie'],
    'music': ['music', 'concert', 'streaming', 'musique', 'chanson', 'artiste'],
    'education': ['tutorial', 'learning', 'education', 'cours', 'formation', 'apprentissage'],
    'lifestyle': ['vlog', 'lifestyle', 'travel', 'decoration', 'diy', 'voyage']
}

class QuotaManager:
    """Gestionnaire intelligent des quotas Google Trends"""
    
    def __init__(self):
        self.requests_made = 0
        self.session_start = datetime.now()
        self.last_error_time = None
        self.consecutive_errors = 0
        
    def get_adaptive_delay(self):
        """Délai adaptatif basé sur les erreurs récentes"""
        base_delay = random.uniform(DELAY_MIN, DELAY_MAX)
        
        # Augmenter le délai si erreurs récentes
        if self.consecutive_errors > 0:
            multiplier = 1 + (self.consecutive_errors * 0.5)
            base_delay *= multiplier
            
        # Délai plus long en fin de session
        if self.requests_made > 20:
            base_delay *= 1.5
            
        return base_delay
    
    def should_take_batch_pause(self):
        """Détermine si une pause longue est nécessaire"""
        return self.requests_made > 0 and self.requests_made % BATCH_PAUSE_EVERY == 0
    
    def record_success(self):
        """Enregistre une requête réussie"""
        self.requests_made += 1
        self.consecutive_errors = 0
        
    def record_error(self):
        """Enregistre une erreur 429"""
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
    def get_error_recovery_delay(self):
        """Délai de récupération après erreur 429"""
        if self.consecutive_errors == 1:
            return DELAY_AFTER_ERROR
        elif self.consecutive_errors == 2:
            return DELAY_AFTER_ERROR * 2
        else:
            return DELAY_AFTER_ERROR * 3  # Délai maximal

def get_random_user_agent():
    """User-Agent aléatoire avec rotation maximale"""
    return random.choice(USER_AGENTS)

def create_cache_key(keyword, geo, timeframe):
    """Clé de cache unique"""
    cache_string = f"{keyword}_{geo}_{timeframe}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def connect_mongodb():
    """Connexion MongoDB"""
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        client = MongoClient(mongo_uri)
        db = client['ad_trackr']
        client.admin.command('ping')
        return db
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return None

def check_cached_data(keyword, geo, timeframe, max_age_hours=48):
    """Cache avec durée étendue pour éviter re-requêtes"""
    try:
        db = connect_mongodb()
        if not db:
            return None
            
        cache_key = create_cache_key(keyword, geo, timeframe)
        cached_doc = db.google_trends_raw.find_one({'cache_key': cache_key})
        
        if cached_doc:
            cache_time = datetime.fromisoformat(cached_doc.get('ingestion_timestamp'))
            if datetime.now() - cache_time < timedelta(hours=max_age_hours):
                return cached_doc
        return None
    except Exception:
        return None

def get_single_keyword_trends_safe(keyword, geo, timeframe, quota_manager):
    """
    Version SÉCURISÉE pour un seul mot-clé avec gestion adaptive
    """
    # Vérifier cache en priorité
    cached = check_cached_data(keyword, geo, timeframe)
    if cached:
        print(f"🎯 Cache utilisé: '{keyword}' ({geo})")
        return cached
    
    print(f"🔍 API requête: '{keyword}' ({geo}) [Req #{quota_manager.requests_made + 1}]")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Délai adaptatif avant requête
            if attempt > 0:
                recovery_delay = quota_manager.get_error_recovery_delay()
                print(f"⏰ Récupération erreur: {recovery_delay}s (tentative {attempt + 1})")
                time.sleep(recovery_delay)
            elif quota_manager.requests_made > 0:
                adaptive_delay = quota_manager.get_adaptive_delay()
                print(f"⏰ Délai adaptatif: {adaptive_delay:.1f}s")
                time.sleep(adaptive_delay)
            
            # Pause longue si nécessaire
            if quota_manager.should_take_batch_pause():
                print(f"🛑 PAUSE BATCH ({BATCH_PAUSE_DURATION}s) - Protection quota")
                time.sleep(BATCH_PAUSE_DURATION)
            
            # PyTrends avec configuration conservatrice
            user_agent = get_random_user_agent()
            pytrends = TrendReq(
                hl='fr', tz=360,
                user_agent=user_agent,
                retries=0,  # Pas de retry automatique (on gère manuellement)
                backoff_factor=0,
                timeout=(10, 20)  # Timeout plus long
            )
            
            # Requête individuelle pour valeurs absolues
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            
            # Délai avant récupération des données
            time.sleep(random.uniform(1, 3))
            
            interest_over_time = pytrends.interest_over_time()
            
            if interest_over_time.empty:
                print(f"❌ Pas de données: '{keyword}'")
                quota_manager.record_success()  # Pas une erreur 429
                return None
            
            # Conversion format brut
            raw_data = []
            for index, row in interest_over_time.iterrows():
                raw_data.append({
                    'date': index.isoformat(),
                    'value': int(row[keyword])
                })
            
            # Analyse des pics
            values = [point['value'] for point in raw_data]
            max_value = max(values) if values else 0
            peak_dates = [point['date'] for point in raw_data if point['value'] == max_value]
            
            # Calcul des statistiques de campagne
            high_interest_periods = [point for point in raw_data if point['value'] >= 70]
            avg_value = sum(values) / len(values) if values else 0
            
            result = {
                'keyword': keyword,
                'geo': geo,
                'geo_name': AVAILABLE_GEOS.get(geo, geo),
                'timeframe': timeframe,
                'ingestion_timestamp': datetime.now().isoformat(),
                'raw_data': raw_data,
                'source': 'google_trends_api_safe',
                'cache_key': create_cache_key(keyword, geo, timeframe),
                'user_agent_used': user_agent,
                'attempt_number': attempt + 1,
                # Analyse campagne
                'peak_value': max_value,
                'peak_dates': peak_dates,
                'high_interest_count': len(high_interest_periods),
                'average_interest': round(avg_value, 1),
                'data_points_count': len(raw_data),
                'request_number': quota_manager.requests_made + 1
            }
            
            # Succès !
            quota_manager.record_success()
            print(f"✅ '{keyword}': {len(raw_data)} points, pic={max_value}, moy={avg_value:.1f}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                quota_manager.record_error()
                print(f"🚨 ERREUR 429 '{keyword}' (tentative {attempt + 1}/{MAX_RETRIES})")
                print(f"   📊 Erreurs consécutives: {quota_manager.consecutive_errors}")
                
                if attempt < MAX_RETRIES - 1:
                    # Délai exponentiel après 429
                    recovery_time = quota_manager.get_error_recovery_delay()
                    print(f"   ⏰ Attente récupération: {recovery_time}s")
                    time.sleep(recovery_time)
                else:
                    print(f"   ❌ Abandon '{keyword}' - Quota probablement épuisé")
                    return None
            else:
                print(f"❌ Erreur technique '{keyword}': {e}")
                time.sleep(5)  # Pause courte pour erreurs techniques
                
                if attempt == MAX_RETRIES - 1:
                    return None
    
    return None

def save_to_mongodb(result):
    """Sauvegarde individuelle avec gestion d'erreurs"""
    try:
        db = connect_mongodb()
        if not db:
            return False
        
        collection = db.google_trends_raw
        
        # Upsert par cache_key
        collection.replace_one(
            {'cache_key': result['cache_key']},
            result,
            upsert=True
        )
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde '{result['keyword']}': {e}")
        return False

def analyze_campaign_opportunities(results):
    """Analyse détaillée des opportunités de campagne"""
    if not results:
        return
    
    print("\n" + "="*80)
    print("📈 ANALYSE DES OPPORTUNITÉS DE CAMPAGNE")
    print("="*80)
    
    successful_results = [r for r in results if r]
    
    # Tri par potentiel de campagne (pic + fréquence)
    sorted_results = sorted(
        successful_results, 
        key=lambda x: (x['peak_value'], x['high_interest_count']), 
        reverse=True
    )
    
    for i, result in enumerate(sorted_results, 1):
        keyword = result['keyword']
        peak_value = result['peak_value']
        avg_interest = result['average_interest']
        high_count = result['high_interest_count']
        
        print(f"\n🏆 RANG #{i}: {keyword.upper()}")
        print(f"   📊 Pic maximum: {peak_value}/100")
        print(f"   📈 Intérêt moyen: {avg_interest}/100")
        print(f"   🎯 Périodes favorables: {high_count} points ≥70")
        
        # Recommandation stratégique
        if peak_value >= 90 and high_count >= 5:
            recommendation = "🌟 PRIORITÉ MAXIMALE - Excellent potentiel"
        elif peak_value >= 80 and high_count >= 3:
            recommendation = "⭐ HAUTE PRIORITÉ - Bon potentiel"
        elif peak_value >= 70:
            recommendation = "✨ PRIORITÉ MODÉRÉE - Potentiel correct"
        else:
            recommendation = "💫 PRIORITÉ FAIBLE - Potentiel limité"
        
        print(f"   💡 {recommendation}")
        
        # Analyse temporelle des pics
        if result['peak_dates']:
            print(f"   📅 Meilleurs moments:")
            for date_str in result['peak_dates'][:3]:  # Top 3
                date_obj = datetime.fromisoformat(date_str)
                month_year = date_obj.strftime("%B %Y")
                print(f"      🗓️ {month_year}")

def estimate_completion_time(total_keywords, quota_manager):
    """Estimation du temps restant"""
    if quota_manager.requests_made == 0:
        avg_time_per_request = 20  # Estimation initiale
    else:
        elapsed = (datetime.now() - quota_manager.session_start).total_seconds()
        avg_time_per_request = elapsed / quota_manager.requests_made
    
    remaining = total_keywords - quota_manager.requests_made
    estimated_seconds = remaining * avg_time_per_request
    
    hours = int(estimated_seconds // 3600)
    minutes = int((estimated_seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}min"
    else:
        return f"{minutes}min"

def main():
    """Fonction principale SÉCURISÉE"""
    print("🛡️ YOUTUBE CAMPAIGN ANALYZER - VERSION SÉCURISÉE")
    print("=" * 70)
    print("🎯 Optimisé pour 30-50 mots-clés avec protection quota Google Trends")
    
    try:
        # Initialisation
        quota_manager = QuotaManager()
        db = connect_mongodb()
        if not db:
            return
        print("✅ MongoDB connecté")
        
        # Configuration géo
        print(f"\n🌍 GÉOLOCALISATIONS PRINCIPALES:")
        main_geos = ['FR', 'US', 'GB', 'DE', 'ES', 'IT']
        for code in main_geos:
            print(f"  {code:3} → {AVAILABLE_GEOS[code]}")
        
        geo_input = input("\nCode géo (FR par défaut): ").strip().upper()
        geo = geo_input if geo_input in AVAILABLE_GEOS else 'FR'
        print(f"✅ Géolocalisation: {geo} ({AVAILABLE_GEOS[geo]})")
        
        # Saisie mots-clés
        print(f"\n🎬 CATÉGORIES YOUTUBE DISPONIBLES:")
        for category in YOUTUBE_CATEGORIES.keys():
            print(f"   📂 {category}")
        
        print(f"\n💡 EXEMPLES D'UTILISATION:")
        print("   🔸 Catégories: gaming, beauty, tech")
        print("   🔸 Mots-clés: minecraft, makeup, smartphone, fitness")
        print("   🔸 Mixte: gaming, makeup tutorial, tech review")
        
        keywords_input = input("\nMots-clés/catégories (virgules): ").strip()
        
        if not keywords_input:
            print("❌ Aucune saisie")
            return
        
        # Expansion et préparation
        keywords = []
        for item in keywords_input.split(','):
            item = item.strip().lower()
            if item in YOUTUBE_CATEGORIES:
                expanded = YOUTUBE_CATEGORIES[item]
                keywords.extend(expanded)
                print(f"📂 '{item}' → {len(expanded)} mots-clés")
            else:
                keywords.append(item)
        
        # Nettoyage et limitation
        keywords = list(dict.fromkeys(keywords))  # Dédoublonnage
        if len(keywords) > 50:
            print(f"⚠️ Limitation à 50 mots-clés (vous aviez {len(keywords)})")
            keywords = keywords[:50]
        
        print(f"\n📋 LISTE FINALE: {len(keywords)} mots-clés")
        
        # Estimation temps
        estimated_time = len(keywords) * 18  # 18 secondes en moyenne par mot-clé
        hours = estimated_time // 3600
        minutes = (estimated_time % 3600) // 60
        time_str = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
        
        print(f"⏰ Temps estimé: {time_str}")
        print(f"🛡️ Protection 429: Délais adaptatifs + pauses automatiques")
        
        # Confirmation
        confirm = input(f"\n🚀 Lancer l'analyse SÉCURISÉE? (y/n): ")
        if confirm.lower() not in ['y', 'yes', 'o', 'oui']:
            return
        
        # Traitement séquentiel sécurisé
        print(f"\n🔄 TRAITEMENT SÉCURISÉ EN COURS...")
        results = []
        
        for i, keyword in enumerate(keywords, 1):
            print(f"\n--- [{i}/{len(keywords)}] ---")
            
            # Estimation temps restant
            if i > 1:
                remaining_time = estimate_completion_time(len(keywords), quota_manager)
                print(f"⏰ Temps restant estimé: {remaining_time}")
            
            # Traitement avec protection
            result = get_single_keyword_trends_safe(keyword, geo, 'today 12-m', quota_manager)
            
            if result:
                # Sauvegarde immédiate
                if save_to_mongodb(result):
                    print(f"💾 Sauvé: '{keyword}'")
                results.append(result)
            else:
                results.append(None)
            
            # Vérification état quota
            if quota_manager.consecutive_errors >= 3:
                print(f"🚨 ALERTE: {quota_manager.consecutive_errors} erreurs consécutives")
                print(f"💡 Recommandation: Pause longue ou arrêt")
                
                pause_choice = input("Continuer (c), Pause 5min (p), ou Arrêter (a)? ")
                if pause_choice.lower() == 'a':
                    break
                elif pause_choice.lower() == 'p':
                    print("⏸️ Pause de 5 minutes...")
                    time.sleep(300)
                    quota_manager.consecutive_errors = 0
        
        # Analyse finale
        analyze_campaign_opportunities(results)
        
        # Statistiques
        successful = len([r for r in results if r])
        duration = (datetime.now() - quota_manager.session_start).total_seconds()
        
        print(f"\n🎯 RÉSULTATS FINAUX:")
        print(f"✅ Succès: {successful}/{len(keywords)} mots-clés")
        print(f"⏱️ Durée totale: {duration/60:.1f} minutes")
        print(f"🚨 Erreurs 429: {quota_manager.requests_made - successful}")
        print(f"📊 Taux de succès: {(successful/len(keywords)*100):.1f}%")
        
        if successful > 0:
            print(f"\n🚀 Données prêtes pour:")
            print(f"   📊 Spark processing (spark_mongo_to_hdfs_optimized.py)")
            print(f"   📈 Power BI export (powerbi_export.py)")
        
    except KeyboardInterrupt:
        print("\n👋 Arrêt utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == "__main__":
    main() 