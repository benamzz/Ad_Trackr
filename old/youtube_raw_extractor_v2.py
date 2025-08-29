import requests
import csv
import json
from datetime import datetime
import time

class YouTubeChannelExtractor:
    def __init__(self, api_key):
        """
        Extracteur de chaînes YouTube avec catégories et hashtags
        
        Args:
            api_key (str): Clé API YouTube Data v3
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.all_channels = {}  # Pour éviter les doublons
        self.hashtags_categories = set()  # Collecteur d'hashtags/catégories
    
    def get_top_50_global_videos(self, max_results=50):
        """
        Récupère les 50 premières vidéos mondiales populaires
        
        Args:
            max_results (int): Nombre de vidéos
        
        Returns:
            list: Données des vidéos
        """
        url = f"{self.base_url}/videos"
        
        params = {
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            print(f"🌍 Récupération TOP {max_results} vidéos mondiales...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('items', [])
            
            print(f"✅ {len(videos)} vidéos mondiales récupérées")
            return videos
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur récupération vidéos: {e}")
            return []
    
    def get_channels_complete_data(self, channel_ids):
        """
        Récupère TOUTES les données des chaînes (avec catégories et hashtags)
        
        Args:
            channel_ids (list): Liste des IDs de chaînes
        
        Returns:
            list: Données complètes des chaînes
        """
        channels_data = []
        
        # Traitement par batch de 50 (limite API)
        for i in range(0, len(channel_ids), 50):
            batch_ids = channel_ids[i:i+50]
            
            url = f"{self.base_url}/channels"
            params = {
                'part': 'snippet,statistics,brandingSettings,contentDetails,status,topicDetails',
                'id': ','.join(batch_ids),
                'key': self.api_key
            }
            
            try:
                print(f"📊 Récupération chaînes {i+1}-{min(i+50, len(channel_ids))}...")
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                batch_channels = data.get('items', [])
                channels_data.extend(batch_channels)
                
                # Collecter les hashtags/catégories pour la recherche ultérieure
                self.collect_hashtags_categories(batch_channels)
                
                # Pause pour éviter les limites de taux
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur récupération chaînes: {e}")
        
        return channels_data
    
    def collect_hashtags_categories(self, channels_data):
        """
        Collecte tous les hashtags et catégories des chaînes
        
        Args:
            channels_data (list): Données des chaînes
        """
        for channel in channels_data:
            # Catégories de contenu (topicCategories)
            topic_details = channel.get('topicDetails', {})
            topic_categories = topic_details.get('topicCategories', [])
            
            for category in topic_categories:
                # Extraire le nom de la catégorie depuis l'URL
                if '/' in category:
                    category_name = category.split('/')[-1].replace('_', ' ')
                    # Filtrer les catégories trop longues ou vides
                    if len(category_name) > 2 and len(category_name) < 50:
                        self.hashtags_categories.add(category_name)
            
            # Mots-clés du branding (peuvent servir de hashtags)
            branding = channel.get('brandingSettings', {})
            keywords = branding.get('channel', {}).get('keywords', '')
            if keywords:
                # Nettoyage et séparation des mots-clés
                keywords_clean = keywords.replace('"', '').replace("'", "")
                keyword_list = [k.strip() for k in keywords_clean.split(',')]
                
                for keyword in keyword_list:
                    # Filtrer les mots-clés valides (longueur raisonnable)
                    if keyword and len(keyword) > 2 and len(keyword) < 30:
                        self.hashtags_categories.add(keyword)
        
        print(f"📋 {len(self.hashtags_categories)} hashtags/catégories collectés")
    
    def search_top_channels_by_category(self, category_term, max_results=10):
        """
        Recherche les top chaînes par catégorie/hashtag
        
        Args:
            category_term (str): Terme de catégorie ou hashtag
            max_results (int): Nombre de chaînes à récupérer
        
        Returns:
            list: Chaînes trouvées
        """
        url = f"{self.base_url}/search"
        
        params = {
            'part': 'snippet',
            'q': category_term,
            'type': 'channel',
            'order': 'relevance',  # Ordre par pertinence
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            print(f"🔍 Recherche top chaînes pour: '{category_term}'...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('items', [])
            
            # Extraire les IDs de chaînes
            channel_ids = []
            for item in search_results:
                if 'channelId' in item.get('id', {}):
                    channel_ids.append(item['id']['channelId'])
            
            if channel_ids:
                # Récupérer les détails complets des chaînes
                channels_details = self.get_channels_complete_data(channel_ids)
                
                # Trier par nombre d'abonnés (top par followers)
                channels_details.sort(
                    key=lambda x: int(x.get('statistics', {}).get('subscriberCount', 0)), 
                    reverse=True
                )
                
                return channels_details[:max_results]  # Top 10
            
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur recherche catégorie '{category_term}': {e}")
            return []
    
    def process_all_categories(self):
        """
        Traite toutes les catégories collectées pour récupérer les top chaînes
        
        Returns:
            dict: Dictionnaire {catégorie: [chaînes]}
        """
        category_channels = {}
        
        # Convertir en liste pour éviter l'erreur "Set changed size during iteration"
        categories_list = list(self.hashtags_categories)
        
        print(f"\n🔍 Recherche des top chaînes pour {len(categories_list)} catégories...")
        
        for i, category in enumerate(categories_list, 1):
            print(f"\n📂 [{i}/{len(categories_list)}] Catégorie: {category}")
            
            # Rechercher les top chaînes pour cette catégorie
            top_channels = self.search_top_channels_by_category(category, max_results=10)
            
            if top_channels:
                category_channels[category] = top_channels
                print(f"   ✅ {len(top_channels)} chaînes trouvées")
                
                # Ajouter au dictionnaire global pour éviter les doublons
                for channel in top_channels:
                    channel_id = channel.get('id')
                    if channel_id:
                        self.all_channels[channel_id] = channel
            else:
                print(f"   ❌ Aucune chaîne trouvée")
            
            # Pause entre les requêtes pour respecter les limites
            time.sleep(0.5)
        
        return category_channels
    
    def export_all_channels_csv(self):
        """
        Exporte toutes les chaînes uniques collectées en CSV
        """
        filename = f"youtube_all_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'channel_id', 'title', 'description', 'custom_url', 'published_at',
                'country', 'default_language', 'subscriber_count', 'view_count',
                'video_count', 'keywords', 'topic_categories', 'topic_ids',
                'privacy_status', 'is_linked', 'made_for_kids', 'subscriber_tier'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for channel in self.all_channels.values():
                snippet = channel.get('snippet', {})
                statistics = channel.get('statistics', {})
                branding = channel.get('brandingSettings', {})
                status = channel.get('status', {})
                topic_details = channel.get('topicDetails', {})
                
                # Topic categories
                topic_categories = topic_details.get('topicCategories', [])
                topic_categories_clean = []
                for cat in topic_categories:
                    if '/' in cat:
                        topic_categories_clean.append(cat.split('/')[-1])
                    else:
                        topic_categories_clean.append(cat)
                topic_categories_str = '|'.join(topic_categories_clean)
                
                # Topic IDs
                topic_ids = topic_details.get('topicIds', [])
                topic_ids_str = '|'.join(topic_ids) if topic_ids else ''
                
                # Keywords
                keywords = branding.get('channel', {}).get('keywords', '')
                
                # Calcul du tier d'abonnés
                subscriber_count = int(statistics.get('subscriberCount', 0))
                if subscriber_count >= 10000000:
                    tier = "Mega (10M+)"
                elif subscriber_count >= 1000000:
                    tier = "Macro (1M-10M)"
                elif subscriber_count >= 100000:
                    tier = "Mid (100K-1M)"
                elif subscriber_count >= 10000:
                    tier = "Micro (10K-100K)"
                elif subscriber_count >= 1000:
                    tier = "Nano (1K-10K)"
                else:
                    tier = "Emerging (<1K)"
                
                row = {
                    'channel_id': channel.get('id', ''),
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', '')[:500],  # Limité
                    'custom_url': snippet.get('customUrl', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'country': snippet.get('country', ''),
                    'default_language': snippet.get('defaultLanguage', ''),
                    'subscriber_count': subscriber_count,
                    'view_count': statistics.get('viewCount', 0),
                    'video_count': statistics.get('videoCount', 0),
                    'keywords': keywords,
                    'topic_categories': topic_categories_str,
                    'topic_ids': topic_ids_str,
                    'privacy_status': status.get('privacyStatus', ''),
                    'is_linked': status.get('isLinked', False),
                    'made_for_kids': status.get('madeForKids', False),
                    'subscriber_tier': tier
                }
                
                writer.writerow(row)
        
        print(f"📊 Toutes les chaînes exportées: {filename}")
        return filename
    
    def export_categories_channels_csv(self, category_channels):
        """
        Exporte la relation catégories -> chaînes en CSV
        """
        filename = f"youtube_categories_channels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'category', 'channel_id', 'channel_title', 'subscriber_count',
                'view_count', 'video_count', 'country', 'position_in_category'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for category, channels in category_channels.items():
                for position, channel in enumerate(channels, 1):
                    snippet = channel.get('snippet', {})
                    statistics = channel.get('statistics', {})
                    
                    row = {
                        'category': category,
                        'channel_id': channel.get('id', ''),
                        'channel_title': snippet.get('title', ''),
                        'subscriber_count': statistics.get('subscriberCount', 0),
                        'view_count': statistics.get('viewCount', 0),
                        'video_count': statistics.get('videoCount', 0),
                        'country': snippet.get('country', ''),
                        'position_in_category': position
                    }
                    
                    writer.writerow(row)
        
        print(f"📊 Relations catégories-chaînes exportées: {filename}")
        return filename

def main():
    """
    Script principal pour extraire les chaînes YouTube par catégories
    """
    print("📊 EXTRACTEUR DE CHAÎNES YOUTUBE PAR CATÉGORIES")
    print("="*60)
    print("🎯 Processus:")
    print("   1. Récupérer TOP 50 vidéos mondiales")
    print("   2. Extraire leurs chaînes + catégories/hashtags")
    print("   3. Rechercher TOP 10 chaînes par catégorie")
    print("   4. Export CSV complet")
    print("="*60)
    
    # Configuration API
    API_KEY = "AIzaSyCbet0zd9cco2V1_6zLGlPkaJE2AF_arNs"
    
    if not API_KEY or API_KEY == "VOTRE_CLE_API_YOUTUBE_ICI":
        print("❌ Veuillez configurer votre clé API YouTube Data v3")
        return
    
    # Initialiser l'extracteur
    extractor = YouTubeChannelExtractor(API_KEY)
    
    print("\n🔍 ÉTAPE 1: Récupération des TOP 50 vidéos mondiales")
    videos = extractor.get_top_50_global_videos(max_results=50)
    
    if not videos:
        print("❌ Aucune vidéo récupérée")
        return
    
    print("\n🔍 ÉTAPE 2: Récupération des chaînes des vidéos populaires")
    # Extraire les IDs uniques des chaînes depuis les vidéos
    initial_channel_ids = list(set([video['snippet']['channelId'] for video in videos]))
    initial_channels = extractor.get_channels_complete_data(initial_channel_ids)
    
    print(f"✅ {len(initial_channels)} chaînes initiales récupérées")
    print(f"📋 {len(extractor.hashtags_categories)} catégories/hashtags collectés")
    
    # Ajouter les chaînes initiales au dictionnaire global
    for channel in initial_channels:
        channel_id = channel.get('id')
        if channel_id:
            extractor.all_channels[channel_id] = channel
    
    print("\n🔍 ÉTAPE 3: Recherche des TOP 10 chaînes par catégorie")
    category_channels = extractor.process_all_categories()
    
    print(f"\n📊 ÉTAPE 4: Export des données")
    
    # Export uniquement : Toutes les chaînes uniques
    channels_file = extractor.export_all_channels_csv()
    
    print(f"\n✅ Extraction terminée!")
    print(f"📊 Résumé:")
    print(f"   🎬 Vidéos analysées: {len(videos)}")
    print(f"   📺 Chaînes uniques: {len(extractor.all_channels)}")
    print(f"   📂 Catégories explorées: {len(extractor.hashtags_categories)}")
    print(f"   🔗 Relations catégorie-chaîne: {sum(len(channels) for channels in category_channels.values())}")
    
    print(f"\n📄 Fichier généré:")
    print(f"   • {channels_file} - Toutes les chaînes avec métadonnées complètes")
    
    # Afficher quelques statistiques
    print(f"\n📈 Aperçu des top catégories:")
    category_stats = [(cat, len(channels)) for cat, channels in category_channels.items()]
    category_stats.sort(key=lambda x: x[1], reverse=True)
    
    for i, (category, count) in enumerate(category_stats[:10], 1):
        print(f"   {i:2d}. {category}: {count} chaînes trouvées")

if __name__ == "__main__":
    main()
