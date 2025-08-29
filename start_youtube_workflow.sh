#!/bin/bash

echo "🎬 Démarrage du Workflow YouTube avec Docker"
echo "============================================="

# Vérifier si le fichier .env existe
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé. Création d'un template..."
    cat > .env << EOF
# Configuration pour le workflow YouTube
# Remplacez YOUR_YOUTUBE_API_KEY par votre vraie clé API YouTube

# YouTube API
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY

# MongoDB Configuration
MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password123
MONGO_URI=mongodb://admin:password123@mongo:27017/

# HDFS Configuration
HDFS_HOST=namenode
HDFS_PORT=9870
HDFS_NAMENODE_URL=hdfs://namenode:9000

# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
EOF
    echo "✅ Fichier .env créé. Veuillez y ajouter votre clé API YouTube."
    echo "💡 Éditez le fichier .env et remplacez YOUR_YOUTUBE_API_KEY par votre vraie clé."
    exit 1
fi

# Vérifier si la clé API YouTube est configurée
if grep -q "YOUR_YOUTUBE_API_KEY" .env; then
    echo "❌ Veuillez configurer votre clé API YouTube dans le fichier .env"
    echo "💡 Remplacez YOUR_YOUTUBE_API_KEY par votre vraie clé API YouTube"
    exit 1
fi

echo "✅ Configuration validée"

# Démarrer l'infrastructure Docker
echo "🐳 Démarrage de l'infrastructure Docker..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

# Vérifier l'état des services
echo "🔍 Vérification de l'état des services..."
docker-compose ps

# Attendre que MongoDB soit prêt
echo "⏳ Attente que MongoDB soit prêt..."
until docker exec datalake-mongo mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; do
    echo "   En attente de MongoDB..."
    sleep 5
done
echo "✅ MongoDB est prêt"

# Attendre que HDFS soit prêt
echo "⏳ Attente que HDFS soit prêt..."
until curl -s http://localhost:9870 > /dev/null 2>&1; do
    echo "   En attente de HDFS..."
    sleep 5
done
echo "✅ HDFS est prêt"

# Attendre que Spark soit prêt
echo "⏳ Attente que Spark soit prêt..."
until curl -s http://localhost:8086 > /dev/null 2>&1; do
    echo "   En attente de Spark..."
    sleep 5
done
echo "✅ Spark est prêt"

# Exécuter le workflow YouTube
echo "🎬 Exécution du workflow YouTube..."
docker exec -it datalake-myflow python examples/youtube_ingestion_workflow.py

echo ""
echo "✅ Workflow terminé!"
echo "📊 Consultez les logs ci-dessus pour les résultats détaillés"
echo ""
echo "🔗 Interfaces disponibles:"
echo "   - MongoDB Express: http://localhost:8082 (admin/admin)"
echo "   - HDFS NameNode: http://localhost:9870"
echo "   - Spark Master: http://localhost:8086"
echo "   - Spark Worker: http://localhost:8087"
