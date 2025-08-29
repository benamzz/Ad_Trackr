"""
Script de test pour le workflow d'ingestion YouTube
Vérifie la faisabilité avant l'exécution complète
"""

import os
import sys
import subprocess
from pathlib import Path

# Ajouter le chemin de la librairie
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'myflow_lib'))

def check_docker_services():
    """Vérifier que les services Docker sont en cours d'exécution"""
    print("🐳 Vérification des services Docker...")
    
    required_containers = [
        "datalake-mongo",
        "datalake-namenode", 
        "datalake-spark-master"
    ]
    
    all_running = True
    
    for container in required_containers:
        try:
            result = subprocess.run(
                ["docker", "inspect", container],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  ✅ {container} en cours d'exécution")
            else:
                print(f"  ❌ {container} non trouvé ou arrêté")
                all_running = False
                
        except Exception as e:
            print(f"  ❌ Erreur lors de la vérification de {container}: {e}")
            all_running = False
    
    return all_running


def check_environment_variables():
    """Vérifier les variables d'environnement"""
    print("\n🔧 Vérification des variables d'environnement...")
    
    # Charger .env si disponible
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("  ✅ Fichier .env chargé")
        except ImportError:
            print("  ⚠️ python-dotenv non installé")
        except Exception as e:
            print(f"  ⚠️ Erreur lors du chargement .env: {e}")
    
    required_vars = {
        'YOUTUBE_API_KEY': 'Clé API YouTube',
        'MONGO_URI': 'URI MongoDB',
        'HDFS_NAMENODE_URL': 'URL HDFS NameNode',
        'SPARK_MASTER_URL': 'URL Spark Master'
    }
    
    all_present = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Masquer les clés sensibles
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: {description} manquante")
            all_present = False
    
    return all_present


def check_scripts_availability():
    """Vérifier que les scripts sont disponibles"""
    print("\n📄 Vérification des scripts...")
    
    project_root = Path(__file__).parent.parent.parent
    required_scripts = [
        'youtube_extractor_to_mongo.py',
        'run_etl_spark.py',
        'influenceurs_youtube_etl.py'
    ]
    
    all_available = True
    
    for script in required_scripts:
        script_path = project_root / script
        if script_path.exists():
            print(f"  ✅ {script} trouvé")
        else:
            print(f"  ❌ {script} non trouvé")
            all_available = False
    
    return all_available


def test_mongodb_connection():
    """Tester la connexion MongoDB"""
    print("\n🗄️ Test de connexion MongoDB...")
    
    try:
        import pymongo
        
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        
        print("  ✅ Connexion MongoDB réussie")
        return True
        
    except ImportError:
        print("  ❌ pymongo non installé")
        return False
    except Exception as e:
        print(f"  ❌ Erreur de connexion MongoDB: {e}")
        return False


def test_hdfs_connection():
    """Tester la connexion HDFS"""
    print("\n💾 Test de connexion HDFS...")
    
    try:
        result = subprocess.run(
            ["docker", "exec", "datalake-namenode", "hdfs", "dfsadmin", "-report"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✅ Connexion HDFS réussie")
            return True
        else:
            print(f"  ❌ Erreur HDFS: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ❌ Timeout lors de la connexion HDFS")
        return False
    except Exception as e:
        print(f"  ❌ Erreur lors du test HDFS: {e}")
        return False


def test_youtube_api():
    """Tester l'API YouTube"""
    print("\n🎬 Test de l'API YouTube...")
    
    try:
        import requests
        
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            print("  ❌ YOUTUBE_API_KEY non définie")
            return False
        
        # Test simple avec une requête
        url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'key': api_key,
            'part': 'snippet',
            'q': 'test',
            'maxResults': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ API YouTube accessible")
            return True
        else:
            print(f"  ❌ Erreur API YouTube: {response.status_code}")
            return False
            
    except ImportError:
        print("  ❌ requests non installé")
        return False
    except Exception as e:
        print(f"  ❌ Erreur lors du test API YouTube: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🧪 Test de Faisabilité - Workflow d'Ingestion YouTube")
    print("=" * 60)
    
    tests = [
        ("Variables d'environnement", check_environment_variables),
        ("Scripts disponibles", check_scripts_availability),
        ("Connexion MongoDB", test_mongodb_connection),
        ("Connexion HDFS", test_hdfs_connection),
        ("API YouTube", test_youtube_api)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ❌ Erreur lors du test {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print("\n📊 Résumé des tests:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés! Le workflow est faisable.")
        print("💡 Vous pouvez maintenant exécuter:")
        print("   python examples/youtube_ingestion_workflow.py")
        return 0
    else:
        print("\n💥 Certains tests ont échoué. Vérifiez la configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
