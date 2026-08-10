"""
aggregate_trips.py — the Spark job that example_taxi_dag submits to the cluster.

Usage:  spark-submit --master spark://spark-master:7077 aggregate_trips.py 2026-07-27

Reads  /workspace/data/trips_<ds>.csv   (created by the DAG's generate task)
Writes /workspace/data/agg_<ds>.parquet (total fare per zone for that day)

Run it, then find the job in the Spark UI (localhost:8080) and count its
stages — the groupBy causes exactly one shuffle.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

ds = sys.argv[1] if len(sys.argv) > 1 else "manual"

spark = SparkSession.builder.appName(f"aggregate_trips_{ds}").getOrCreate()

# Explicit schema: never let production jobs infer types from data
schema = StructType([
    StructField("pickup_time", StringType()),
    StructField("zone_id", IntegerType()),
    StructField("distance_km", DoubleType()),
    StructField("fare", DoubleType()),
])

trips = spark.read.csv(f"/workspace/data/trips_{ds}.csv", header=True, schema=schema)

agg = (
    trips
    .filter((F.col("fare") > 0) & (F.col("distance_km") > 0))   # transformation (lazy)
    .groupBy("zone_id")                                          # -> shuffle boundary
    .agg(F.round(F.sum("fare"), 2).alias("total_fare"))
    .withColumn("ds", F.lit(ds))
)

# .write is the ACTION: only here does the whole plan actually execute
agg.write.mode("overwrite").parquet(f"/workspace/data/agg_{ds}.parquet")

print(f"aggregate_trips: wrote agg_{ds}.parquet with {agg.count()} zones")
spark.stop()
