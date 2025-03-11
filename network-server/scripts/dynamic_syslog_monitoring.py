import json
import random
import socket
import time
from datetime import datetime

# Function to generate a timestamp
def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Function to generate a random log entry
def generate_log():
    routers = ["Router01", "Router02", "Router03"]
    events = [
        {"msg": "%LINK-3-UPDOWN: Interface GigabitEthernet{}/1, changed state to up", "severity": 6},
        {"msg": "%SYS-5-CONFIG_I: Configured from console by admin", "severity": 6},
        {"msg": "%LINEPROTO-5-UPDOWN: Line protocol on Interface FastEthernet{}/0, changed state to up", "severity": 6},
        {"msg": "%LINK-3-UPDOWN: Interface GigabitEthernet{}/2, changed state to down", "severity": 6},
        {"msg": "%SYS-5-RESTART: System restarted due to power cycle", "severity": 5},
        {"msg": "%DHCP-6-ADDRESS_ASSIGN: DHCP address 192.168.1.100 assigned to client", "severity": 6},
        {"msg": "%SECURITY-6-PACKET_ACCEPT: Packet accepted from source 192.168.2.10", "severity": 6},
    ]
    
    router = random.choice(routers)
    event = random.choice(events)
    interface_id = random.randint(0, 3)
    log_entry = {
        "hostname": router,
        "app_name": "IOS",
        "msg": event["msg"].format(interface_id),
        "severity_num": event["severity"],
        "facility": 23,  # Local use code
        "timestamp": generate_timestamp(),
    }
    return log_entry

# Function to send logs to Logstash (via syslog)
def send_to_logstash(log_entry, logstash_host, logstash_port):
    try:
        log_json = json.dumps(log_entry)
        
        # Open UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Send log to Logstash server
        sock.sendto(log_json.encode(), (logstash_host, logstash_port))
        
        sock.close()
    
    except Exception as e:
        print(f"Error sending log: {e}")

# Simulate log generation and sending
def simulate_logs(logstash_host, logstash_port, duration=60, interval=5):
    print(f"Sending logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            log_entry = generate_log()
            send_to_logstash(log_entry, logstash_host, logstash_port)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Logstash details
LOGSTASH_HOST = "172.31.20.40"  # Replace with your Logstash server IP
LOGSTASH_PORT = 514  # Syslog UDP port

# Define the time interval (in seconds) between log entries and the simulation duration
LOG_INTERVAL = 5
DURATION = 60  # 1 minute simulation

simulate_logs(LOGSTASH_HOST, LOGSTASH_PORT, duration=DURATION, interval=LOG_INTERVAL)

