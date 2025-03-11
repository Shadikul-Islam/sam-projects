import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate interface utilization logs
def generate_interface_utilization(router, interface, utilization):
    return {
        "hostname": router,
        "app_name": "InterfaceMonitor",
        "msg": f"Interface {interface} bandwidth utilization at {utilization}%",
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
interfaces = ["GigabitEthernet0/1", "GigabitEthernet0/2", "GigabitEthernet0/3"]
issues = [
    ("OSPF", "OSPF adjacency loss detected on RouterB"),
    ("MPLS", "MPLS LSP LSP1 experiencing packet drops"),
    ("BGP", "BGP session reset due to congestion on RouterA")
]

# Generate and send logs continuously
def simulate_interface_utilization_logs(logstash_host, logstash_port, interval):
    print(f"Sending interface utilization logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            router = random.choice(routers)

            if random.randint(0, 2) == 0:  # Generate high interface utilization logs randomly
                interface = random.choice(interfaces)
                utilization = random.randint(85, 100)  # Simulate utilization between 85% and 100%
                log_entry = generate_interface_utilization(router, interface, utilization)
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

simulate_interface_utilization_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

