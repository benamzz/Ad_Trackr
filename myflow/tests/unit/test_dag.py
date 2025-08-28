"""
Tests unitaires pour la classe DAG
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime

# Ajouter le chemin de la librairie
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'myflow_lib'))

from core.dag import DAG, DAGBuilder
from core.task import Task, TaskState
from operators.python_operator import PythonOperator


class TestDAG(unittest.TestCase):
    """Tests pour la classe DAG"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.dag = DAG("test_dag", "Test DAG")
        self.task1 = PythonOperator("task1", "test_dag", lambda: print("Task 1"))
        self.task2 = PythonOperator("task2", "test_dag", lambda: print("Task 2"))
        self.task3 = PythonOperator("task3", "test_dag", lambda: print("Task 3"))
    
    def test_dag_initialization(self):
        """Test de l'initialisation d'un DAG"""
        self.assertEqual(self.dag.dag_id, "test_dag")
        self.assertEqual(self.dag.description, "Test DAG")
        self.assertEqual(len(self.dag.tasks), 0)
        self.assertEqual(len(self.dag.task_dependencies), 0)
    
    def test_add_task(self):
        """Test de l'ajout de tâches"""
        self.dag.tasks["task1"] = self.task1
        self.dag.task_dependencies["task1"] = []
        
        self.assertIn("task1", self.dag.tasks)
        self.assertEqual(self.dag.tasks["task1"], self.task1)
    
    def test_add_dependency(self):
        """Test de l'ajout de dépendances"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.dag.task_dependencies["task1"] = []
        self.dag.task_dependencies["task2"] = []
        
        self.dag.add_dependency("task1", "task2")
        
        self.assertIn("task1", self.dag.task_dependencies["task2"])
        self.assertIn(self.task1, self.task2.dependencies)
        self.assertIn(self.task2, self.task1.dependents)
    
    def test_get_ready_tasks(self):
        """Test de l'obtention des tâches prêtes"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.dag.task_dependencies["task1"] = []
        self.dag.task_dependencies["task2"] = []
        
        ready_tasks = self.dag.get_ready_tasks()
        
        self.assertEqual(len(ready_tasks), 2)
        self.assertIn(self.task1, ready_tasks)
        self.assertIn(self.task2, ready_tasks)
    
    def test_get_execution_order(self):
        """Test de l'ordre d'exécution"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.dag.tasks["task3"] = self.task3
        self.dag.task_dependencies["task1"] = []
        self.dag.task_dependencies["task2"] = ["task1"]
        self.dag.task_dependencies["task3"] = ["task2"]
        
        order = self.dag.get_execution_order()
        
        self.assertEqual(order, ["task1", "task2", "task3"])
    
    def test_validate_dag(self):
        """Test de la validation du DAG"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.dag.task_dependencies["task1"] = []
        self.dag.task_dependencies["task2"] = ["task1"]
        
        self.assertTrue(self.dag.validate())
    
    def test_validate_dag_with_cycle(self):
        """Test de la validation d'un DAG avec cycle"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.dag.task_dependencies["task1"] = ["task2"]  # Cycle
        self.dag.task_dependencies["task2"] = ["task1"]  # Cycle
        
        self.assertFalse(self.dag.validate())
    
    def test_get_status_summary(self):
        """Test du résumé de statut"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.task1.state = TaskState.SUCCESS
        self.task2.state = TaskState.FAILED
        
        summary = self.dag.get_status_summary()
        
        self.assertEqual(summary["success"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["pending"], 0)
    
    def test_is_complete(self):
        """Test de la vérification de complétion"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.task1.state = TaskState.SUCCESS
        self.task2.state = TaskState.SUCCESS
        
        self.assertTrue(self.dag.is_complete())
        
        self.task2.state = TaskState.RUNNING
        self.assertFalse(self.dag.is_complete())
    
    def test_has_failures(self):
        """Test de la vérification d'échecs"""
        self.dag.tasks["task1"] = self.task1
        self.dag.tasks["task2"] = self.task2
        self.task1.state = TaskState.SUCCESS
        self.task2.state = TaskState.SUCCESS
        
        self.assertFalse(self.dag.has_failures())
        
        self.task2.state = TaskState.FAILED
        self.assertTrue(self.dag.has_failures())
    
    def test_reset(self):
        """Test de la réinitialisation"""
        self.dag.tasks["task1"] = self.task1
        self.task1.state = TaskState.SUCCESS
        self.task1.start_time = datetime.now()
        self.task1.end_time = datetime.now()
        
        self.dag.reset()
        
        self.assertEqual(self.task1.state, TaskState.PENDING)
        self.assertIsNone(self.task1.start_time)
        self.assertIsNone(self.task1.end_time)


class TestDAGBuilder(unittest.TestCase):
    """Tests pour la classe DAGBuilder"""
    
    def test_builder_initialization(self):
        """Test de l'initialisation du builder"""
        builder = DAGBuilder("test_dag")
        
        self.assertEqual(builder.dag_id, "test_dag")
        self.assertEqual(builder.description, "")
        self.assertEqual(len(builder.tasks), 0)
    
    def test_builder_fluent_interface(self):
        """Test de l'interface fluide du builder"""
        task1 = PythonOperator("task1", "test_dag", lambda: print("Task 1"))
        task2 = PythonOperator("task2", "test_dag", lambda: print("Task 2"))
        
        dag = (DAGBuilder("test_dag")
               .set_description("Test DAG")
               .add_task(task1)
               .add_task(task2)
               .add_dependency("task1", "task2")
               .build())
        
        self.assertEqual(dag.dag_id, "test_dag")
        self.assertEqual(dag.description, "Test DAG")
        self.assertEqual(len(dag.tasks), 2)
        self.assertIn("task1", dag.task_dependencies["task2"])
    
    def test_builder_with_tags(self):
        """Test du builder avec des tags"""
        dag = (DAGBuilder("test_dag")
               .add_tag("test")
               .add_tag("example")
               .build())
        
        self.assertIn("test", dag.tags)
        self.assertIn("example", dag.tags)


if __name__ == '__main__':
    unittest.main()
