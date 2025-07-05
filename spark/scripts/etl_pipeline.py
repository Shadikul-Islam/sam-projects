from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_timestamp, regexp_extract, lower, length, when, lit
)
from datetime import datetime, timedelta
from pytz import timezone, utc
import pandas as pd
import numpy as np
import pickle
import socket
import struct
import os
from sklearn.decomposition import PCA

# Constants
ES_INDEX = "network_logs"
OUTPUT_DIR = "/opt/spark_output"
DHAKA_TZ = timezone("Asia/Dhaka")

# Helper: Convert IP to integer
def ip_to_int(ip):
    try:
        return struct.unpack("!I", socket.inet_aton(ip))[0]
    except:
        return 0

# Helper: Get last hour window in UTC based on Dhaka time
def get_last_hour_window():
    now_dhaka = datetime.now(DHAKA_TZ).replace(minute=0, second=0, microsecond=0)
    last_hour_end = now_dhaka
    last_hour_start = last_hour_end - timedelta(hours=1)

    # Convert to UTC for Elasticsearch
    last_hour_start_utc = last_hour_start.astimezone(utc).isoformat()
    last_hour_end_utc = last_hour_end.astimezone(utc).isoformat()

    # Time window for folder naming (e.g., 15-16)
    start_hour = last_hour_start.strftime("%H")
    end_hour = last_hour_end.strftime("%H")
    window_folder = f"{start_hour}-{end_hour}"

    return last_hour_start_utc, last_hour_end_utc, last_hour_start.strftime("%Y-%m-%d"), window_folder

# Start Spark
spark = SparkSession.builder \
    .appName("ETLNetworkLogs") \
    .config("spark.es.nodes", "52.6.4.88") \
    .config("spark.es.port", "9200") \
    .config("spark.es.net.http.auth.user", "elastic") \
    .config("spark.es.net.http.auth.pass", "0wBH-ZP1y=olUiV_J7bb") \
    .config("spark.es.nodes.wan.only", "true") \
    .config("spark.es.net.ssl", "true") \
    .config("spark.es.net.ssl.cert.allow.self.signed", "true") \
    .getOrCreate()

# Step 1: Load 1-hour window data from Elasticsearch
start_time, end_time, day_str, hour_window = get_last_hour_window()

# Format time range for logging
start_dt = datetime.fromisoformat(start_time)
end_dt = datetime.fromisoformat(end_time)
formatted_window = f"{start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')} UTC"

print("======================================================")
print(f"🔎  Fetching data from: {formatted_window}")
print("======================================================")

df = spark.read.format("org.elasticsearch.spark.sql").load(ES_INDEX) \
    .filter((col("@timestamp") >= lit(start_time)) & (col("@timestamp") < lit(end_time)))

if df.rdd.isEmpty():
    print("##################################################################")
    print("ℹ️  No logs found in Elasticsearch for the previous hour window.")
    print("##################################################################")
    spark.stop()
    exit(0)

# Step 2: Convert timestamp and parse fields
df = df.withColumn("event_time", to_timestamp(col("@timestamp")))

df_parsed = df.withColumn("router_id", regexp_extract(col("message"), r"^(Router\d+)", 1)) \
    .withColumn("event_type", regexp_extract(col("message"), r"(Incorrectly Advertised|Duplicate|High Latency|reset)", 1)) \
    .withColumn("peer_ip", regexp_extract(col("message"), r"(\d{1,3}(?:\.\d{1,3}){3})", 1)) \
    .withColumn("message_lower", lower(col("message"))) \
    .withColumn("severity_score", when(col("log.level") == "INFO", 1)
                                  .when(col("log.level") == "WARN", 2)
                                  .when(col("log.level") == "ERROR", 3)
                                  .otherwise(0)) \
    .withColumn("message_length", length(col("message"))) \
    .withColumn("has_keyword_error", col("message_lower").rlike("error|timeout|failed|unreachable").cast("boolean"))

# Step 3: Select relevant fields
selected_columns = [
    "@timestamp", "@version", "host", "log", "message", "event_time",
    "router_id", "event_type", "peer_ip", "severity_score",
    "message_length", "has_keyword_error"
]
df_final = df_parsed.select(*selected_columns)

# Step 4: Convert to Pandas for ML processing
ml_df = df_final.select(
    "router_id", "event_type", "peer_ip", "severity_score",
    "message_length", "has_keyword_error"
).dropna()
pandas_df = ml_df.toPandas()

if pandas_df.empty:
    print("################################################################")
    print("ℹ️  No valid records for ML processing after filtering.")
    print("ℹ️  Skipping PCA and data export.")
    print("################################################################")
else:
    # Step 5: Feature engineering
    pandas_df["peer_ip_int"] = pandas_df["peer_ip"].apply(ip_to_int)
    pandas_df["router_id_hash"] = pandas_df["router_id"].apply(lambda x: hash(x) % 100000 if pd.notnull(x) else 0)
    pandas_df["event_type_hash"] = pandas_df["event_type"].apply(lambda x: hash(x) % 100 if pd.notnull(x) else 0)

    feature_cols = [
        "peer_ip_int", "router_id_hash", "event_type_hash",
        "severity_score", "message_length", "has_keyword_error"
    ]
    pandas_df[feature_cols] = pandas_df[feature_cols].fillna(0)

    # Step 6: PCA for vector compression
    pca = PCA(n_components=2)
    vectors = pca.fit_transform(pandas_df[feature_cols])

    # Step 7: Create output directory using Dhaka-local hour window
    output_path = os.path.join(OUTPUT_DIR, day_str, hour_window)
    os.makedirs(output_path, exist_ok=True)

    # Save FAISS vectors
    # vector_output_path = os.path.join(output_path, "faiss_ready_vectors.pkl")
    # with open(vector_output_path, "wb") as f:
    #     pickle.dump({
    #         "vectors": vectors,
    #         "metadata": pandas_df[["peer_ip", "router_id", "event_type"]].to_dict(orient="records")
    #     }, f)


    # Save FAISS vectors + extended metadata
    vector_output_path = os.path.join(output_path, "faiss_ready_vectors.pkl")

    # Join with original DataFrame to get full log context
    enriched_df = pandas_df.copy()
    enriched_df["pca_x"] = vectors[:, 0]
    enriched_df["pca_y"] = vectors[:, 1]

    json_logs = df_final.toPandas()

    # Safety check in case number of rows differ
    metadata = []
    if len(enriched_df) == len(json_logs):
        for i in range(len(enriched_df)):
            metadata.append({
                "peer_ip": enriched_df.loc[i, "peer_ip"],
                "router_id": enriched_df.loc[i, "router_id"],
                "event_type": enriched_df.loc[i, "event_type"],
                "timestamp": str(json_logs.loc[i, "@timestamp"]),
                "message": json_logs.loc[i, "message"],
                "host": json_logs.loc[i, "host"],
                "pca_x": enriched_df.loc[i, "pca_x"],
                "pca_y": enriched_df.loc[i, "pca_y"]
            })
    else:
        print("❗ Warning: Data mismatch, falling back to partial info.")
        for i in range(len(enriched_df)):
            metadata.append({
                "peer_ip": enriched_df.loc[i, "peer_ip"],
                "router_id": enriched_df.loc[i, "router_id"],
                "event_type": enriched_df.loc[i, "event_type"],
                "timestamp": "unknown",
                "message": "unknown",
                "host": "unknown",
                "pca_x": enriched_df.loc[i, "pca_x"],
                "pca_y": enriched_df.loc[i, "pca_y"]
            })


    # Save vectors and metadata
    with open(vector_output_path, "wb") as f:
        pickle.dump({
            "vectors": vectors,
            "metadata": metadata
        }, f)


    print("========================================================================================")
    print("✅  FAISS vector saved to:", vector_output_path)
    print("========================================================================================")

    # Save processed logs
    log_output_path = os.path.join(output_path, "processed_json_logs")
    df_final.write.mode("overwrite").json(log_output_path)

    print("=========================================================================================")
    print("✅  Processed JSON logs saved to:", log_output_path)
    print("=========================================================================================")

# Completion log
print("=======================================================================================")
print(f"✅  Hourly ETL pipeline completed successfully. Timeframe: {formatted_window}")
print("=======================================================================================")

spark.stop()