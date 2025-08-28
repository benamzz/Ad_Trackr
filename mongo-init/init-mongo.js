// Script d'initialisation MongoDB pour le Data Lake
// Création de la base de données et des collections pour la pipeline

db = db.getSiblingDB('datalake');

// Création des collections pour les données brutes
db.createCollection('raw_data');
db.createCollection('api_logs');
db.createCollection('processing_status');

// Index pour optimiser les requêtes
db.raw_data.createIndex({ "timestamp": 1 });
db.raw_data.createIndex({ "source": 1 });
db.raw_data.createIndex({ "processed": 1 });

db.api_logs.createIndex({ "timestamp": 1 });
db.processing_status.createIndex({ "job_id": 1 });

// Insertion d'un document exemple
db.raw_data.insertOne({
    "source": "youtube_api",
    "timestamp": new Date(),
    "processed": false,
    "data": {
        "example": "Données brutes provenant des API calls"
    }
});

print("Base de données 'datalake' initialisée avec succès !");
