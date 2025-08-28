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
    """
    Récupère le top 50 des vidéos YouTube les plus populaires
    
    Args:
        api_key (str): Clé API YouTube Data v3
    
    Returns:
        list: Liste des 50 vidéos les plus populaires
    """
    url = "https://www.googleapis.com/youtube/v3/videos"
    
    params = {
        'part': 'snippet,statistics',
        'chart': 'mostPopular',
        'regionCode': 'FR',  # Région pour obtenir le classement global
        'maxResults': 50,    # Maximum autorisé par YouTube
        'key': api_key
    }
    
    try:
        print("🔥 Récupération du TOP 50 des vidéos YouTube...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        videos = data.get('items', [])
        
        print(f"✅ {len(videos)} vidéos récupérées")
        return videos
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return []

def display_top_videos(videos):
    """
    Affiche la liste des vidéos populaires
    
    Args:
        videos (list): Liste des vidéos depuis l'API YouTube
    """
    print("\n" + "="*80)
    print("🏆 TOP 50 VIDÉOS YOUTUBE LES PLUS POPULAIRES")
    print("="*80)
    
    for i, video in enumerate(videos, 1):
        snippet = video.get('snippet', {})
        stats = video.get('statistics', {})
        
        title = snippet.get('title', 'N/A')
        channel = snippet.get('channelTitle', 'N/A')
        views = format_views(stats.get('viewCount', '0'))
        
        # Limiter la longueur du titre
        if len(title) > 60:
            title = title[:57] + "..."
        
        print(f"{i:2d}. {title}")
        print(f"    👤 {channel} | 👀 {views} vues")
        print()

def format_views(view_count):
    """
    Formate le nombre de vues de façon lisible
    
    Args:
        view_count (str): Nombre de vues sous forme de chaîne
    
    Returns:
        str: Nombre de vues formaté
    """
    try:
        views = int(view_count)
        if views >= 1_000_000_000:
            return f"{views / 1_000_000_000:.1f}B"
        elif views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        elif views >= 1_000:
            return f"{views / 1_000:.1f}K"
        else:
            return f"{views:,}"
    except (ValueError, TypeError):
        return "0"

def save_to_json(videos, filename="top_50_youtube_videos.json"):
    """
    Sauvegarde les vidéos dans un fichier JSON
    
    Args:
        videos (list): Liste des vidéos
        filename (str): Nom du fichier de sortie
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        print(f"💾 Données sauvegardées dans: {filename}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")

def main():
    """
    Fonction principale
    """
    print("🎬 Récupération TOP 50 Vidéos YouTube")
    print("="*40)
    
    # ⚠️ CLÉ API YOUTUBE DATA V3 CONFIGURÉE
    API_KEY = "AIzaSyCbet0zd9cco2V1_6zLGlPkaJE2AF_arNs"
    
    if not API_KEY or API_KEY == "VOTRE_CLE_API_YOUTUBE_ICI":
        print("❌ Veuillez configurer votre clé API YouTube Data v3")
        print("\n📋 Instructions:")
        print("1. Allez sur https://console.cloud.google.com/")
        print("2. Créez/sélectionnez un projet")
        print("3. Activez l'API YouTube Data v3")
        print("4. Créez une clé API")
        return
    
    # Récupérer le top 50
    top_videos = get_top_50_videos(API_KEY)
    
    if top_videos:
        # Afficher les résultats
        display_top_videos(top_videos)
        
        # Sauvegarder en JSON
        save_to_json(top_videos)
        
        print(f"\n✅ Mission accomplie! {len(top_videos)} vidéos récupérées")
    else:
        print("❌ Aucune vidéo récupérée")

if __name__ == "__main__":
    main()
