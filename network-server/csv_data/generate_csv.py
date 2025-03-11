import json
import datetime
import csv
import os

# Severity mapping (matching Logstash)
severity_map = {
    0: "emergency",
    1: "alert",
    2: "critical",
    3: "error",
    4: "warning",
    5: "notice",
    6: "informational",
    7: "debug"
}

CSV_FILE = "ecs_logs.csv"

# ECS headers (matching Logstash output)
ECS_HEADERS = [
    "@timestamp", "host.ip", "host.name", "log.level", "log.level_num",
    "observer.product", "message", "full_log.json"
]

# Ensure CSV file exists and has headers
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(ECS_HEADERS)

# Write multiple log entries to CSV in bulk
def write_to_csv(log_entries):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_ALL)  # Quote all fields
        for log_entry in log_entries:
            writer.writerow([
                log_entry["@timestamp"],
                log_entry["host.ip"],  # Ensure this field is present
                log_entry["host.name"],
                log_entry["log.level"],
                log_entry["log.level_num"],
                log_entry["observer.product"],
                log_entry["message"].replace("\n", " "),
                log_entry["full_log.json"],
            ])

# Process log file and save logs to CSV
def process_logs(json_file, num_logs):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file}'.")
        return

    if not isinstance(data, list) or len(data) == 0:
        print(f"Error: No valid logs found in '{json_file}'")
        return

    log_entries = []
    base_time = datetime.datetime.now(datetime.timezone.utc)  # Updated line to avoid deprecation warning

    for i in range(num_logs):
        log_entry = data[i % len(data)].copy()  # Copy original entry

        # Generate unique timestamps by adding seconds
        timestamp = (base_time + datetime.timedelta(seconds=i)).strftime('%Y-%m-%dT%H:%M:%S')
        log_entry["@timestamp"] = timestamp

        # Process severity
        numeric_severity = log_entry.get('severity_num', 6)  # Default to "informational"
        severity = severity_map.get(numeric_severity, "informational")

        log_entry["log.level"] = severity
        log_entry["log.level_num"] = numeric_severity

        # Map ECS fields
        log_entry["host.name"] = log_entry.get("hostname", "unknown")
        log_entry["observer.product"] = log_entry.get("app_name", "unknown")
        log_entry["message"] = log_entry.get("msg", "unknown")
        log_entry["full_log.json"] = json.dumps(log_entry)

        # Add `host.ip` if available (assuming it's part of the log)
        log_entry["host.ip"] = log_entry.get("host_ip", "172.31.9.215")  # Placeholder if not found

        log_entries.append(log_entry)

        if len(log_entries) >= 1000:  # Write in batches of 1000
            write_to_csv(log_entries)
            log_entries = []

    # Write remaining logs
    if log_entries:
        write_to_csv(log_entries)

    print(f"Saved {num_logs} logs to {CSV_FILE}")

# Main execution
if __name__ == "__main__":
    json_file = "cisco_informational.json"  # Your log file
    initialize_csv()  # Ensure CSV structure is set up
    process_logs(json_file, num_logs=30000)  # Save 30000 logs
