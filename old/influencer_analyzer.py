import requests
import json
from datetime import datetime
import time

class YouTubeInfluencerAnalyzer:
    def __init__(self, api_key):
        """
        Initialise l'analyseur d'influenceurs YouTube
        
        Args:
            api_key (str): Clé API YouTube Data v3
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.channels_data = []
        self.videos_data = []
    
    def get_popular_videos_with_channels(self, region_code="FR", max_results=50):
        """
        Récupère les vidéos populaires et les détails des chaînes
        """
        url = f"{self.base_url}/videos"
        
        params = {
            'part': 'snippet,statistics,contentDetails',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            print(f"🔥 Récupération des vidéos populaires ({region_code})...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('items', [])
            
            # Extraire les IDs de chaînes uniques
            channel_ids = list(set([video['snippet']['channelId'] for video in videos]))
            
            print(f"✅ {len(videos)} vidéos et {len(channel_ids)} chaînes uniques trouvées")
            
            # Récupérer les détails des chaînes
            channels_details = self.get_channels_details(channel_ids)
            
            return videos, channels_details
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur API vidéos: {e}")
            return [], []
    
    def get_channels_details(self, channel_ids):
        """
        Récupère TOUTES les métadonnées disponibles pour les chaînes
        
        Args:
            channel_ids (list): Liste des IDs de chaînes
        
        Returns:
            list: Détails complets des chaînes
        """
        channels_data = []
        
        # YouTube API limite à 50 chaînes par requête
        for i in range(0, len(channel_ids), 50):
            batch_ids = channel_ids[i:i+50]
            
            url = f"{self.base_url}/channels"
            params = {
                'part': 'snippet,statistics,brandingSettings,contentDetails,status,topicDetails,localizations',
                'id': ','.join(batch_ids),
                'key': self.api_key
            }
            
            try:
                print(f"📊 Récupération métadonnées chaînes {i+1}-{min(i+50, len(channel_ids))}...")
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                channels_data.extend(data.get('items', []))
                
                # Pause pour éviter les limites de taux
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur API chaînes: {e}")
        
        return channels_data
    
    def search_influencers_by_topic(self, topic, max_results=25):
        """
        Recherche d'influenceurs par sujet/niche
        
        Args:
            topic (str): Sujet de recherche (ex: "tech", "beauty", "gaming")
            max_results (int): Nombre de résultats
        
        Returns:
            tuple: (vidéos, chaînes)
        """
        url = f"{self.base_url}/search"
        
        params = {
            'part': 'snippet',
            'q': topic,
            'type': 'channel',
            'order': 'relevance',
            'maxResults': max_results,
            'key': self.api_key
        }
        
        try:
            print(f"🔍 Recherche d'influenceurs sur: '{topic}'...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('items', [])
            
            # Extraire les IDs de chaînes
            channel_ids = [item['id']['channelId'] for item in search_results if 'channelId' in item.get('id', {})]
            
            # Récupérer les détails complets
            channels_details = self.get_channels_details(channel_ids)
            
            return search_results, channels_details
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur recherche: {e}")
            return [], []
    
    def analyze_channel_engagement(self, channel_data):
        """
        Calcule les métriques d'engagement pour une chaîne
        
        Args:
            channel_data (dict): Données de la chaîne
        
        Returns:
            dict: Métriques d'engagement calculées
        """
        stats = channel_data.get('statistics', {})
        
        subscribers = int(stats.get('subscriberCount', 0))
        total_views = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        
        # Calculs d'engagement
        avg_views_per_video = total_views / video_count if video_count > 0 else 0
        engagement_rate = (avg_views_per_video / subscribers * 100) if subscribers > 0 else 0
        
        return {
            'subscribers': subscribers,
            'total_views': total_views,
            'video_count': video_count,
            'avg_views_per_video': avg_views_per_video,
            'engagement_rate': engagement_rate,
            'views_per_subscriber': total_views / subscribers if subscribers > 0 else 0
        }
    
    def generate_influencer_report(self, channels_data, videos_data=None):
        """
        Génère un rapport d'analyse des influenceurs
        
        Args:
            channels_data (list): Données des chaînes
            videos_data (list): Données des vidéos (optionnel)
        
        Returns:
            dict: Rapport d'analyse complet
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_channels': len(channels_data),
                'total_videos': len(videos_data) if videos_data else 0
            },
            'channels_analysis': [],
            'summary_stats': {
                'top_subscribers': [],
                'top_engagement': [],
                'content_categories': {},
                'geographic_distribution': {},
                'language_distribution': {}
            }
        }
        
        # Analyser chaque chaîne
        for channel in channels_data:
            channel_analysis = self.analyze_single_channel(channel)
            report['channels_analysis'].append(channel_analysis)
        
        # Générer les statistiques de résumé
        report['summary_stats'] = self.generate_summary_stats(report['channels_analysis'])
        
        return report
    
    def analyze_single_channel(self, channel_data):
        """
        Analyse complète d'une seule chaîne
        
        Args:
            channel_data (dict): Données de la chaîne
        
        Returns:
            dict: Analyse complète de la chaîne
        """
        snippet = channel_data.get('snippet', {})
        statistics = channel_data.get('statistics', {})
        branding = channel_data.get('brandingSettings', {})
        content_details = channel_data.get('contentDetails', {})
        status = channel_data.get('status', {})
        topic_details = channel_data.get('topicDetails', {})
        
        # Informations de base
        basic_info = {
            'channel_id': channel_data.get('id'),
            'title': snippet.get('title'),
            'description': snippet.get('description', '')[:500] + '...' if len(snippet.get('description', '')) > 500 else snippet.get('description', ''),
            'custom_url': snippet.get('customUrl'),
            'published_at': snippet.get('publishedAt'),
            'country': snippet.get('country'),
            'default_language': snippet.get('defaultLanguage'),
            'thumbnails': snippet.get('thumbnails', {})
        }
        
        # Statistiques d'audience
        audience_stats = {
            'subscriber_count': int(statistics.get('subscriberCount', 0)),
            'view_count': int(statistics.get('viewCount', 0)),
            'video_count': int(statistics.get('videoCount', 0)),
            'hidden_subscriber_count': statistics.get('hiddenSubscriberCount', False)
        }
        
        # Métriques d'engagement
        engagement_metrics = self.analyze_channel_engagement(channel_data)
        
        # Branding et positionnement
        branding_info = {
            'channel_keywords': branding.get('channel', {}).get('keywords'),
            'channel_description': branding.get('channel', {}).get('description'),
            'banner_image': branding.get('image', {}).get('bannerExternalUrl'),
            'trailer_video_id': branding.get('channel', {}).get('unsubscribedTrailerVideoId')
        }
        
        # Catégories de contenu
        content_info = {
            'related_playlists': content_details.get('relatedPlaylists', {}),
            'topic_categories': topic_details.get('topicCategories', []),
            'topic_ids': topic_details.get('topicIds', [])
        }
        
        # Statut et monétisation
        monetization_info = {
            'privacy_status': status.get('privacyStatus'),
            'is_linked': status.get('isLinked'),
            'long_uploads_status': status.get('longUploadsStatus'),
            'made_for_kids': status.get('madeForKids')
        }
        
        # Score d'influence calculé
        influence_score = self.calculate_influence_score(audience_stats, engagement_metrics)
        
        return {
            'basic_info': basic_info,
            'audience_stats': audience_stats,
            'engagement_metrics': engagement_metrics,
            'branding_info': branding_info,
            'content_info': content_info,
            'monetization_info': monetization_info,
            'influence_score': influence_score,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def calculate_influence_score(self, audience_stats, engagement_metrics):
        """
        Calcule un score d'influence basé sur plusieurs métriques
        
        Args:
            audience_stats (dict): Statistiques d'audience
            engagement_metrics (dict): Métriques d'engagement
        
        Returns:
            dict: Score d'influence et composants
        """
        # Normalisation des métriques (score sur 100)
        subscriber_score = min(audience_stats['subscriber_count'] / 1000000 * 20, 30)  # Max 30 points
        engagement_score = min(engagement_metrics['engagement_rate'] * 2, 25)  # Max 25 points
        consistency_score = min(audience_stats['video_count'] / 100 * 15, 20)  # Max 20 points
        views_score = min(audience_stats['view_count'] / 10000000 * 25, 25)  # Max 25 points
        
        total_score = subscriber_score + engagement_score + consistency_score + views_score
        
        # Classification
        if total_score >= 80:
            tier = "Macro-Influencer"
        elif total_score >= 60:
            tier = "Mid-Tier Influencer"
        elif total_score >= 40:
            tier = "Micro-Influencer"
        elif total_score >= 20:
            tier = "Nano-Influencer"
        else:
            tier = "Emerging Creator"
        
        return {
            'total_score': round(total_score, 2),
            'tier': tier,
            'components': {
                'subscriber_score': round(subscriber_score, 2),
                'engagement_score': round(engagement_score, 2),
                'consistency_score': round(consistency_score, 2),
                'views_score': round(views_score, 2)
            }
        }
    
    def generate_summary_stats(self, channels_analysis):
        """
        Génère des statistiques de résumé pour le rapport
        
        Args:
            channels_analysis (list): Liste des analyses de chaînes
        
        Returns:
            dict: Statistiques de résumé
        """
        # Top chaînes par abonnés
        top_subscribers = sorted(
            channels_analysis, 
            key=lambda x: x['audience_stats']['subscriber_count'], 
            reverse=True
        )[:10]
        
        # Top chaînes par engagement
        top_engagement = sorted(
            channels_analysis,
            key=lambda x: x['engagement_metrics']['engagement_rate'],
            reverse=True
        )[:10]
        
        # Distribution des catégories
        category_count = {}
        country_count = {}
        language_count = {}
        tier_count = {}
        
        for analysis in channels_analysis:
            # Catégories de contenu
            categories = analysis['content_info']['topic_categories']
            for category in categories:
                category_name = category.split('/')[-1] if '/' in category else category
                category_count[category_name] = category_count.get(category_name, 0) + 1
            
            # Pays
            country = analysis['basic_info']['country']
            if country:
                country_count[country] = country_count.get(country, 0) + 1
            
            # Langues
            language = analysis['basic_info']['default_language']
            if language:
                language_count[language] = language_count.get(language, 0) + 1
            
            # Tiers d'influence
            tier = analysis['influence_score']['tier']
            tier_count[tier] = tier_count.get(tier, 0) + 1
        
        return {
            'top_subscribers': [
                {
                    'channel': ch['basic_info']['title'],
                    'subscribers': ch['audience_stats']['subscriber_count'],
                    'engagement_rate': ch['engagement_metrics']['engagement_rate']
                }
                for ch in top_subscribers
            ],
            'top_engagement': [
                {
                    'channel': ch['basic_info']['title'],
                    'engagement_rate': ch['engagement_metrics']['engagement_rate'],
                    'subscribers': ch['audience_stats']['subscriber_count']
                }
                for ch in top_engagement
            ],
            'content_categories': dict(sorted(category_count.items(), key=lambda x: x[1], reverse=True)),
            'geographic_distribution': dict(sorted(country_count.items(), key=lambda x: x[1], reverse=True)),
            'language_distribution': dict(sorted(language_count.items(), key=lambda x: x[1], reverse=True)),
            'influence_tiers': tier_count
        }

def save_analysis_report(report, filename="influencer_analysis_report.json"):
    """
    Sauvegarde le rapport d'analyse
    
    Args:
        report (dict): Rapport d'analyse
        filename (str): Nom du fichier
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"💾 Rapport sauvegardé: {filename}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def display_summary_report(report):
    """
    Affiche un résumé du rapport d'analyse
    
    Args:
        report (dict): Rapport d'analyse
    """
    print("\n" + "="*80)
    print("📊 RAPPORT D'ANALYSE DES INFLUENCEURS YOUTUBE")
    print("="*80)
    
    metadata = report['metadata']
    summary = report['summary_stats']
    
    print(f"\n📈 MÉTRIQUES GÉNÉRALES:")
    print(f"   📺 Chaînes analysées: {metadata['total_channels']}")
    print(f"   🎬 Vidéos analysées: {metadata['total_videos']}")
    print(f"   📅 Généré le: {metadata['generated_at'][:19]}")
    
    print(f"\n🏆 TOP 5 CHAÎNES PAR ABONNÉS:")
    for i, channel in enumerate(summary['top_subscribers'][:5], 1):
        subs = format_number(channel['subscribers'])
        eng = f"{channel['engagement_rate']:.2f}%"
        print(f"   {i}. {channel['channel']} - {subs} abonnés (Eng: {eng})")
    
    print(f"\n🔥 TOP 5 CHAÎNES PAR ENGAGEMENT:")
    for i, channel in enumerate(summary['top_engagement'][:5], 1):
        eng = f"{channel['engagement_rate']:.2f}%"
        subs = format_number(channel['subscribers'])
        print(f"   {i}. {channel['channel']} - {eng} engagement ({subs} abonnés)")
    
    print(f"\n📊 RÉPARTITION PAR INFLUENCE:")
    for tier, count in summary['influence_tiers'].items():
        print(f"   {tier}: {count} chaînes")
    
    print(f"\n🌍 RÉPARTITION GÉOGRAPHIQUE (Top 5):")
    for i, (country, count) in enumerate(list(summary['geographic_distribution'].items())[:5], 1):
        print(f"   {i}. {country}: {count} chaînes")
    
    print(f"\n📋 CATÉGORIES DE CONTENU (Top 5):")
    for i, (category, count) in enumerate(list(summary['content_categories'].items())[:5], 1):
        print(f"   {i}. {category}: {count} chaînes")

def format_number(num):
    """Formate un nombre pour affichage"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return f"{num:,}"

def main():
    """
    Fonction principale pour l'analyse d'influenceurs
    """
    print("🎯 ANALYSEUR D'INFLUENCEURS YOUTUBE")
    print("="*50)
    print("📋 Objectifs d'analyse:")
    print("   • Cartographie des influenceurs")
    print("   • Analyse de l'audience et engagement")
    print("   • Identification des tendances marché")
    print("   • Analyse concurrentielle")
    print("="*50)
    
    # Configuration API
    API_KEY = "AIzaSyCbet0zd9cco2V1_6zLGlPkaJE2AF_arNs"
    
    if not API_KEY or API_KEY == "VOTRE_CLE_API_YOUTUBE_ICI":
        print("❌ Veuillez configurer votre clé API YouTube Data v3")
        return
    
    # Initialiser l'analyseur
    analyzer = YouTubeInfluencerAnalyzer(API_KEY)
    
    print("\n🔍 ÉTAPE 1: Analyse des chaînes populaires")
    videos, channels = analyzer.get_popular_videos_with_channels(region_code="FR", max_results=50)
    
    # Option: Recherche par niche
    print("\n🔍 ÉTAPE 2: Recherche d'influenceurs par niche")
    niches = ["tech", "beauty", "gaming", "fitness", "food"]
    
    all_channels = list(channels)  # Copie des chaînes populaires
    
    for niche in niches:
        print(f"\n   Recherche niche: {niche}")
        _, niche_channels = analyzer.search_influencers_by_topic(niche, max_results=10)
        all_channels.extend(niche_channels)
        time.sleep(1)  # Pause entre les requêtes
    
    # Supprimer les doublons
    unique_channels = {}
    for channel in all_channels:
        channel_id = channel.get('id')
        if channel_id and channel_id not in unique_channels:
            unique_channels[channel_id] = channel
    
    final_channels = list(unique_channels.values())
    
    print(f"\n📊 ÉTAPE 3: Génération du rapport d'analyse")
    print(f"   Total chaînes uniques: {len(final_channels)}")
    
    # Générer le rapport complet
    report = analyzer.generate_influencer_report(final_channels, videos)
    
    # Afficher le résumé
    display_summary_report(report)
    
    # Sauvegarder le rapport
    save_analysis_report(report, "influencer_analysis_report.json")
    
    print(f"\n✅ Analyse terminée!")
    print(f"📄 Rapport détaillé disponible dans: influencer_analysis_report.json")

if __name__ == "__main__":
    main()
