"""
Workflow d'ingestion YouTube avec MyFlow
Pipeline complet: YouTube API -> MongoDB -> Spark -> HDFS
"""

import os
import sys
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'myflow_lib'))

from myflow_lib import DAG
from myflow_lib.operators.youtube_operator import (
    YouTubeExtractorOperator, 
    MongoDBHealthCheckOperator,
    HDFSHealthCheckOperator
)
from myflow_lib.operators.python_operator import PythonOperator


def check_environment():
    """Vérifier que l'environnement est prêt"""
    required_vars = ['YOUTUBE_API_KEY', 'MONGO_URI']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environnement configuré correctement")
    return True


def run_spark_etl():
    """Appeler le script run_etl_spark.py pour exécuter l'ETL"""
    try:
        script_path = "/app/run_etl_spark.py"
        if not os.path.exists(script_path):
            print(f"❌ Script ETL introuvable: {script_path}")
            return False
        
        print("⚡ Exécution du script ETL Spark...")
        result = subprocess.run(
            ["python", script_path],
            check=True,
            text=True
        )
        print("✅ ETL Spark exécuté avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution du script ETL Spark: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def create_youtube_ingestion_dag():
    """Créer le DAG d'ingestion YouTube"""
    
    # Créer le DAG avec le Builder Pattern
    dag = (DAG.builder("youtube_ingestion_pipeline")
           .set_description("Pipeline d'ingestion YouTube: API -> MongoDB -> Spark -> HDFS")
           .add_tag("youtube")
           .add_tag("ingestion")
           .add_tag("etl")
           .build())
    
    # 1. Vérification de l'environnement
    env_check = PythonOperator(
        "check_environment",
        "youtube_ingestion_pipeline",
        check_environment
    )
    
    # 2. Vérification de la santé des services
    mongo_health = MongoDBHealthCheckOperator(
        "mongo_health_check",
        "youtube_ingestion_pipeline"
    )
    
    hdfs_health = HDFSHealthCheckOperator(
        "hdfs_health_check", 
        "youtube_ingestion_pipeline"
    )
    
    # 3. Extraction YouTube vers MongoDB
    youtube_extraction = YouTubeExtractorOperator(
        "youtube_extraction",
        "youtube_ingestion_pipeline"
    )
    
    # 4. ETL Spark (MongoDB vers HDFS) via run_etl_spark.py
    spark_etl = PythonOperator(
        "spark_etl",
        "youtube_ingestion_pipeline",
        run_spark_etl
    )
    
    # Ajouter les tâches au DAG
    dag.tasks["check_environment"] = env_check
    dag.tasks["mongo_health_check"] = mongo_health
    dag.tasks["hdfs_health_check"] = hdfs_health
    dag.tasks["youtube_extraction"] = youtube_extraction
    dag.tasks["spark_etl"] = spark_etl
    
    # Définir les dépendances
    dag.task_dependencies["check_environment"] = []
    dag.task_dependencies["mongo_health_check"] = ["check_environment"]
    dag.task_dependencies["hdfs_health_check"] = ["check_environment"]
    dag.task_dependencies["youtube_extraction"] = ["mongo_health_check"]
    dag.task_dependencies["spark_etl"] = ["youtube_extraction", "hdfs_health_check"]
    
    return dag


def main():
    """Fonction principale"""
    print("🎬 Workflow d'Ingestion YouTube avec MyFlow")
    print("=" * 60)
    
    # Charger les variables d'environnement depuis .env
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        print("✅ Variables d'environnement chargées depuis .env")
    except ImportError:
        print("⚠️ python-dotenv non installé, utilisation des variables système")
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement .env: {e}")
    
    # Créer le DAG
    dag = create_youtube_ingestion_dag()
    
    # Valider le DAG
    if not dag.validate():
        print("❌ DAG invalide!")
        return
    
    print("✅ DAG validé avec succès")
    print(f"📋 Tâches: {list(dag.tasks.keys())}")
    print(f"🔄 Ordre d'exécution: {' -> '.join(dag.get_execution_order())}")
    
    # Exécuter le workflow
    print("\n🔄 Exécution du workflow d'ingestion...")
    
    for task_id in dag.get_execution_order():
        task = dag.tasks[task_id]
        print(f"\n📝 Exécution de {task_id}...")
        
        success = task.run()
        status = "✅ Succès" if success else "❌ Échec"
        print(f"   {status}")
        
        if not success:
            print(f"❌ Workflow arrêté à cause de l'échec de {task_id}")
            break
    
    # Résumé final
    print("\n📊 Résumé du workflow:")
    summary = dag.get_status_summary()
    for state, count in summary.items():
        if count > 0:
            print(f"   {state.capitalize()}: {count}")
    
    # Vérifier le succès global
    if dag.is_complete() and not dag.has_failures():
        print("\n🎉 Workflow d'ingestion YouTube terminé avec succès!")
    else:
        print("\n💥 Workflow d'ingestion YouTube a échoué!")


if __name__ == "__main__":
    main()
