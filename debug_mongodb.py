#!/usr/bin/env python3
"""
Script de débogage pour analyser la structure des données MongoDB
"""

from pymongo import MongoClient

def analyze_mongodb_structure():
    """Analyse la structure des données MongoDB"""
    try:
        # Connexion MongoDB
        client = MongoClient('mongodb://admin:password123@datalake-mongo:27017/', authSource='admin')
        db = client.datalake
        collection = db.raw_data
        
        print("=== ANALYSE DE LA STRUCTURE MONGODB ===")
        print(f"Nombre total de documents: {collection.count_documents({})}")
        
        # Analyse de quelques documents
        docs = list(collection.find({}).limit(3))
        
        for i, doc in enumerate(docs):
            print(f"\n--- DOCUMENT {i+1} ---")
            print(f"Clés principales: {list(doc.keys())}")
            
            for key, value in doc.items():
                if key == '_id':
                    print(f"{key}: {type(value).__name__} = {str(value)}")
                elif isinstance(value, dict):
                    print(f"{key}: dict avec {len(value)} clés")
                    if key == 'raw_data' and len(value) > 0:
                        print(f"  Clés de raw_data: {list(value.keys())[:10]}...")  # Première 10 clés
                        # Échantillon de données
                        for subkey, subvalue in list(value.items())[:3]:
                            print(f"    {subkey}: {type(subvalue).__name__} = {str(subvalue)[:50]}...")
                elif isinstance(value, list):
                    print(f"{key}: list avec {len(value)} éléments")
                else:
                    print(f"{key}: {type(value).__name__} = {str(value)[:50]}...")
        
        client.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    analyze_mongodb_structure()
