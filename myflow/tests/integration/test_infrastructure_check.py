"""
Tests d'intégration pour les vérifications d'infrastructure
"""

import unittest
import sys
import os

# Ajouter le chemin de la librairie
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'myflow_lib'))

from core.dag import DAG
from operators.python_operator import PythonOperator
from operators.bash_operator import BashOperator
from operators.http_operator import HttpOperator


class TestInfrastructureCheck(unittest.TestCase):
    """Tests d'intégration pour les vérifications d'infrastructure"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.dag = DAG("infrastructure_test", "Test d'infrastructure")
    
    def test_docker_check_task(self):
        """Test de la tâche de vérification Docker"""
        def check_docker():
            import subprocess
            try:
                result = subprocess.run(["docker", "--version"], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except:
                return False
        
        task = PythonOperator("check_docker", "infrastructure_test", check_docker)
        self.dag.tasks["check_docker"] = task
        self.dag.task_dependencies["check_docker"] = []
        
        result = task.run()
        # Le test peut réussir ou échouer selon l'environnement
        self.assertIsInstance(result, bool)
    
    def test_http_check_task(self):
        """Test de la tâche de vérification HTTP"""
        task = HttpOperator(
            "check_http", 
            "infrastructure_test", 
            "https://httpbin.org/status/200",
            expected_status_code=200
        )
        self.dag.tasks["check_http"] = task
        self.dag.task_dependencies["check_http"] = []
        
        result = task.run()
        # Le test peut réussir ou échouer selon la connectivité
        self.assertIsInstance(result, bool)
    
    def test_bash_check_task(self):
        """Test de la tâche de vérification bash"""
        task = BashOperator("check_bash", "infrastructure_test", "echo 'Hello World'")
        self.dag.tasks["check_bash"] = task
        self.dag.task_dependencies["check_bash"] = []
        
        result = task.run()
        self.assertTrue(result)  # Cette commande devrait toujours réussir
    
    def test_dag_with_multiple_checks(self):
        """Test d'un DAG avec plusieurs vérifications"""
        # Tâche de vérification bash (toujours réussit)
        bash_task = BashOperator("bash_check", "infrastructure_test", "echo 'test'")
        
        # Tâche de vérification Python
        def python_check():
            return True
        
        python_task = PythonOperator("python_check", "infrastructure_test", python_check)
        
        # Ajouter les tâches au DAG
        self.dag.tasks["bash_check"] = bash_task
        self.dag.tasks["python_check"] = python_task
        self.dag.task_dependencies["bash_check"] = []
        self.dag.task_dependencies["python_check"] = ["bash_check"]
        
        # Vérifier la structure du DAG
        self.assertEqual(len(self.dag.tasks), 2)
        self.assertIn("bash_check", self.dag.task_dependencies["python_check"])
        
        # Vérifier l'ordre d'exécution
        order = self.dag.get_execution_order()
        self.assertEqual(order, ["bash_check", "python_check"])
        
        # Vérifier la validation
        self.assertTrue(self.dag.validate())


if __name__ == '__main__':
    unittest.main()
