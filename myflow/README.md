# 🚀 MyFlow - Mini-librairie d'Orchestration de Workflows

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/myflow/myflow)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

MyFlow est une mini-librairie d'orchestration de workflows inspirée d'Airflow, conçue avec les meilleurs design patterns pour l'apprentissage et la production.

## ✨ Fonctionnalités

- 🏗️ **Architecture Modulaire** - Design patterns avancés (Builder, Factory, Template Method, Singleton)
- 🔄 **Orchestration Flexible** - DAGs avec dépendances complexes
- 🚀 **Exécution Parallèle** - Support des exécutions simultanées
- 🛡️ **Robustesse** - Gestion d'erreurs, retry automatique, validation
- �� **Monitoring** - Logging détaillé et métriques d'exécution
- 🧪 **Tests Complets** - Tests unitaires et d'intégration
- 📚 **Documentation** - Exemples et guides détaillés

## 🏗️ Architecture

### Design Patterns Utilisés

| Pattern | Utilisation | Avantage |
|---------|-------------|----------|
| **Builder** | Construction des DAGs | Interface fluide et configurable |
| **Factory** | Création d'opérateurs | Extensibilité et découplage |
| **Template Method** | Exécution des tâches | Flux standardisé avec hooks |
| **Singleton** | Logger global | Instance unique et cohérente |
| **Strategy** | Exécuteurs | Interchangeabilité des algorithmes |

### Structure des Modules

```
myflow_lib/
├── core/                    # Classes fondamentales
│   ├── task.py             # Task (Template Method)
│   ├── dag.py              # DAG (Builder Pattern)
│   └── scheduler.py        # Planificateur
├── operators/              # Opérateurs (Factory Pattern)
│   ├── base_operator.py    # Classe de base
│   ├── python_operator.py  # Exécution Python
│   ├── bash_operator.py    # Commandes bash
│   ├── http_operator.py    # Requêtes HTTP
│   └── operator_factory.py # Factory
├── executors/              # Exécuteurs (Strategy Pattern)
│   ├── sequential_executor.py
│   └── parallel_executor.py
└── utils/                  # Utilitaires
    ├── logger.py           # Logger (Singleton)
    └── config.py           # Configuration
```

## 🚀 Installation

### Prérequis
- Python 3.7+
- pip

### Installation
```bash
# Cloner le repository
git clone https://github.com/myflow/myflow.git
cd myflow

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## 📖 Utilisation Rapide

### Exemple Simple
```python
from myflow_lib import DAG, PythonOperator, BashOperator

def hello_world():
    print("Hello World!")
    return True

# Construction fluide avec Builder Pattern
dag = (DAG.builder("hello_world")
       .set_description("Exemple simple")
       .build())

# Création des tâches
hello_task = PythonOperator("hello", "hello_world", hello_world)
echo_task = BashOperator("echo", "hello_world", "echo 'Hello from Bash!'")

# Ajout au DAG
dag.tasks["hello"] = hello_task
dag.tasks["echo"] = echo_task
dag.task_dependencies["hello"] = []
dag.task_dependencies["echo"] = ["hello"]

# Validation et exécution
if dag.validate():
    for task_id in dag.get_execution_order():
        dag.tasks[task_id].run()
```

### Exemple avec Factory Pattern
```python
from myflow_lib import OperatorFactory

# Création via Factory
python_task = OperatorFactory.create_operator(
    "python", "task1", "my_dag", 
    python_callable=my_function
)

bash_task = OperatorFactory.create_operator(
    "bash", "task2", "my_dag", 
    bash_command="echo hello"
)
```

## 🔧 Configuration

### Variables d'Environnement
```bash
export MYFLOW_MAX_WORKERS=4
export MYFLOW_LOG_LEVEL=INFO
export MYFLOW_TIMEOUT=300
export MYFLOW_DEFAULT_MAX_RETRIES=3
```

### Configuration Programmatique
```python
from myflow_lib.utils.config import Config

config = Config()
config.executor.max_workers = 8
config.logging.level = "DEBUG"
config.dag.default_max_retries = 5
```

## 🧪 Tests

### Exécution des Tests
```bash
# Tous les tests
python scripts/run_tests.py

# Tests unitaires uniquement
python -m unittest discover tests/unit

# Tests d'intégration
python -m unittest discover tests/integration
```

### Structure des Tests
```
tests/
├── unit/                   # Tests unitaires
│   ├── test_task.py       # Tests de la classe Task
│   ├── test_dag.py        # Tests de la classe DAG
│   └── test_operators.py  # Tests des opérateurs
├── integration/            # Tests d'intégration
│   ├── test_infrastructure.py
│   └── test_workflows.py
└── fixtures/              # Données de test
```

## 📚 Exemples

### Exemples Disponibles
```bash
# Exécuter tous les exemples
python scripts/run_examples.py

# Exemple simple
python examples/simple_example.py

# Vérifications d'infrastructure
python examples/infrastructure_example.py
```

### Exemple d'Infrastructure
```python
from myflow_lib import DAG, HttpOperator, BashOperator

# DAG de vérification d'infrastructure
dag = (DAG.builder("infrastructure_check")
       .set_description("Vérification de l'infrastructure")
       .add_tag("monitoring")
       .build())

# Tâches de vérification
docker_check = BashOperator("docker_check", "infrastructure_check", 
                           "docker --version")
http_check = HttpOperator("http_check", "infrastructure_check", 
                         "https://httpbin.org/status/200")

# Configuration des dépendances
dag.tasks["docker_check"] = docker_check
dag.tasks["http_check"] = http_check
dag.task_dependencies["docker_check"] = []
dag.task_dependencies["http_check"] = ["docker_check"]
```

## 📊 Monitoring et Logging

### Logging Configurable
```python
from myflow_lib.utils.logger import Logger

logger = Logger.get_instance()
logger.set_level("DEBUG")
logger.add_file_handler("myflow.log")
```

### Métriques d'Exécution
```python
# Informations sur les tâches
for task in dag.tasks.values():
    info = task.get_status_info()
    print(f"Tâche: {info['task_id']}")
    print(f"État: {info['state']}")
    print(f"Durée: {info['duration']:.2f}s")
```

## 🔄 Workflow d'Exécution

### 1. Construction
```python
dag = DAG.builder("workflow").build()
```

### 2. Validation
```python
if dag.validate():  # Vérification des cycles
    # DAG valide
```

### 3. Exécution
```python
# Template Method Pattern
for task in dag.get_ready_tasks():
    task.run()  # pre_execute() -> execute() -> post_execute()
```

### 4. Monitoring
```python
summary = dag.get_status_summary()
print(f"Succès: {summary['success']}")
print(f"Échecs: {summary['failed']}")
```

## 🎯 Cas d'Usage

### 1. **ETL Pipelines**
- Extraction de données
- Transformation
- Chargement

### 2. **Vérifications d'Infrastructure**
- Tests de connectivité
- Vérifications de services
- Monitoring

### 3. **Traitement de Données**
- Scripts Python
- Commandes système
- Appels d'API

### 4. **Automatisation**
- Déploiements
- Sauvegardes
- Maintenance

## 🤝 Contribution

### Développement
```bash
# Fork le repository
git clone https://github.com/your-username/myflow.git

# Créer une branche
git checkout -b feature/new-feature

# Installer en mode développement
pip install -e .

# Exécuter les tests
python scripts/run_tests.py
```

### Ajout d'Opérateurs
```python
from myflow_lib.operators.base_operator import BaseOperator
from myflow_lib.operators.operator_factory import OperatorFactory

class CustomOperator(BaseOperator):
    def execute(self) -> bool:
        # Implémentation personnalisée
        return True

# Enregistrer le nouvel opérateur
OperatorFactory.register_operator("custom", CustomOperator)
```

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- Inspiré par [Apache Airflow](https://airflow.apache.org/)
- Design patterns de [Gang of Four](https://en.wikipedia.org/wiki/Design_Patterns)
- Communauté Python

## 📞 Support

- 📧 Email: support@myflow.dev
- 🐛 Issues: [GitHub Issues](https://github.com/myflow/myflow/issues)
- 📖 Documentation: [Wiki](https://github.com/myflow/myflow/wiki)

---

**MyFlow** - Orchestration de workflows simplifiée et puissante 🚀
