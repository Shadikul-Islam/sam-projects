import json
import random
import socket
import time
from datetime import datetime, timedelta

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate hardware degradation logs
def generate_hardware_issue(router, issue_type, details, severity):
    return {
        "hostname": router,
        "app_name": "HardwareMonitor",
        "msg": f"{issue_type}: {details}",
        "severity_num": severity,
        "facility": 23,  # Local use 7
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
routers = ["RouterX", "RouterY", "RouterZ"]
issues = [
    ("CRC", "High CRC error count on GigabitEthernet0/1"),
    ("Temperature", "Device temperature exceeds safe threshold (85°C)"),
    ("Power", "Power supply unit failure detected on slot 1"),
    ("Fan", "Fan speed below operational threshold on slot 2"),
    ("Memory", "Critical memory utilization due to hardware degradation"),
]

# Generate and send logs continuously
def simulate_hardware_issues(logstash_host, logstash_port, interval):
    print(f"Sending hardware degradation logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            router = random.choice(routers)
            issue_type, details = random.choice(issues)
            severity = random.choice([2, 3, 4])

            log_entry = generate_hardware_issue(router, issue_type, details, severity)
            send_to_logstash(log_entry, logstash_host, logstash_port)

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 10

simulate_hardware_issues(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

