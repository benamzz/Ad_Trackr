#!/bin/bash

echo "🎬 Démarrage du Workflow d'Ingestion YouTube"
echo "============================================="

# Aller dans le répertoire racine du projet
cd "$(dirname "$0")/../.."

echo "📁 Répertoire de travail: $(pwd)"

# Vérifier si Docker est en cours d'exécution
# if ! docker info > /dev/null 2>&1; then
#     echo "❌ Docker n'est pas en cours d'exécution"
#     echo "💡 Démarrez Docker Desktop et réessayez"
#     exit 1
# fi

# echo "✅ Docker est en cours d'exécution"

# Démarrer l'infrastructure
# echo "🐳 Démarrage de l'infrastructure Docker..."
# docker-compose up -d

# Attendre que les services soient prêts
# echo "⏳ Attente du démarrage des services..."
# sleep 30

# Vérifier l'état des services
# echo "🔍 Vérification de l'état des services..."
# docker-compose ps

# Aller dans le dossier myflow
# cd myflow

# Activer l'environnement virtuel
echo "🐍 Activation de l'environnement virtuel..."
source venv/bin/activate

# Tester la faisabilité
echo "🧪 Test de faisabilité..."
python scripts/test_youtube_workflow.py

# Si les tests passent, exécuter le workflow
# if [ $? -eq 0 ]; then
#     echo "🎉 Tests réussis! Exécution du workflow..."
python examples/youtube_ingestion_workflow.py
# else
#     echo "💥 Tests échoués. Vérifiez la configuration."
#     echo "💡 Consultez YOUTUBE_WORKFLOW_GUIDE.md pour plus d'informations"
# fi

echo ""
echo "✅ Script terminé!"
echo "📊 Consultez les logs ci-dessus pour les résultats détaillés"
