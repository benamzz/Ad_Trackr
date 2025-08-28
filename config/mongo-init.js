// Script d'initialisation MongoDB Ad_Trackr

// Utiliser la base de données ad_trackr
db = db.getSiblingDB('ad_trackr');

// Créer UNIQUEMENT les collections utilisées
db.createCollection('google_trends_raw');

// Index MODERNES pour optimiser les requêtes réelles
print("🔧 Création des index optimisés...");

// Index pour le cache (utilisé par les scripts)
db.google_trends_raw.createIndex({ "cache_key": 1 }, { unique: true });

// Index pour les requêtes par mot-clé (utilisé fréquemment)
db.google_trends_raw.createIndex({ "keyword": 1 });

// Index pour les requêtes par géolocalisation
db.google_trends_raw.createIndex({ "geo": 1 });

// Index pour le nettoyage/maintenance par date d'ingestion
db.google_trends_raw.createIndex({ "ingestion_timestamp": 1 });

// Index composé pour requêtes complexes
db.google_trends_raw.createIndex({ "keyword": 1, "geo": 1 });

print("✅ MongoDB initialisé avec succès pour Ad_Trackr !");
print("📊 Collections créées: google_trends_raw");
print("🔍 Index optimisés: cache_key, keyword, geo, ingestion_timestamp"); 