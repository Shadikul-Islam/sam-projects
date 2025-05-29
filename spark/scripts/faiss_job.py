from pyspark.sql import SparkSession
import datetime

# Create Spark session
spark = SparkSession.builder \
    .appName("ElasticsearchLastMinutePull") \
    .config("spark.es.nodes", "52.6.4.88") \
    .config("spark.es.port", "9200") \
    .config("spark.es.net.http.auth.user", "elastic") \
    .config("spark.es.net.http.auth.pass", "0wBH-ZP1y=olUiV_J7bb") \
    .config("spark.es.nodes.wan.only", "true") \
    .config("spark.es.net.ssl", "true") \
    .config("spark.es.net.ssl.cert.allow.self.signed", "true") \
    .getOrCreate()

# Build query to filter data from last 1 minute
es_query = """
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1m",
        "lt": "now"
      }
    }
  }
}
"""

# Read data from Elasticsearch using the query
df = spark.read.format("org.elasticsearch.spark.sql") \
    .option("es.resource", "network_logs") \
    .option("es.query", es_query) \
    .load()

# Show sample results
df.show(10, truncate=False)

# Save to file (e.g., JSON) with timestamped filename
output_path = "/opt/spark_output/anomalies_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
df.write.mode("overwrite").json(output_path)

print(f"Saved last 1 minute of logs to: {output_path}")
