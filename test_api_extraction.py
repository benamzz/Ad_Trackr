#!/bin/bash
"""
🧪 Test du script d'extraction API YouTube
Script de test pour l'étape 1: API → MongoDB
"""

import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_extraction():
    """Test de l'extraction API YouTube vers MongoDB"""
    logger.info("🧪 TEST: Extraction API YouTube → MongoDB")
    logger.info("=" * 50)
    
    try:
        # 1. Vérification que MongoDB est actif
        logger.info("🔍 Vérification MongoDB...")
        mongo_check = subprocess.run(
            "docker exec datalake-mongo mongosh -u admin -p password123 --authenticationDatabase admin --eval 'db.runCommand(\"ping\")' --quiet",
            shell=True, capture_output=True, text=True
        )
        
        if mongo_check.returncode != 0:
            logger.error("❌ MongoDB non accessible")
            return False
        
        logger.info("✅ MongoDB accessible")
        
        # 2. Exécution du script d'extraction
        logger.info("📡 Lancement de l'extraction YouTube...")
        start_time = datetime.now()
        
        extraction_result = subprocess.run(
            "docker exec datalake-jupyter python /workspace/youtube_extractor_to_mongo.py",
            shell=True, capture_output=True, text=True, timeout=600
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 3. Vérification des résultats
        if extraction_result.returncode == 0:
            logger.info(f"✅ Extraction terminée en {execution_time:.2f}s")
            logger.info("📄 Output:")
            print(extraction_result.stdout)
            
            # Compter les documents insérés
            count_result = subprocess.run(
                "docker exec datalake-mongo mongosh -u admin -p password123 --authenticationDatabase admin datalake --eval 'db.raw_data.countDocuments()' --quiet",
                shell=True, capture_output=True, text=True
            )
            
            if count_result.returncode == 0:
                doc_count = count_result.stdout.strip()
                logger.info(f"📊 Documents dans MongoDB: {doc_count}")
            
            return True
        else:
            logger.error("❌ Échec de l'extraction")
            logger.error(f"📄 Error: {extraction_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Timeout de l'extraction (10 minutes)")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_api_extraction()
    if success:
        print("\n🎉 Test d'extraction réussi!")
    else:
        print("\n❌ Test d'extraction échoué!")
