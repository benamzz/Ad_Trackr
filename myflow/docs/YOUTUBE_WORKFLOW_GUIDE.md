# �� Guide du Workflow d'Ingestion YouTube

## 📋 Vue d'ensemble

Ce guide vous explique comment utiliser le workflow MyFlow pour l'ingestion des données YouTube :
**YouTube API → MongoDB → Spark → HDFS**

## 🏗️ Architecture du Workflow

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   YouTube API   │───▶│   MongoDB    │───▶│    Spark    │───▶│    HDFS     │
│                 │    │              │    │             │    │             │
│ • Extraction    │    │ • Stockage   │    │ • ETL       │    │ • Stockage  │
│ • Données brutes│    │ • Données    │    │ • Transform │    │ • Final     │
│                 │    │   brutes     │    │ • Clean     │    │             │
└─────────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Étapes de Démarrage

### 1. Démarrer l'Infrastructure

```bash
# Aller dans le répertoire racine du projet
cd /Users/finnhuman/Documents/TD_groupe_Datalake/Ad_Trackr

# Démarrer tous les services
docker-compose up -d

# Vérifier que tous les services sont en cours
docker-compose ps
```

### 2. Vérifier la Configuration

```bash
# Aller dans le dossier myflow
cd myflow

# Activer l'environnement virtuel
source venv/bin/activate

# Tester la faisabilité
python scripts/test_youtube_workflow.py
```

### 3. Exécuter le Workflow

```bash
# Exécuter le workflow complet
python examples/youtube_ingestion_workflow.py
```

## 🔧 Configuration Requise

### Variables d'Environnement (.env)
```bash
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# MongoDB Configuration  
MONGO_URI=mongodb://admin:password123@mongo:27017/
MONGO_USERNAME=admin
MONGO_PASSWORD=password123
MONGO_DATABASE=datalake

# HDFS Configuration
HDFS_NAMENODE_URL=hdfs://namenode:9000
HDFS_BASE_PATH=/user/influencers_analysis

# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
```

### Services Docker Requis
- `datalake-mongo` : Base de données MongoDB
- `datalake-namenode` : HDFS NameNode
- `datalake-spark-master` : Spark Master

## 📊 Workflow Détaillé

### Tâche 1: Vérification de l'Environnement
- ✅ Variables d'environnement présentes
- ✅ Clé API YouTube valide

### Tâche 2: Vérification de la Santé des Services
- ✅ MongoDB accessible
- ✅ HDFS accessible

### Tâche 3: Extraction YouTube → MongoDB
- 🎬 Appel API YouTube Data v3
- 📊 Extraction des données des influenceurs
- 💾 Stockage dans MongoDB (collection `raw_data`)

### Tâche 4: ETL Spark (MongoDB → HDFS)
- 🔄 Lecture des données depuis MongoDB
- 🧹 Transformation et nettoyage
- �� Stockage final dans HDFS

### Tâche 5: Vérification Finale
- 📊 Comptage des documents dans MongoDB
- ✅ Vérification des fichiers dans HDFS

## 🧪 Tests de Validation

### Test de Faisabilité
```bash
python scripts/test_youtube_workflow.py
```

**Résultats attendus :**
- ✅ Services Docker: PASS
- ✅ Variables d'environnement: PASS  
- ✅ Scripts disponibles: PASS
- ✅ Connexion MongoDB: PASS
- ✅ Connexion HDFS: PASS
- ✅ API YouTube: PASS

### Test du Workflow Complet
```bash
python examples/youtube_ingestion_workflow.py
```

**Résultats attendus :**
- ✅ Toutes les tâches réussies
- 📊 Données dans MongoDB
- 💾 Données dans HDFS

## 🔍 Monitoring et Debugging

### Logs du Workflow
Le workflow MyFlow génère des logs détaillés :
```
2025-08-29 09:30:00 - myflow - INFO - Démarrage de l'extraction YouTube vers MongoDB
2025-08-29 09:30:05 - myflow - INFO - Extraction YouTube terminée avec succès
2025-08-29 09:30:10 - myflow - INFO - Démarrage de l'ETL Spark (MongoDB vers HDFS)
2025-08-29 09:30:30 - myflow - INFO - ETL Spark terminé avec succès
```

### Vérification des Données

#### MongoDB
```bash
# Se connecter à MongoDB
docker exec -it datalake-mongo mongosh

# Vérifier les données
use datalake
db.raw_data.countDocuments({})
db.raw_data.findOne()
```

#### HDFS
```bash
# Lister les fichiers dans HDFS
docker exec datalake-namenode hdfs dfs -ls /user/influencers_analysis

# Vérifier le contenu
docker exec datalake-namenode hdfs dfs -cat /user/influencers_analysis/part-00000
```

## 🚨 Résolution de Problèmes

### Problème: Services Docker non démarrés
```bash
# Solution
docker-compose up -d
docker-compose ps
```

### Problème: Erreur de connexion MongoDB
```bash
# Vérifier que MongoDB est démarré
docker logs datalake-mongo

# Vérifier la configuration
echo $MONGO_URI
```

### Problème: Erreur API YouTube
```bash
# Vérifier la clé API
echo $YOUTUBE_API_KEY

# Tester manuellement
curl "https://www.googleapis.com/youtube/v3/search?key=$YOUTUBE_API_KEY&part=snippet&q=test&maxResults=1"
```

### Problème: Erreur HDFS
```bash
# Vérifier que HDFS est démarré
docker logs datalake-namenode

# Vérifier l'espace disque
docker exec datalake-namenode hdfs dfsadmin -report
```

## 📈 Métriques de Performance

### Temps d'Exécution Typiques
- **Vérification environnement** : ~1 seconde
- **Vérification services** : ~5 secondes
- **Extraction YouTube** : ~30-60 secondes
- **ETL Spark** : ~2-5 minutes
- **Vérification finale** : ~5 secondes

### Volume de Données
- **Données brutes** : ~1-10 MB par extraction
- **Données transformées** : ~500 KB - 5 MB
- **Fréquence recommandée** : Quotidienne

## 🎯 Prochaines Étapes

1. **Automatisation** : Planifier l'exécution quotidienne
2. **Monitoring** : Ajouter des alertes en cas d'échec
3. **Optimisation** : Paralléliser les extractions
4. **Analytics** : Créer des dashboards de monitoring

## 📞 Support

En cas de problème :
1. Vérifiez les logs du workflow
2. Consultez les logs Docker des services
3. Testez chaque composant individuellement
4. Vérifiez la configuration des variables d'environnement

---

**MyFlow YouTube Workflow** - Pipeline d'ingestion automatisé 🎬🚀
