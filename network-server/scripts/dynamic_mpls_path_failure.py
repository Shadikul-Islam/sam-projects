import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate MPLS path failure logs
def generate_mpls_failure(router, lsp_id):
    return {
        "hostname": router,
        "app_name": "MPLS",
        "msg": f"LSP {lsp_id} failure detected due to path loss",
        "severity_num": 3,  # Error level
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp()
    }

# Function to generate misrouted packet logs
def generate_mpls_misroute(router, src_ip, dst_ip):
    return {
        "hostname": router,
        "app_name": "MPLS",
        "msg": f"Packet from {src_ip} to {dst_ip} misrouted",
        "severity_num": 4,  # Warning level
        "facility": 23,
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
lsp_ids = ["LSP1", "LSP2", "LSP3"]
ips = ["192.168.1.1", "192.168.2.2", "192.168.3.3"]
issues = [
    ("OSPF", "OSPF adjacency loss detected on RouterA"),
    ("BGP", "BGP session reset on peer 192.168.1.2"),
    ("Interface", "Interface GigabitEthernet0/1 down on RouterB")
]

# Generate and send logs continuously
def simulate_mpls_logs(logstash_host, logstash_port, interval):
    print(f"Sending MPLS logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            router = random.choice(routers)

            log_type = random.randint(0, 2)  # Randomly choose log type

            if log_type == 0:  # Generate MPLS path failure logs
                lsp_id = random.choice(lsp_ids)
                log_entry = generate_mpls_failure(router, lsp_id)
            elif log_type == 1:  # Generate MPLS misrouted packet logs
                src_ip = random.choice(ips)
                dst_ip = random.choice([ip for ip in ips if ip != src_ip])
                log_entry = generate_mpls_misroute(router, src_ip, dst_ip)
            else:  # Generate contributing factor logs
                issue_type, details = random.choice(issues)
                severity = random.choice([2, 4])
                log_entry = generate_contributing_logs(router, issue_type, details, severity)

            send_to_logstash(log_entry, logstash_host, logstash_port)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 5

simulate_mpls_logs(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)

