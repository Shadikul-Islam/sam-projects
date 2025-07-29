from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_timestamp, regexp_extract, lower, length, when, lit, to_json, from_json, array_contains,
    array_join,
    element_at, size, split, explode, get_json_object, regexp_replace
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, IntegerType, BooleanType, FloatType, ArrayType
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
    except (socket.error, TypeError): # Handle cases where ip might be None or invalid string
        return 0

# Helper: Get last hour window in UTC based on Dhaka time
def get_last_hour_window():
    now_dhaka = datetime.now(DHAKA_TZ).replace(minute=0, second=0, microsecond=0)
    last_hour_end = now_dhaka
    last_hour_start = last_hour_end - timedelta(hours=1)

    # Convert to UTC for Elasticsearch
    last_hour_start_utc = last_hour_start.astimezone(utc).isoformat()
    last_hour_end_utc = last_hour_end.astimezone(utc).isoformat() # Corrected from astazimuth

    # Time window for folder naming (e.g., 15-16)
    start_hour = last_hour_start.strftime("%H")
    end_hour = last_hour_end.strftime("%H")
    window_folder = f"{start_hour}-{end_hour}"

    return last_hour_start_utc, last_hour_end_utc, last_hour_start.strftime("%Y-%m-%d"), window_folder

# Define schema for the 'message' field (which is a JSON string)
message_schema = StructType([
    StructField("hostname", StringType(), True),
    StructField("app_name", StringType(), True),
    StructField("msg", StringType(), True),
    StructField("severity_num", IntegerType(), True),
    StructField("facility", IntegerType(), True),
    StructField("timestamp", StringType(), True),
    # Add other fields from your JSON message if they exist and you need them
])

# Define schema for the 'host' field (which is a non-standard JSON-like string)
host_schema = StructType([
    StructField("ip_address", StringType(), True), # Assuming the first part is an IP
    StructField("other_value", StringType(), True) # Assuming the second part is some other value, currently null
])


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

df = spark.read.format("org.elasticsearch.spark.sql") \
    .option("es.read.field.as.string", "@timestamp,host,message,level,value") \
    .option("es.read.field.as.array.include", "tags") \
    .load(ES_INDEX) \
    .filter((col("@timestamp") >= lit(start_time)) & (col("@timestamp") < lit(end_time)))

# After loading, explicitly cast again for safety for the fields we know are strings.
df = df.withColumn("host", col("host").cast(StringType())) \
       .withColumn("message", col("message").cast(StringType())) \
       .withColumn("@timestamp", col("@timestamp").cast(StringType())) \
       .withColumn("level", col("level").cast(StringType())) \
       .withColumn("value", col("value").cast(StringType()))

if df.rdd.isEmpty():
    print("##################################################################")
    print("ℹ️  No logs found in Elasticsearch for the previous hour window.")
    print("##################################################################")
    spark.stop()
    exit(0)

# Step 2: Parse the 'message' field as JSON
df = df.withColumn("parsed_message", from_json(col("message"), message_schema))

# Now extract fields from the parsed_message struct
df_parsed = df.withColumn("router_id", col("parsed_message.hostname")) \
    .withColumn("event_type",
                when(col("parsed_message.msg").rlike("(?i)Incorrectly Advertised"), "Incorrectly Advertised")
                .when(col("parsed_message.msg").rlike("(?i)Duplicate"), "Duplicate")
                .when(col("parsed_message.msg").rlike("(?i)High Latency"), "High Latency")
                .when(col("parsed_message.msg").rlike("(?i)reset"), "reset")
                .otherwise(None) # Set to None if no specific event type found
    ) \
    .withColumn("peer_ip", regexp_extract(col("parsed_message.msg"), r"(\d{1,3}(?:\.\d{1,3}){3})", 1)) \
    .withColumn("message_lower", lower(col("parsed_message.msg"))) \
    .withColumn("severity_score", col("parsed_message.severity_num").cast(IntegerType())) \
    .withColumn("message_length", length(col("parsed_message.msg"))) \
    .withColumn("has_keyword_error", col("message_lower").rlike("error|timeout|failed|unreachable|configuration errors").cast("boolean")) \
    .withColumn("event_time", to_timestamp(col("@timestamp"))) # Ensure event_time is created here

# Handle the 'value' column: try to convert to float directly
# Keeping this, but it will be NULL for your current data based on logs
df_parsed = df_parsed.withColumn("parsed_value_float", col("value").cast(FloatType()))

# Handle the 'tags' column:
df_parsed = df_parsed.withColumn("tags_string",
                   when(col("tags").isNotNull(), array_join(col("tags"), ","))
                   .otherwise(lit(None).cast(StringType())))


# Step 3: Select relevant fields
selected_columns = [
    "@timestamp", "@version", "host", "message", "event_time",
    "router_id", "event_type", "peer_ip", "severity_score",
    "message_length", "has_keyword_error", "level", "parsed_value_float",
    "tags", "tags_string", "parsed_message" # Keep parsed_message for debugging if needed, will be dropped before final Pandas conversion
]
df_final = df_parsed.select(*selected_columns)

# --- DEBUGGING START ---
print("===============================================")
print("Debug: df_final schema before ML processing:")
df_final.printSchema()
print("\nDebug: df_final sample rows (showing nulls):")
df_final.show(20, truncate=False) # Show 20 rows, don't truncate long strings

# Corrected: Define ml_df before iterating over its columns for null count
ml_df = df_final.select(
    "router_id", "event_type", "peer_ip", "severity_score",
    "message_length", "has_keyword_error",
    # "parsed_value_float", # Comment out if it's consistently null and not needed for ML
    "tags_string"
)

print("\nDebug: Counting nulls per column in ml_df:")
for c in ml_df.columns:
    print(f"  {c}: {ml_df.filter(col(c).isNull()).count()}") # Use ml_df for counts
print("===============================================")
# --- DEBUGGING END ---


# Add a count before dropping to see how many rows you have
total_rows_before_dropna = ml_df.count()
print(f"Total rows in ml_df before dropna: {total_rows_before_dropna}")


# Define output path early, outside the if/else for saving files
output_path = os.path.join(OUTPUT_DIR, day_str, hour_window)
os.makedirs(output_path, exist_ok=True)
vector_output_path = os.path.join(output_path, "faiss_ready_vectors.pkl")
log_output_path = os.path.join(output_path, "processed_json_logs") # Defined here now


# Step 4: Convert to Pandas for ML processing
# Option 1: Fill NaNs with default values for numeric features
pandas_df = ml_df.fillna({
    "severity_score": 0, # Default to 0 if null
    "message_length": 0, # Default to 0 if null (shouldn't be null if message is not null)
    "has_keyword_error": False, # Default to False if null
    # "parsed_value_float": 0.0, # Uncomment if you keep parsed_value_float and want to fill
    "tags_string": "" # Default to empty string if null
}).toPandas()

# If after fillna, pandas_df is empty, it means all rows were filled with values and then somehow ended up empty.
# This check is more robust for cases where filtering happens earlier.
if pandas_df.empty:
    print("################################################################")
    print("ℹ️  No valid records for ML processing after filtering.")
    print("ℹ️  Skipping PCA and data export.")
    print("################################################################")
else:
    # Step 5: Feature engineering
    # Ensure peer_ip is not None before converting to int
    pandas_df["peer_ip_int"] = pandas_df["peer_ip"].apply(ip_to_int)
    # Ensure hash functions handle None/NaN gracefully
    pandas_df["router_id_hash"] = pandas_df["router_id"].apply(lambda x: hash(x) % 100000 if pd.notnull(x) else 0)
    pandas_df["event_type_hash"] = pandas_df["event_type"].apply(lambda x: hash(x) % 100 if pd.notnull(x) else 0)

    # Convert 'has_keyword_error' boolean to int (0 or 1)
    pandas_df["has_keyword_error_int"] = pandas_df["has_keyword_error"].astype(int)

    feature_cols = [
        "peer_ip_int", "router_id_hash", "event_type_hash",
        "severity_score", "message_length", "has_keyword_error_int",
        # "parsed_value_float" # Uncomment if you re-include it in ml_df.select
    ]

    # Ensure all feature columns are numeric and handle any remaining NaNs
    for col_name in feature_cols:
        if col_name in pandas_df.columns:
            pandas_df[col_name] = pd.to_numeric(pandas_df[col_name], errors='coerce').fillna(0) # Convert to numeric, fill any new NaNs with 0

    # Step 6: PCA for vector compression
    pca = PCA(n_components=2)
    vectors = pca.fit_transform(pandas_df[feature_cols])

    # No need to create output_path or vector_output_path again, they are defined above

    # Save FAISS vectors + extended metadata

    # Prepare json_logs_spark from df_final
    # 1. Parse 'host' column from string to a struct (it's in the format "{ip, null}")
    json_logs_spark = df_final.withColumn(
        "temp_parsed_host",
        from_json(regexp_replace(col("host"), r"\{(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}), (null)\}", r'{"ip_address": "$1", "other_value": $2}'), host_schema)
    )

    # 2. Convert the 'temp_parsed_host' struct into a JSON string
    json_logs_spark = json_logs_spark.withColumn("host_json", to_json(col("temp_parsed_host"))) \
                                     .drop("host", "temp_parsed_host") \
                                     .withColumnRenamed("host_json", "host")

    # 3. Handle 'tags' column (already an array, so to_json should work directly)
    json_logs_spark = json_logs_spark.withColumn("tags_json", to_json(col("tags"))) \
                                     .drop("tags") \
                                     .withColumnRenamed("tags_json", "tags")

    # Drop parsed_message before converting to Pandas to avoid complex objects that Pandas might struggle with
    # (unless you want to handle it specifically in Pandas)
    json_logs_spark = json_logs_spark.drop("parsed_message")

    json_logs = json_logs_spark.toPandas() # Convert to Pandas once here

    # Join with original DataFrame to get full log context
    enriched_df = pandas_df.copy()
    enriched_df["pca_x"] = vectors[:, 0]
    enriched_df["pca_y"] = vectors[:, 1]


    # Safety check in case number of rows differ or indices are not aligned (Pandas default index)
    # The safest way is to join on a unique ID if available, or assume order if no transformations reorder.
    # For this case, we'll assume the order is preserved, but adding a warning.
    metadata = []
    if len(enriched_df) == len(json_logs):
        for i in range(len(enriched_df)):
            metadata.append({
                "peer_ip": enriched_df.loc[i, "peer_ip"],
                "router_id": enriched_df.loc[i, "router_id"],
                "event_type": enriched_df.loc[i, "event_type"],
                "timestamp": str(json_logs.loc[i, "@timestamp"]),
                "message": json_logs.loc[i, "message"],
                "host": json_logs.loc[i, "host"], # This will now be a proper JSON string
                "level": json_logs.loc[i, "level"],
                "parsed_value_float": json_logs.loc[i, "parsed_value_float"], # Keep this if you want it in metadata
                "tags": json_logs.loc[i, "tags"], # This will now be a proper JSON string
                "pca_x": enriched_df.loc[i, "pca_x"],
                "pca_y": enriched_df.loc[i, "pca_y"]
            })
    else:
        print("❗ Warning: Data mismatch in row count between ML features and original logs for metadata. Falling back to partial info.")
        for i in range(len(enriched_df)):
            metadata.append({
                "peer_ip": enriched_df.loc[i, "peer_ip"],
                "router_id": enriched_df.loc[i, "router_id"],
                "event_type": enriched_df.loc[i, "event_type"],
                "timestamp": "unknown",
                "message": "unknown",
                "host": "unknown",
                "level": "unknown",
                "parsed_value_float": "unknown",
                "tags": "unknown",
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
    json_logs_spark.write.mode("overwrite").json(log_output_path)

    print("=========================================================================================")
    print("✅  Processed JSON logs saved to:", log_output_path)
    print("=========================================================================================")

# Completion log
print("=======================================================================================")
print(f"✅  Hourly ETL pipeline completed successfully. Timeframe: {formatted_window}")
print("=======================================================================================")

spark.stop()
