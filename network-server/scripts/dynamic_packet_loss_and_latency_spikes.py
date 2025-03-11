import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate logs for packet loss and latency issues
def generate_network_log(device, segment, issue, details, severity):
    return {
        "hostname": device,
        "app_name": "NetworkMonitoring",
        "msg": f"{issue}: {details}",
        "severity_num": severity,  # 4 = Warning, 3 = Error
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp(),
        "network_segment": segment
    }

# Function to send logs to Logstash
def send_to_logstash(log_entry, logstash_host, logstash_port):
    try:
        log_json = json.dumps(log_entry)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(log_json.encode(), (logstash_host, logstash_port))
        sock.close()
    except Exception as e:
        print(f"Error sending log: {e}")

# Parameters
devices = ["Router01", "Router02", "Switch01", "Switch02"]
segments = ["SegmentA", "SegmentB", "SegmentC"]
issues = [
    ("Packet Loss", "Packet loss exceeded threshold (5%)"),
    ("Latency Spike", "Latency spiked above 100ms"),
    ("Congestion", "High bandwidth usage detected"),
    ("Dropped Packets", "Packets dropped due to buffer overflow"),
    ("Interface Errors", "Errors detected on interface GigabitEthernet0/1")
]

# Generate and send logs continuously
def simulate_network_logs(logstash_host, logstash_port, interval):
    print(f"Sending network logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            device = random.choice(devices)
            segment = random.choice(segments)
            issue, details = random.choice(issues)
            severity = random.choice([3, 4])  # Randomly assign severity (Error or Warning)

            log_entry = generate_network_log(device, segment, issue, details, severity)
            send_to_logstash(log_entry, logstash_host, logstash_port)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 5

simulate_network_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

