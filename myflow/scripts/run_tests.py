"""
Script pour exécuter tous les tests
"""

import unittest
import sys
import os

# Ajouter le chemin de la librairie
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'myflow_lib'))

def run_unit_tests():
    """Exécuter les tests unitaires"""
    print("🧪 Exécution des tests unitaires...")
    print("=" * 50)
    
    # Découvrir et exécuter les tests unitaires
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Exécuter les tests d'intégration"""
    print("\n🔗 Exécution des tests d'intégration...")
    print("=" * 50)
    
    # Découvrir et exécuter les tests d'intégration
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'integration')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Fonction principale"""
    print("🚀 Exécution des tests MyFlow")
    print("=" * 60)
    
    # Exécuter les tests unitaires
    unit_success = run_unit_tests()
    
    # Exécuter les tests d'intégration
    integration_success = run_integration_tests()
    
    # Résumé final
    print("\n📊 Résumé des tests:")
    print("=" * 30)
    print(f"Tests unitaires: {'✅ Réussis' if unit_success else '❌ Échoués'}")
    print(f"Tests d'intégration: {'✅ Réussis' if integration_success else '❌ Échoués'}")
    
    if unit_success and integration_success:
        print("\n🎉 Tous les tests sont passés avec succès!")
        return 0
    else:
        print("\n💥 Certains tests ont échoué!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
