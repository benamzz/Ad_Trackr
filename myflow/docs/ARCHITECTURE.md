# 🏗️ Architecture de MyFlow

## 📋 Vue d'ensemble

MyFlow est une mini-librairie d'orchestration de workflows conçue avec les meilleurs design patterns pour assurer la maintenabilité, l'extensibilité et la robustesse.

## 🎯 Design Patterns Utilisés

### 1. **Builder Pattern** - Construction des DAGs
```python
dag = (DAG.builder("my_dag")
       .set_description("Mon DAG")
       .add_task(task1)
       .add_dependency("task1", "task2")
       .build())
```

### 2. **Factory Pattern** - Création d'opérateurs
```python
operator = OperatorFactory.create_operator("python", "task_id", "dag_id", 
                                          python_callable=my_function)
```

### 3. **Template Method Pattern** - Exécution des tâches
```python
class Task(ABC):
    def run(self):  # Template method
        self.pre_execute()
        success = self.execute()  # Hook method
        self.post_execute(success)
```

### 4. **Singleton Pattern** - Logger
```python
logger = Logger.get_instance()  # Une seule instance globale
```

### 5. **Strategy Pattern** - Exécuteurs
```python
executor = SequentialExecutor()  # ou ParallelExecutor()
```

## 📁 Structure des Modules

```
myflow_lib/
├── __init__.py              # Point d'entrée principal
├── core/                    # Classes fondamentales
│   ├── __init__.py
│   ├── task.py             # Classe Task (Template Method)
│   ├── dag.py              # Classe DAG (Builder Pattern)
│   └── scheduler.py        # Planificateur
├── operators/              # Opérateurs (Factory Pattern)
│   ├── __init__.py
│   ├── base_operator.py    # Classe de base
│   ├── python_operator.py  # Opérateur Python
│   ├── bash_operator.py    # Opérateur Bash
│   ├── http_operator.py    # Opérateur HTTP
│   └── operator_factory.py # Factory des opérateurs
├── executors/              # Exécuteurs (Strategy Pattern)
│   ├── __init__.py
│   ├── sequential_executor.py
│   └── parallel_executor.py
└── utils/                  # Utilitaires
    ├── __init__.py
    ├── logger.py           # Logger (Singleton)
    └── config.py           # Configuration
```

## 🔄 Flux d'Exécution

### 1. **Construction du DAG**
```python
# Builder Pattern
dag = DAG.builder("my_dag").set_description("...").build()

# Factory Pattern
task = OperatorFactory.create_operator("python", "task1", "my_dag", 
                                      python_callable=my_function)
```

### 2. **Validation**
```python
if dag.validate():  # Vérification des cycles
    # DAG valide
```

### 3. **Exécution**
```python
# Template Method Pattern
for task in dag.get_ready_tasks():
    task.run()  # pre_execute() -> execute() -> post_execute()
```

## �� Arbre de Décision

### Niveau 1: Construction
```
DAGBuilder → Validation → DAG
```

### Niveau 2: Exécution
```
Task.run() → pre_execute() → execute() → post_execute()
```

### Niveau 3: Gestion des États
```
PENDING → RUNNING → SUCCESS/FAILED/SKIPPED/RETRY
```

## 🎨 Avantages de cette Architecture

### 1. **Extensibilité**
- Nouveaux opérateurs via Factory Pattern
- Nouveaux exécuteurs via Strategy Pattern
- Configuration flexible via Config

### 2. **Maintenabilité**
- Séparation claire des responsabilités
- Code modulaire et testable
- Documentation intégrée

### 3. **Robustesse**
- Gestion d'erreurs à tous les niveaux
- Mécanisme de retry intégré
- Validation des DAGs

### 4. **Performance**
- Exécution parallèle possible
- Gestion des ressources
- Optimisations configurables

## �� Configuration

### Variables d'Environnement
```bash
export MYFLOW_MAX_WORKERS=4
export MYFLOW_LOG_LEVEL=INFO
export MYFLOW_TIMEOUT=300
```

### Configuration Programmatique
```python
from myflow_lib.utils.config import Config

config = Config()
config.executor.max_workers = 8
config.logging.level = "DEBUG"
```

## 🧪 Tests

### Structure des Tests
```
tests/
├── unit/                   # Tests unitaires
│   ├── test_task.py
│   ├── test_dag.py
│   └── test_operators.py
├── integration/            # Tests d'intégration
│   ├── test_infrastructure.py
│   └── test_workflows.py
└── fixtures/              # Données de test
```

### Exécution des Tests
```bash
python scripts/run_tests.py
```

## 📚 Exemples

### Exemples Disponibles
```
examples/
├── simple_example.py       # Exemple basique
├── infrastructure_example.py # Vérifications d'infrastructure
└── advanced_example.py     # Exemple avancé
```

### Exécution des Exemples
```bash
python scripts/run_examples.py
```

## 🚀 Utilisation

### Import Simple
```python
from myflow_lib import DAG, PythonOperator, BashOperator
```

### Construction Fluide
```python
dag = (DAG.builder("my_workflow")
       .set_description("Mon workflow")
       .add_task(PythonOperator("task1", "my_workflow", my_function))
       .add_task(BashOperator("task2", "my_workflow", "echo hello"))
       .add_dependency("task1", "task2")
       .build())
```

### Exécution
```python
for task in dag.get_execution_order():
    task.run()
```

Cette architecture garantit un code propre, maintenable et extensible, tout en offrant une API intuitive et puissante pour l'orchestration de workflows.
