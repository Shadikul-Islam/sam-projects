import json
import random
import socket
import time
from datetime import datetime, timedelta

# Function to send logs to Logstash
def send_to_logstash(log_entry):
    try:
        log_json = json.dumps(log_entry)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(log_json.encode(), (LOGSTASH_HOST, LOGSTASH_PORT))
        sock.close()
    except Exception as e:
        print(f"Error sending log: {e}")

# Function to generate a timestamp
def generate_timestamp(start_time, increment):
    return (start_time + timedelta(seconds=increment)).strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate OSPF state changes
def generate_ospf_flapping(router, interface):
    states = ["Full", "Loading", "Init", "Down"]
    return {
        "hostname": router,
        "app_name": "OSPF",
        "msg": f"OSPF neighbor state on {interface} changed to {random.choice(states)}",
        "severity_num": random.choice([2, 3, 4, 6]),  # Random severity level
        "facility": 23,
        "timestamp": "",
    }

# Function to simulate contributing factors
def generate_contributing_logs(router, issue_type, details):
    return {
        "hostname": router,
        "app_name": "OSPF",
        "msg": f"{issue_type}: {details}",
        "severity_num": random.choice([2, 3, 4, 6]),  # Random severity level
        "facility": 23,
        "timestamp": "",
    }

def simulate_dynamic_ospf_flapping(logstash_host, logstash_port, interval):
    print(f"Sending logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")
    global log_counter

    try:
        while True:
            router = random.choice(routers)
            interface = random.choice(interfaces)
            increment = log_counter * random.randint(5, 10)
            
            if log_counter % 3 == 0:  # Generate OSPF flapping logs
                log_entry = generate_ospf_flapping(router, interface)
            else:  # Generate contributing logs
                issue_type = random.choice(issues)
                details = f"{issue_type} on {interface} of {router}"
                log_entry = generate_contributing_logs(router, issue_type, details)
            
            log_entry["timestamp"] = generate_timestamp(start_time, increment)
            send_to_logstash(log_entry)
            log_counter += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Parameters
routers = ["Router01", "Router02", "Router03"]
interfaces = ["GigabitEthernet0/1", "GigabitEthernet0/2", "GigabitEthernet0/3"]
issues = ["LSA Flooding", "Intermittent Link Connectivity", "High Latency Detected"]
start_time = datetime.now()
log_counter = 0

# Logstash configuration
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash server IP
LOGSTASH_PORT = 514  # Replace with Logstash UDP port
INTERVAL = 5

simulate_dynamic_ospf_flapping(LOGSTASH_HOST, LOGSTASH_PORT, INTERVAL)


