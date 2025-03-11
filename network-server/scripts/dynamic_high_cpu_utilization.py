import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate CPU utilization logs
def generate_cpu_utilization(router, cpu_usage):
    return {
        "hostname": router,
        "app_name": "System",
        "msg": f"CPU utilization at {cpu_usage}%",
        "severity_num": 4,  # Warning level
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp()
    }

# Function to generate contributing factor logs
def generate_contributing_logs(router, issue_type, details, severity):
    return {
        "hostname": router,
        "app_name": issue_type,
        "msg": details,
        "severity_num": severity,
        "facility": 23,
        "timestamp": generate_timestamp()
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
routers = ["RouterA", "RouterB", "RouterC"]
issues = [
    ("Memory", "High memory usage detected on RouterA"),
    ("Interface", "Interface GigabitEthernet0/1 experiencing errors"),
    ("BGP", "BGP session reset due to high CPU load"),
    ("OSPF", "OSPF adjacency loss detected on RouterB"),
    ("MPLS", "MPLS LSP experiencing packet drops due to resource constraints")
]

# Generate and send logs continuously
def simulate_cpu_utilization_logs(logstash_host, logstash_port, interval):
    print(f"Sending CPU utilization logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            router = random.choice(routers)

            if random.randint(0, 2) == 0:  # Generate high CPU utilization logs randomly
                cpu_usage = random.randint(85, 100)  # Simulate CPU usage between 85% and 100%
                log_entry = generate_cpu_utilization(router, cpu_usage)
            else:  # Generate contributing factor logs
                issue_type, details = random.choice(issues)
                severity = random.choice([2, 3, 4])
                log_entry = generate_contributing_logs(router, issue_type, details, severity)

            send_to_logstash(log_entry, logstash_host, logstash_port)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 10

simulate_cpu_utilization_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

