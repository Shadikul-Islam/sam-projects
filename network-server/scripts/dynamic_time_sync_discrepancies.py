import json
import random
import socket
import time
from datetime import datetime, timedelta

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate NTP-related logs
def generate_time_sync_log(device, details, severity):
    return {
        "hostname": device,
        "app_name": "NTP",
        "msg": details,
        "severity_num": severity,
        "facility": 22,  # Local use 22
        "timestamp": generate_timestamp(),
    }

# Function to send logs to Logstash
def send_to_logstash(log_entry, logstash_host, logstash_port):
    try:
        # Convert log to JSON format
        log_json = json.dumps(log_entry)
        
        # Open a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Send the log entry
        sock.sendto(log_json.encode(), (logstash_host, logstash_port))
        
        # Close the socket
        sock.close()
    
    except Exception as e:
        print(f"Error sending log: {e}")

# Parameters
devices = ["Router01", "Router02", "Router03"]
issues = [
    ("Offset", "NTP offset exceeds acceptable threshold (120ms)"),
    ("Sync Failure", "NTP synchronization failed with primary server"),
    ("Drift", "High clock drift detected on device"),
    ("Server Unreachable", "NTP server unreachable"),
    ("Clock Reset", "Clock reset to factory defaults due to sync issues"),
]

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Generate and send logs infinitely until manually stopped
def simulate_ntp_sync_issues(logstash_host, logstash_port, interval):
    print(f"Sending logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            device = random.choice(devices)
            issue_type, message = random.choice(issues)  # Extract message from the tuple
            severity = random.choice([2, 4])  # Random severity
            
            # Create the log entry in the standard format
            log_entry = generate_time_sync_log(device, message, severity)
            
            # Send the log entry to Logstash
            send_to_logstash(log_entry, logstash_host, logstash_port)

            # Wait for the defined interval before generating the next log
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 5

simulate_ntp_sync_issues(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

