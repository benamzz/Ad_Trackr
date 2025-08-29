"""
Tests unitaires pour la classe Task
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Ajouter le chemin de la librairie
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'myflow_lib'))

from core.task import Task, TaskState
from utils.logger import Logger


class MockTask(Task):
    """Tâche mock pour les tests"""
    
    def __init__(self, task_id: str, dag_id: str, should_succeed: bool = True, **kwargs):
        super().__init__(task_id, dag_id, **kwargs)
        self.should_succeed = should_succeed
        self.execute_called = False
    
    def execute(self) -> bool:
        """Implémentation mock de execute"""
        self.execute_called = True
        return self.should_succeed


class TestTask(unittest.TestCase):
    """Tests pour la classe Task"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.task = MockTask("test_task", "test_dag")
    
    def test_task_initialization(self):
        """Test de l'initialisation d'une tâche"""
        self.assertEqual(self.task.task_id, "test_task")
        self.assertEqual(self.task.dag_id, "test_dag")
        self.assertEqual(self.task.state, TaskState.PENDING)
        self.assertEqual(len(self.task.dependencies), 0)
        self.assertEqual(len(self.task.dependents), 0)
        self.assertIsNone(self.task.start_time)
        self.assertIsNone(self.task.end_time)
    
    def test_add_dependency(self):
        """Test de l'ajout de dépendances"""
        dependency = MockTask("dependency", "test_dag")
        self.task.add_dependency(dependency)
        
        self.assertIn(dependency, self.task.dependencies)
        self.assertIn(self.task, dependency.dependents)
    
    def test_can_run_without_dependencies(self):
        """Test can_run sans dépendances"""
        self.assertTrue(self.task.can_run())
    
    def test_can_run_with_successful_dependencies(self):
        """Test can_run avec dépendances réussies"""
        dependency = MockTask("dependency", "test_dag", should_succeed=True)
        dependency.state = TaskState.SUCCESS
        self.task.add_dependency(dependency)
        
        self.assertTrue(self.task.can_run())
    
    def test_can_run_with_failed_dependencies(self):
        """Test can_run avec dépendances échouées"""
        dependency = MockTask("dependency", "test_dag", should_succeed=True)
        dependency.state = TaskState.FAILED
        self.task.add_dependency(dependency)
        
        self.assertFalse(self.task.can_run())
    
    def test_should_skip_with_failed_dependencies(self):
        """Test should_skip avec dépendances échouées"""
        dependency = MockTask("dependency", "test_dag", should_succeed=True)
        dependency.state = TaskState.FAILED
        self.task.add_dependency(dependency)
        
        self.assertTrue(self.task.should_skip())
    
    def test_should_skip_without_failed_dependencies(self):
        """Test should_skip sans dépendances échouées"""
        dependency = MockTask("dependency", "test_dag", should_succeed=True)
        dependency.state = TaskState.SUCCESS
        self.task.add_dependency(dependency)
        
        self.assertFalse(self.task.should_skip())
    
    def test_successful_execution(self):
        """Test d'exécution réussie"""
        self.task.should_succeed = True
        result = self.task.run()
        
        self.assertTrue(result)
        self.assertEqual(self.task.state, TaskState.SUCCESS)
        self.assertTrue(self.task.execute_called)
        self.assertIsNotNone(self.task.start_time)
        self.assertIsNotNone(self.task.end_time)
    
    def test_failed_execution(self):
        """Test d'exécution échouée"""
        self.task.should_succeed = False
        result = self.task.run()
        
        self.assertFalse(result)
        self.assertEqual(self.task.state, TaskState.FAILED)
        self.assertTrue(self.task.execute_called)
        self.assertIsNotNone(self.task.start_time)
        self.assertIsNotNone(self.task.end_time)
    
    def test_retry_mechanism(self):
        """Test du mécanisme de retry"""
        task = MockTask("test_task", "test_dag", should_succeed=False, max_retries=2)
        result = task.run()
        
        self.assertFalse(result)
        self.assertEqual(task.state, TaskState.FAILED)
        self.assertEqual(task.retry_count, 2)  # 2 tentatives + 1 initiale
    
    def test_skip_on_dependency_failure(self):
        """Test du skip en cas d'échec de dépendance"""
        dependency = MockTask("dependency", "test_dag", should_succeed=True)
        dependency.state = TaskState.FAILED
        self.task.add_dependency(dependency)
        
        result = self.task.run()
        
        self.assertTrue(result)  # Skip est considéré comme un succès
        self.assertEqual(self.task.state, TaskState.SKIPPED)
        self.assertFalse(self.task.execute_called)
    
    def test_get_duration(self):
        """Test du calcul de durée"""
        self.task.should_succeed = True
        self.task.run()
        
        duration = self.task.get_duration()
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)
    
    def test_get_status_info(self):
        """Test de l'obtention des informations de statut"""
        self.task.should_succeed = True
        self.task.run()
        
        status_info = self.task.get_status_info()
        
        self.assertEqual(status_info['task_id'], "test_task")
        self.assertEqual(status_info['dag_id'], "test_dag")
        self.assertEqual(status_info['state'], TaskState.SUCCESS.value)
        self.assertIsNotNone(status_info['start_time'])
        self.assertIsNotNone(status_info['end_time'])
        self.assertIsNotNone(status_info['duration'])


if __name__ == '__main__':
    unittest.main()
