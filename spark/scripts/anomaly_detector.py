from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.types import DoubleType
import numpy as np
import os
import pickle
import json
import time
from datetime import datetime, timedelta
from pytz import timezone

# Settings
OUTPUT_BASE = "/opt/spark_output"
DHAKA_TZ = timezone("Asia/Dhaka")

def compute_distance(point, center):
    return float(np.linalg.norm(np.array(point) - np.array(center)))

def get_last_hour_folder():
    now_dhaka = datetime.now(DHAKA_TZ).replace(minute=0, second=0, microsecond=0)
    last_hour_end = now_dhaka
    last_hour_start = last_hour_end - timedelta(hours=1)

    start_hour = last_hour_start.strftime("%H")
    end_hour = last_hour_end.strftime("%H")
    day_str = last_hour_start.strftime("%Y-%m-%d")
    hour_window = f"{start_hour}-{end_hour}"

    return day_str, hour_window, os.path.join(OUTPUT_BASE, day_str, hour_window)

def main():
    spark = SparkSession.builder \
        .appName("AnomalyDetector") \
        .getOrCreate()

    day_str, hour_window, path = get_last_hour_folder()
    print(f"📦  Analyzing data for: {path}")

    vector_file = os.path.join(path, "faiss_ready_vectors.pkl")
    output_file = os.path.join(path, "anomalies.json")

    print(f"⏳ Waiting for vector file: {vector_file}")

    # Wait for up to 10 minutes (adjustable)
    timeout = 600  # seconds
    interval = 10  # check every 10 seconds
    elapsed = 0

    while not os.path.exists(vector_file) and elapsed < timeout:
        time.sleep(interval)
        elapsed += interval

    if not os.path.exists(vector_file):
        print("❌ Timeout reached. Vector file not found:", vector_file)
        return

    with open(vector_file, "rb") as f:
        data = pickle.load(f)
        vectors = data["vectors"]
        metadata = data["metadata"]

    if len(vectors) == 0:
        print("⚠️ No vectors found for analysis.")
        return

    # Prepare DataFrame for Spark
    rows = [Row(pca_x=float(v[0]), pca_y=float(v[1])) for v in vectors]
    spark_df = spark.createDataFrame(rows)
    assembler = VectorAssembler(inputCols=["pca_x", "pca_y"], outputCol="features")
    assembled_df = assembler.transform(spark_df)

    # KMeans Clustering
    kmeans = KMeans(k=3, seed=42)
    model = kmeans.fit(assembled_df)
    clustered = model.transform(assembled_df)

    # Add distance to cluster center
    centers = model.clusterCenters()
    distance_udf = spark.udf.register("distance_udf", lambda point, cluster: compute_distance(point, centers[cluster]), DoubleType())
    clustered = clustered.withColumn("distance", distance_udf(col("features"), col("prediction")))

    # Detect anomalies using 95th percentile
    threshold = clustered.approxQuantile("distance", [0.95], 0.01)[0]
    anomalies_df = clustered.filter(col("distance") > threshold)

    # Collect anomalies with metadata
    anomalies = anomalies_df.select("pca_x", "pca_y", "distance").collect()
    anomaly_list = []

    seen = set()  # to avoid duplicate anomalies
    for i, row in enumerate(anomalies):
        if i >= len(metadata):
            continue  # safety check
        m = metadata[i]
        key = (m.get("peer_ip"), m.get("router_id"), m.get("event_type"), m.get("message"))
        if key in seen:
            continue
        seen.add(key)

        anomaly_list.append({
            "pca_x": row["pca_x"],
            "pca_y": row["pca_y"],
            "distance": row["distance"],
            "peer_ip": m.get("peer_ip", "unknown"),
            "router_id": m.get("router_id", "unknown"),
            "event_type": m.get("event_type", "unknown"),
            "timestamp": str(m.get("timestamp", "unknown")),
            "message": m.get("message", "unknown"),
            "host": m.get("host", "unknown")
        })

    # Save to JSON
    with open(output_file, "w") as out:
        json.dump(anomaly_list, out, indent=2)

    print("🚨  Anomaly detection completed.")
    print(f"✅  Saved: {output_file}")
    print(f"📊  Total anomalies: {len(anomaly_list)}")

    spark.stop()

if __name__ == "__main__":
    main()
