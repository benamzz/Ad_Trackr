"""
Exemple d'utilisation de MyFlow pour les vérifications d'infrastructure
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'myflow_lib'))

from core.dag import DAG
from operators.python_operator import PythonOperator
from operators.bash_operator import BashOperator
from operators.http_operator import HttpOperator


def check_docker():
    """Vérifier Docker"""
    import subprocess
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker est installé")
            return True
        else:
            print("❌ Docker n'est pas installé")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification Docker: {e}")
        return False


def check_python():
    """Vérifier Python"""
    import sys
    print(f"✅ Python {sys.version} est disponible")
    return True


def main():
    """Fonction principale"""
    print("🔍 Exemple de vérification d'infrastructure avec MyFlow")
    print("=" * 60)
    
    # Créer un DAG avec le Builder Pattern
    dag = (DAG.builder("infrastructure_check")
           .set_description("Vérification de l'infrastructure")
           .add_tag("infrastructure")
           .add_tag("monitoring")
           .build())
    
    # Créer les tâches de vérification
    docker_task = PythonOperator("check_docker", "infrastructure_check", check_docker)
    python_task = PythonOperator("check_python", "infrastructure_check", check_python)
    system_task = BashOperator("check_system", "infrastructure_check", "uname -a")
    http_task = HttpOperator("check_http", "infrastructure_check", "https://httpbin.org/status/200")
    
    # Ajouter les tâches au DAG
    dag.tasks["check_docker"] = docker_task
    dag.tasks["check_python"] = python_task
    dag.tasks["check_system"] = system_task
    dag.tasks["check_http"] = http_task
    
    # Définir les dépendances
    dag.task_dependencies["check_docker"] = []
    dag.task_dependencies["check_python"] = []
    dag.task_dependencies["check_system"] = ["check_python"]
    dag.task_dependencies["check_http"] = ["check_system"]
    
    # Vérifier le DAG
    if not dag.validate():
        print("❌ DAG invalide!")
        return
    
    print("✅ DAG validé avec succès")
    print(f"📋 Tâches: {list(dag.tasks.keys())}")
    print(f"🔄 Ordre d'exécution: {' -> '.join(dag.get_execution_order())}")
    
    # Exécuter les tâches
    print("\n🔄 Exécution des vérifications...")
    for task_id in dag.get_execution_order():
        task = dag.tasks[task_id]
        print(f"\n📝 Vérification: {task_id}...")
        success = task.run()
        status = "✅ Succès" if success else "❌ Échec"
        print(f"   {status}")
    
    # Résumé final
    print("\n📊 Résumé des vérifications:")
    summary = dag.get_status_summary()
    for state, count in summary.items():
        if count > 0:
            print(f"   {state.capitalize()}: {count}")
    
    # Informations détaillées
    print("\n📋 Informations détaillées:")
    for task_id, task in dag.tasks.items():
        info = task.get_status_info()
        print(f"   {task_id}: {info['state']} (durée: {info['duration']:.2f}s)")


if __name__ == "__main__":
    main()
