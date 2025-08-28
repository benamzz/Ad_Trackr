#!/usr/bin/env python3
"""
Script Spark OPTIMISÉ pour MongoDB → HDFS avec partitioning et optimisations
VERSION PERFORMANCE avec indexation logique et cache intelligent
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from pyspark.sql.types import *
from datetime import datetime, timedelta
import os

def create_optimized_spark_session():
    """Créer une session Spark optimisée pour performance"""
    try:
        print("🔧 Initialisation de Spark OPTIMISÉ...")
        
        spark = SparkSession.builder \
            .appName("GoogleTrends_Optimized_Analytics") \
            .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "64MB") \
            .config("spark.sql.parquet.enableVectorizedReader", "true") \
            .config("spark.sql.parquet.columnarReaderBatchSize", "4096") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        print("✅ Session Spark OPTIMISÉE créée")
        return spark
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def read_raw_data_from_mongodb(spark):
    """Lire les données brutes depuis MongoDB avec cache"""
    try:
        print("📖 Lecture des données BRUTES depuis MongoDB...")
        
        df = spark.read \
            .format("com.mongodb.spark.sql.DefaultSource") \
            .option("uri", "mongodb://admin:password123@mongodb:27017/ad_trackr.google_trends_raw?authSource=admin") \
            .load()
        
        # CACHE pour réutilisation multiple
        df.cache()
        
        count = df.count()
        print(f"✅ Données brutes lues et MISES EN CACHE: {count} documents")
        
        if count > 0:
            print("📋 Schéma des données BRUTES:")
            df.printSchema()
            print("\n📄 Aperçu des données BRUTES:")
            df.show(2, truncate=True)
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lecture MongoDB: {e}")
        return None

def explode_raw_data_optimized(df_raw):
    """Explosion optimisée des données brutes avec pré-filtrage"""
    try:
        print("🔄 Explosion OPTIMISÉE des données brutes...")
        
        # Filtrer les documents valides AVANT explosion (optimisation)
        df_valid = df_raw.filter(
            col("raw_data").isNotNull() & 
            (size(col("raw_data")) > 0)
        )
        
        # Explosion avec colonnes optimisées
        df_exploded = df_valid.select(
            col("keyword").alias("search_keyword"),
            col("geo").alias("country_code"),
            col("timeframe"),
            col("ingestion_timestamp"),
            col("source"),
            explode(col("raw_data")).alias("trend_data")
        ).select(
            "*",
            col("trend_data.date").alias("trend_date_str"),
            col("trend_data.value").alias("trend_value_raw")
        ).drop("trend_data")
        
        # CACHE après explosion (données fréquemment réutilisées)
        df_exploded.cache()
        
        count = df_exploded.count()
        print(f"✅ Données explosées et CACHÉES: {count} lignes individuelles")
        
        return df_exploded
        
    except Exception as e:
        print(f"❌ Erreur explosion: {e}")
        return None

def transform_data_with_performance_optimization(df_exploded):
    """Transformation avec optimisations de performance et pré-agrégations"""
    try:
        print("🔄 Transformation OPTIMISÉE des données...")
        
        # 1. Nettoyage et conversion de types optimisée
        df_cleaned = df_exploded.filter(
            col("trend_value_raw").isNotNull() & 
            (col("trend_value_raw") >= 0)
        ).withColumn(
            "trend_date", 
            to_timestamp(col("trend_date_str"), "yyyy-MM-dd'T'HH:mm:ss")
        ).withColumn(
            "trend_value", 
            col("trend_value_raw").cast(IntegerType())
        ).withColumn(
            "processing_date", 
            current_timestamp()
        )
        
        # 2. Enrichissement avec colonnes d'indexation logique
        df_enriched = df_cleaned.withColumn(
            "date_year", 
            year("trend_date")
        ).withColumn(
            "date_month", 
            month("trend_date")
        ).withColumn(
            "date_day", 
            dayofmonth("trend_date")
        ).withColumn(
            "day_of_week", 
            dayofweek("trend_date")
        ).withColumn(
            "week_of_year", 
            weekofyear("trend_date")
        ).withColumn(
            "quarter",
            when(col("date_month").between(1, 3), "Q1")
            .when(col("date_month").between(4, 6), "Q2")
            .when(col("date_month").between(7, 9), "Q3")
            .otherwise("Q4")
        ).withColumn(
            "season",
            when(col("date_month").isin([12, 1, 2]), "Hiver")
            .when(col("date_month").isin([3, 4, 5]), "Printemps")
            .when(col("date_month").isin([6, 7, 8]), "Été")
            .otherwise("Automne")
        ).withColumn(
            "month_name_fr",
            when(col("date_month") == 1, "Janvier")
            .when(col("date_month") == 2, "Février")
            .when(col("date_month") == 3, "Mars")
            .when(col("date_month") == 4, "Avril")
            .when(col("date_month") == 5, "Mai")
            .when(col("date_month") == 6, "Juin")
            .when(col("date_month") == 7, "Juillet")
            .when(col("date_month") == 8, "Août")
            .when(col("date_month") == 9, "Septembre")
            .when(col("date_month") == 10, "Octobre")
            .when(col("date_month") == 11, "Novembre")
            .otherwise("Décembre")
        )
        
        # 3. Métriques de performance avec fenêtres optimisées
        window_spec = Window.partitionBy("search_keyword", "country_code").orderBy("trend_date")
        window_30d = Window.partitionBy("search_keyword", "country_code").orderBy("trend_date").rowsBetween(-29, 0)
        
        df_with_metrics = df_enriched.withColumn(
            "is_peak", 
            when(col("trend_value") == 100, True).otherwise(False)
        ).withColumn(
            "is_high_interest", 
            when(col("trend_value") >= 70, True).otherwise(False)
        ).withColumn(
            "campaign_potential",
            when(col("trend_value") >= 90, "Excellent")
            .when(col("trend_value") >= 80, "Très Bon")
            .when(col("trend_value") >= 70, "Bon")
            .when(col("trend_value") >= 50, "Moyen")
            .otherwise("Faible")
        ).withColumn(
            "moving_avg_30d", 
            avg("trend_value").over(window_30d)
        ).withColumn(
            "trend_change", 
            col("trend_value") - lag("trend_value", 1).over(window_spec)
        ).withColumn(
            "trend_change_pct",
            (col("trend_change") / lag("trend_value", 1).over(window_spec)) * 100
        ).withColumn(
            "momentum",
            when(col("trend_change_pct") >= 20, "Forte hausse")
            .when(col("trend_change_pct") >= 10, "Hausse")
            .when(col("trend_change_pct") >= -10, "Stable")
            .when(col("trend_change_pct") >= -20, "Baisse")
            .otherwise("Forte baisse")
        )
        
        # CACHE final pour réutilisation
        df_with_metrics.cache()
        count = df_with_metrics.count()
        print(f"✅ Données enrichies et CACHÉES: {count} enregistrements")
        
        return df_with_metrics
        
    except Exception as e:
        print(f"❌ Erreur transformation: {e}")
        return None

def save_to_hdfs_optimized(df, path, description, partition_cols=None, bucket_col=None):
    """Sauvegarde OPTIMISÉE vers HDFS avec partitioning et optimisations"""
    try:
        hdfs_path = f"hdfs://namenode:9000{path}"
        print(f"💾 Sauvegarde OPTIMISÉE {description} vers HDFS: {path}")
        
        if partition_cols and bucket_col:
            print(f"   📊 Partitioning par: {partition_cols}")
            print(f"   🎯 Bucketing par: {bucket_col}")
            
            df.write \
                .mode("overwrite") \
                .format("parquet") \
                .option("compression", "snappy") \
                .partitionBy(*partition_cols) \
                .bucketBy(10, bucket_col) \
                .sortBy("trend_date") \
                .save(hdfs_path)
        elif partition_cols:
            print(f"   📊 Partitioning par: {partition_cols}")
            
            df.write \
                .mode("overwrite") \
                .format("parquet") \
                .option("compression", "snappy") \
                .partitionBy(*partition_cols) \
                .save(hdfs_path)
        else:
            # Sauvegarde standard avec compression optimisée
            df.coalesce(4).write \
                .mode("overwrite") \
                .format("parquet") \
                .option("compression", "snappy") \
                .save(hdfs_path)
        
        print(f"✅ Sauvegarde OPTIMISÉE réussie: {hdfs_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde HDFS: {e}")
        return False

def create_optimized_analytics(df):
    """Créer des analyses optimisées avec agrégations pré-calculées"""
    try:
        print("🎯 Création d'analyses OPTIMISÉES...")
        
        # 1. Analyse mensuelle avec partitioning optimal
        monthly_analysis = df.groupBy(
            "search_keyword", "country_code", "date_year", "date_month", 
            "month_name_fr", "season", "quarter"
        ).agg(
            avg("trend_value").alias("avg_monthly_interest"),
            max("trend_value").alias("peak_monthly_interest"),
            min("trend_value").alias("min_monthly_interest"),
            sum(when(col("is_high_interest"), 1).otherwise(0)).alias("high_interest_days"),
            sum(when(col("is_peak"), 1).otherwise(0)).alias("peak_days"),
            count("*").alias("total_days"),
            avg("moving_avg_30d").alias("avg_30d_trend"),
            stddev("trend_value").alias("volatility")
        ).withColumn(
            "high_interest_ratio", col("high_interest_days") / col("total_days")
        ).withColumn(
            "peak_ratio", col("peak_days") / col("total_days")
        ).withColumn(
            "campaign_score",
            (col("avg_monthly_interest") * 0.4) + 
            (col("high_interest_ratio") * 30) + 
            (col("peak_ratio") * 30)
        ).withColumn(
            "campaign_recommendation",
            when(col("campaign_score") >= 80, "🏆 EXCELLENT - Période idéale pour campagne majeure")
            .when(col("campaign_score") >= 70, "🥇 TRÈS BON - Excellente période pour campagne")
            .when(col("campaign_score") >= 60, "🥈 BON - Période favorable pour campagne")
            .when(col("campaign_score") >= 50, "🥉 MOYEN - Période acceptable avec budget réduit")
            .otherwise("❌ FAIBLE - Éviter cette période")
        ).withColumn(
            "best_month_rank",
            row_number().over(Window.partitionBy("search_keyword").orderBy(desc("campaign_score")))
        )
        
        # CACHE pour réutilisation
        monthly_analysis.cache()
        
        # 2. Analyse saisonnière optimisée
        seasonal_analysis = df.groupBy("search_keyword", "country_code", "season").agg(
            avg("trend_value").alias("avg_seasonal_interest"),
            max("trend_value").alias("peak_seasonal_interest"),
            sum(when(col("is_high_interest"), 1).otherwise(0)).alias("high_interest_days"),
            count("*").alias("total_days")
        ).withColumn(
            "seasonal_score",
            (col("avg_seasonal_interest") * 0.6) + (col("high_interest_days") / col("total_days") * 40)
        ).withColumn(
            "seasonal_rank",
            row_number().over(Window.partitionBy("search_keyword").orderBy(desc("seasonal_score")))
        )
        
        # 3. Autres analyses...
        weekly_analysis = df.groupBy("search_keyword", "country_code", "day_of_week").agg(
            avg("trend_value").alias("avg_daily_interest"),
            count("*").alias("occurrences")
        ).withColumn(
            "day_name",
            when(col("day_of_week") == 1, "Dimanche")
            .when(col("day_of_week") == 2, "Lundi")
            .when(col("day_of_week") == 3, "Mardi")
            .when(col("day_of_week") == 4, "Mercredi")
            .when(col("day_of_week") == 5, "Jeudi")
            .when(col("day_of_week") == 6, "Vendredi")
            .otherwise("Samedi")
        ).withColumn(
            "day_rank",
            row_number().over(Window.partitionBy("search_keyword").orderBy(desc("avg_daily_interest")))
        )
        
        strategic_recommendations = df.groupBy("search_keyword", "country_code").agg(
            avg("trend_value").alias("overall_avg_interest"),
            max("trend_value").alias("absolute_peak"),
            min("trend_value").alias("lowest_point"),
            sum(when(col("is_high_interest"), 1).otherwise(0)).alias("total_high_days"),
            count("*").alias("total_data_points"),
            min("trend_date").alias("analysis_start"),
            max("trend_date").alias("analysis_end")
        ).withColumn(
            "market_attractiveness",
            when(col("overall_avg_interest") >= 70, "📈 MARCHÉ TRÈS ATTRACTIF")
            .when(col("overall_avg_interest") >= 50, "📈 MARCHÉ ATTRACTIF")
            .when(col("overall_avg_interest") >= 30, "📊 MARCHÉ MODÉRÉ")
            .otherwise("📉 MARCHÉ PEU ATTRACTIF")
        ).withColumn(
            "budget_recommendation",
            when(col("absolute_peak") >= 90, "Budget élevé - ROI potentiel excellent")
            .when(col("absolute_peak") >= 70, "Budget moyen-élevé - ROI potentiel bon")
            .when(col("absolute_peak") >= 50, "Budget moyen - ROI potentiel modéré")
            .otherwise("Budget faible - ROI potentiel limité")
        )
        
        print(f"✅ Analyses optimisées créées:")
        print(f"   • Analyse mensuelle: {monthly_analysis.count()} lignes")
        print(f"   • Analyse saisonnière: {seasonal_analysis.count()} lignes")
        print(f"   • Analyse hebdomadaire: {weekly_analysis.count()} lignes")
        print(f"   • Recommandations stratégiques: {strategic_recommendations.count()} lignes")
        
        return monthly_analysis, seasonal_analysis, weekly_analysis, strategic_recommendations
        
    except Exception as e:
        print(f"❌ Erreur création analyses: {e}")
        return None, None, None, None

def main():
    """Pipeline principal OPTIMISÉ"""
    print("🚀 PIPELINE MARKETING OPTIMISÉ: PERFORMANCE & INDEXATION LOGIQUE")
    print("="*70)
    
    start_time = datetime.now()
    
    spark = create_optimized_spark_session()
    if not spark:
        return
    
    try:
        # 1. Lecture avec cache
        df_raw = read_raw_data_from_mongodb(spark)
        if df_raw is None:
            return
        
        # 2. Explosion optimisée
        df_exploded = explode_raw_data_optimized(df_raw)
        if df_exploded is None:
            return
        
        # 3. Transformation avec optimisations
        df_transformed = transform_data_with_performance_optimization(df_exploded)
        if df_transformed is None:
            return
        
        # 4. Analyses optimisées
        monthly, seasonal, weekly, strategic = create_optimized_analytics(df_transformed)
        if monthly is None:
            return
        
        print("\n💾 SAUVEGARDE OPTIMISÉE HDFS:")
        
        # 5. Sauvegarde avec partitioning optimal
        # Données détaillées partitionnées par keyword et date
        save_to_hdfs_optimized(
            df_transformed, 
            "/data/google/clean/detailed", 
            "données détaillées",
            partition_cols=["search_keyword", "date_year", "date_month"]
        )
        
        # Analyses partitionnées par keyword pour accès rapide
        save_to_hdfs_optimized(
            monthly, 
            "/data/google/analytics/monthly_analysis", 
            "analyse mensuelle",
            partition_cols=["search_keyword"]
        )
        
        save_to_hdfs_optimized(
            seasonal, 
            "/data/google/analytics/seasonal_analysis", 
            "analyse saisonnière",
            partition_cols=["search_keyword"]
        )
        
        save_to_hdfs_optimized(weekly, "/data/google/analytics/weekly_analysis", "analyse hebdomadaire")
        save_to_hdfs_optimized(strategic, "/data/google/analytics/strategic_recommendations", "recommandations")
        
        duration = datetime.now() - start_time
        print(f"\n⏱️ Pipeline OPTIMISÉ terminé en: {duration}")
        print("✅ Données indexées logiquement et optimisées pour requêtes rapides!")
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {e}")
    
    finally:
        spark.stop()

if __name__ == "__main__":
    main() 