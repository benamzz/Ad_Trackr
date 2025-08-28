"""
Exemple simple d'utilisation de MyFlow
"""

from myflow_lib import DAG, PythonOperator, BashOperator, HttpOperator


def hello_world():
    """Fonction simple pour l'exemple"""
    print("Hello World from MyFlow!")
    return True


def main():
    """Fonction principale"""
    print("🚀 Exemple simple de MyFlow")
    print("=" * 40)
    
    # Créer un DAG avec le Builder Pattern
    dag = (DAG.builder("simple_example")
           .set_description("Exemple simple d'utilisation de MyFlow")
           .add_tag("example")
           .add_tag("simple")
           .build())
    
    # Créer les tâches
    hello_task = PythonOperator("hello", "simple_example", hello_world)
    echo_task = BashOperator("echo", "simple_example", "echo 'Hello from Bash!'")
    http_task = HttpOperator("http_check", "simple_example", "https://httpbin.org/status/200")
    
    # Ajouter les tâches au DAG
    dag.tasks["hello"] = hello_task
    dag.tasks["echo"] = echo_task
    dag.tasks["http_check"] = http_task
    dag.task_dependencies["hello"] = []
    dag.task_dependencies["echo"] = []
    dag.task_dependencies["http_check"] = []
    
    # Vérifier le DAG
    if not dag.validate():
        print("❌ DAG invalide!")
        return
    
    print("✅ DAG validé avec succès")
    print(f"📋 Tâches: {list(dag.tasks.keys())}")
    print(f"🔄 Ordre d'exécution: {' -> '.join(dag.get_execution_order())}")
    
    # Exécuter les tâches
    print("\n🔄 Exécution des tâches...")
    for task_id in dag.get_execution_order():
        task = dag.tasks[task_id]
        print(f"\n📝 Exécution de {task_id}...")
        success = task.run()
        status = "✅ Succès" if success else "❌ Échec"
        print(f"   {status}")
    
    # Résumé final
    print("\n📊 Résumé final:")
    summary = dag.get_status_summary()
    for state, count in summary.items():
        if count > 0:
            print(f"   {state.capitalize()}: {count}")


if __name__ == "__main__":
    main()
