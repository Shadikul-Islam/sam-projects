import json
import random
import socket
import time
from datetime import datetime, timedelta

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate logs for configuration drift
def generate_config_drift_log(device, config_change, severity):
    return {
        "hostname": device,
        "app_name": "ConfigurationManagement",
        "msg": f"Configuration Drift Detected: {config_change}",
        "severity_num": severity,  # 4 = Warning, 3 = Error
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp(),
        "configuration_version": random.choice(["v1.0", "v1.1", "v1.2", "v2.0"])
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
config_changes = [
    "OSPF area configuration mismatch",
    "BGP neighbor authentication key mismatch",
    "Access Control List (ACL) policy discrepancy",
    "QoS policy configuration drift",
    "Incorrect VLAN assignment",
    "SNMP community string changed unexpectedly"
]

# Generate and send logs indefinitely
def simulate_config_drift_logs(logstash_host, logstash_port, interval):
    print(f"Sending configuration drift logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")
    
    try:
        while True:
            device = random.choice(devices)
            config_change = random.choice(config_changes)
            severity = random.choice([2, 3, 4, 6])  # Randomly assign severity (Error or Warning)
            
            log_entry = generate_config_drift_log(device, config_change, severity)
            
            send_to_logstash(log_entry, logstash_host, logstash_port)
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 10

simulate_config_drift_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

