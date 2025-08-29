from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import subprocess
import os

# Configuration par défaut du DAG
default_args = {
    'owner': 'datalake-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Définition du DAG
dag = DAG(
    'youtube_data_pipeline',
    default_args=default_args,
    description='Pipeline d\'extraction des données YouTube vers MongoDB',
    schedule_interval="@monthly",  # Exécution mensuelle   
    catchup=False,
    tags=['youtube', 'api', 'mongodb', 'datalake'],
)

def extract_youtube_data():
    """
    Fonction pour exécuter l'extraction des données YouTube
    """
    import sys
    sys.path.append('/opt/airflow/data')
    
    try:
        # Import et exécution du script d'extraction
        from youtube_extractor_to_mongo import main as extract_main
        extract_main()
        print("✅ Extraction YouTube terminée avec succès")
        return "success"
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction YouTube: {str(e)}")
        raise

def check_mongo_connection():
    """
    Vérifier la connexion à MongoDB
    """
    from pymongo import MongoClient
    try:
        client = MongoClient('mongodb://admin:password123@mongo:27017/')
        # Test de connexion
        client.admin.command('ping')
        print("✅ Connexion MongoDB OK")
        client.close()
        return "success"
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {str(e)}")
        raise

def prepare_jupyter_environment():
    """
    Préparer l'environnement Jupyter en installant les dépendances nécessaires
    """
    try:
        # Installer papermill et pymongo dans le conteneur jupyter
        packages = ['papermill', 'pymongo']
        
        for package in packages:
            install_cmd = [
                'docker', 'exec', 'datalake-jupyter', 
                'pip', 'install', package
            ]
            
            print(f"📦 Installation de {package} dans le conteneur Jupyter...")
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {package} installé avec succès")
            else:
                print(f"⚠️ {package} peut-être déjà installé: {result.stderr}")
        
        return "prepared"
        
    except Exception as e:
        print(f"❌ Erreur lors de la préparation: {str(e)}")
        # Ne pas faire échouer la pipeline pour cette étape
        return "prepared"

def execute_jupyter_notebook():
    """
    Exécuter le notebook Jupyter d'analyse dans le conteneur
    """
    try:
        # Commande pour exécuter le notebook via papermill dans le conteneur jupyter
        cmd = [
            'docker', 'exec', 'datalake-jupyter', 
            'python', '-m', 'papermill',
            '/home/jovyan/work/notebooks/Youtube_ETL_Pipeline.ipynb',
            '/home/jovyan/work/notebooks/Youtube_ETL_Pipeline_executed.ipynb',
            '--log-output'
        ]
        
        print("🚀 Début de l'exécution du notebook Jupyter...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ Notebook Jupyter exécuté avec succès")
            print("📊 Analyse terminée et données sauvegardées dans HDFS")
            return "success"
        else:
            print(f"❌ Erreur lors de l'exécution du notebook: {result.stderr}")
            raise Exception(f"Notebook execution failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout lors de l'exécution du notebook (30 min)")
        raise Exception("Notebook execution timeout")
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du notebook: {str(e)}")
        raise

def trigger_spark_analysis():
    """
    Déclencher l'analyse Spark via une notification
    (L'analyse sera faite manuellement dans Jupyter)
    """
    print("🚀 Données extraites dans MongoDB")
    print("📊 Prêt pour l'analyse Spark dans Jupyter Notebook")
    print("🔗 Connectez-vous à Jupyter: http://localhost:8888")
    return "ready_for_analysis"

# Tâche 1: Vérification de la connexion MongoDB
check_mongo_task = PythonOperator(
    task_id='check_mongo_connection',
    python_callable=check_mongo_connection,
    dag=dag,
)

# Tâche 2: Préparation de l'environnement Jupyter
prepare_env_task = PythonOperator(
    task_id='prepare_jupyter_environment',
    python_callable=prepare_jupyter_environment,
    dag=dag,
)

# Tâche 3: Extraction des données YouTube
extract_data_task = PythonOperator(
    task_id='extract_youtube_data',
    python_callable=extract_youtube_data,
    dag=dag,
)

# Tâche 4: Exécution du notebook Jupyter d'analyse
execute_notebook_task = PythonOperator(
    task_id='execute_jupyter_notebook',
    python_callable=execute_jupyter_notebook,
    dag=dag,
)

# Tâche 5: Notification finale
notify_spark_task = PythonOperator(
    task_id='notify_pipeline_complete',
    python_callable=trigger_spark_analysis,
    dag=dag,
)

# Définition des dépendances
check_mongo_task >> prepare_env_task >> extract_data_task >> execute_notebook_task >> notify_spark_task
