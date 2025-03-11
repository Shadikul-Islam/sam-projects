import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate service outage logs
def generate_service_outage_log(device, issue, severity):
    return {
        "hostname": device,
        "app_name": "ServiceMonitor",
        "msg": f"Service Outage: {issue}",
        "severity_num": severity,  # 3 = Error, 2 = Critical
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp(),
        "service": random.choice(["WebServer", "Database", "AuthenticationService", "LoadBalancer"]),
        "impact": random.choice(["Partial Outage", "Full Outage"])
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
devices = ["LoadBalancer01", "WebServer01", "Database01", "AuthService01"]
issues = [
    "Misconfigured load balancer caused traffic misrouting",
    "Database connection pool exhausted",
    "Authentication service failure",
    "High memory usage on load balancer causing instability",
    "Web server unable to handle incoming requests"
]

# Generate and send logs continuously
def simulate_service_outage_logs(logstash_host, logstash_port, interval):
    print(f"Sending service outage logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            device = random.choice(devices)
            issue = random.choice(issues)
            severity = random.choice([2, 3])  # Randomly assign severity (Critical or Error)

            log_entry = generate_service_outage_log(device, issue, severity)
            send_to_logstash(log_entry, logstash_host, logstash_port)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 5

simulate_service_outage_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

