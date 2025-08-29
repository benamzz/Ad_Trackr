#!/usr/bin/env python3
"""
Script de test pour vérifier que l'infrastructure Docker est prête
pour le workflow YouTube
"""

import os
import sys
import time
import requests
import pymongo
from hdfs import InsecureClient

def test_mongodb():
    """Test de connexion MongoDB"""
    print("🔍 Test de connexion MongoDB...")
    try:
        mongo_host = os.getenv("MONGO_HOST", "mongo")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        mongo_user = os.getenv("MONGO_USER", "admin")
        mongo_password = os.getenv("MONGO_PASSWORD", "password123")
        
        mongo_uri = f'mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/'
        client = pymongo.MongoClient(mongo_uri, authSource='admin', serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        print("✅ MongoDB accessible")
        return True
    except Exception as e:
        print(f"❌ MongoDB non accessible: {e}")
        return False

def test_hdfs():
    """Test de connexion HDFS"""
    print("🔍 Test de connexion HDFS...")
    try:
        hdfs_host = os.getenv("HDFS_HOST", "namenode")
        hdfs_port = os.getenv("HDFS_PORT", "9870")
        hdfs_url = f'http://{hdfs_host}:{hdfs_port}'
        
        client = InsecureClient(hdfs_url, user='root')
        client.list('/')
        print("✅ HDFS accessible")
        return True
    except Exception as e:
        print(f"❌ HDFS non accessible: {e}")
        return False

def test_spark():
    """Test de connexion Spark"""
    print("🔍 Test de connexion Spark...")
    try:
        spark_host = os.getenv("SPARK_HOST", "spark-master")
        spark_port = os.getenv("SPARK_PORT", "8080")
        spark_url = f'http://{spark_host}:{spark_port}'
        
        response = requests.get(spark_url, timeout=5)
        if response.status_code == 200:
            print("✅ Spark accessible")
            return True
        else:
            print(f"❌ Spark non accessible: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Spark non accessible: {e}")
        return False

def test_youtube_api():
    """Test de la clé API YouTube"""
    print("🔍 Test de la clé API YouTube...")
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key or api_key == "YOUR_YOUTUBE_API_KEY":
        print("❌ Clé API YouTube non configurée")
        return False
    
    try:
        # Test simple avec l'API YouTube
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key={api_key}&maxResults=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Clé API YouTube valide")
            return True
        else:
            print(f"❌ Clé API YouTube invalide: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur test API YouTube: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test de l'infrastructure Docker pour le workflow YouTube")
    print("=" * 60)
    
    # Charger les variables d'environnement depuis .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Variables d'environnement chargées depuis .env")
    except ImportError:
        print("⚠️ python-dotenv non installé, utilisation des variables système")
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement .env: {e}")
    
    print()
    
    # Tests
    tests = [
        ("MongoDB", test_mongodb),
        ("HDFS", test_hdfs),
        ("Spark", test_spark),
        ("YouTube API", test_youtube_api)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
        print()
    
    # Résumé
    print("📊 Résumé des tests:")
    print("-" * 30)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:15} {status}")
    
    # Conclusion
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 Tous les tests sont passés! L'infrastructure est prête.")
        print("💡 Vous pouvez maintenant exécuter le workflow YouTube.")
    else:
        print("\n💥 Certains tests ont échoué. Vérifiez la configuration.")
        print("💡 Consultez les messages d'erreur ci-dessus.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
