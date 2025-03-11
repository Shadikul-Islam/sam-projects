import json
import random
import socket
import time
from datetime import datetime, timedelta

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate prefix-related issues
def generate_bgp_prefix_issue(router, peer_ip, issue_type):
    return {
        "hostname": router,
        "app_name": "BGP",
        "msg": f"{issue_type} prefixes from peer {peer_ip}",
        "severity_num": 2,
        "facility": 23,
        "timestamp": generate_timestamp(),
    }

# Function to generate contributing logs
def generate_contributing_logs(router, issue_type, details):
    return {
        "hostname": router,
        "app_name": "BGP",
        "msg": f"{issue_type}: {details}",
        "severity_num": 3,
        "facility": 23,
        "timestamp": generate_timestamp(),
    }

# Function to generate BGP session reset logs
def generate_bgp_flap(router, peer_ip):
    return {
        "hostname": router,
        "app_name": "BGP",
        "msg": f"BGP session to peer {peer_ip} reset due to flapping",
        "severity_num": 4,
        "facility": 23,  # Local use 7
        "timestamp": generate_timestamp(),
    }

# Function to send logs to Logstash
def send_to_logstash(log_entry,logstash_host, logstash_port):
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
routers = ["Router01", "Router02", "Router03"]
peer_ips = ["192.168.1.1", "192.168.2.1", "192.168.3.1"]
prefix_issues = ["Missing", "Duplicate", "Incorrectly Advertised"]
contributing_factors = ["High Latency", "Intermittent Connectivity", "Configuration Errors"]

# Generate and send logs infinitely until manually stopped
def simulate_bgp_route_instability(logstash_host, logstash_port, interval):
    print(f"Sending logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            for _ in range(10):  # Send 10 logs per interval
                router = random.choice(routers)
                peer_ip = random.choice(peer_ips)
                
                log_type = random.randint(0, 2)  # Randomly choose log type
                
                if log_type == 0:  # Generate BGP session reset logs
                    log_entry = generate_bgp_flap(router, peer_ip)
                elif log_type == 1:  # Generate prefix-related issues
                    issue_type = random.choice(prefix_issues)
                    log_entry = generate_bgp_prefix_issue(router, peer_ip, issue_type)
                else:  # Generate contributing logs
                    issue_type = random.choice(contributing_factors)
                    details = f"{issue_type} impacting peer {peer_ip}"
                    log_entry = generate_contributing_logs(router, issue_type, details)

                # Send log to Logstash
                send_to_logstash(log_entry, logstash_host, logstash_port)

            # Sleep after sending 10 logs
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash server details
LOGSTASH_HOST = "172.31.20.40"  # Replace with Logstash IP
LOGSTASH_PORT = 514  # Default syslog UDP port

# Define the time interval (in seconds) between log entries
LOG_INTERVAL = 10

simulate_bgp_route_instability(LOGSTASH_HOST, LOGSTASH_PORT, LOG_INTERVAL)
