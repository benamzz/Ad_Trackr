"""
Script pour exécuter les exemples
"""

import sys
import os
import importlib.util

def run_example(example_name):
    """Exécuter un exemple spécifique"""
    example_path = os.path.join(os.path.dirname(__file__), '..', 'examples', f'{example_name}.py')
    
    if not os.path.exists(example_path):
        print(f"❌ Exemple {example_name} non trouvé")
        return False
    
    print(f"🚀 Exécution de l'exemple: {example_name}")
    print("=" * 50)
    
    try:
        # Charger et exécuter le module
        spec = importlib.util.spec_from_file_location(example_name, example_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Exécuter la fonction main si elle existe
        if hasattr(module, 'main'):
            module.main()
            print(f"✅ Exemple {example_name} exécuté avec succès")
            return True
        else:
            print(f"⚠️  Exemple {example_name} n'a pas de fonction main")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {example_name}: {e}")
        return False


def main():
    """Fonction principale"""
    print("🎯 Exécution des exemples MyFlow")
    print("=" * 40)
    
    # Liste des exemples disponibles
    examples = ['simple_example', 'infrastructure_example']
    
    results = {}
    
    for example in examples:
        results[example] = run_example(example)
        print()  # Ligne vide entre les exemples
    
    # Résumé final
    print("📊 Résumé des exemples:")
    print("=" * 30)
    for example, success in results.items():
        status = "✅ Réussi" if success else "❌ Échoué"
        print(f"{example}: {status}")
    
    successful = sum(results.values())
    total = len(results)
    
    if successful == total:
        print(f"\n🎉 Tous les exemples ({successful}/{total}) ont été exécutés avec succès!")
        return 0
    else:
        print(f"\n💥 {total - successful}/{total} exemples ont échoué!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
