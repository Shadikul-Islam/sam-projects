import json
import random
import time
import socket
from datetime import datetime

# Define network devices and issues
devices = ["Router01", "Router02", "Router03"]
interfaces = ["GigabitEthernet0/1", "GigabitEthernet0/2", "FastEthernet0/0"]
issues = {
    "Interface Errors": [
        "%LINK-3-UPDOWN: Interface {}, changed state to down",
        "%IF-4-ERROR: Excessive errors detected on Interface {}",
    ],
    "OSPF Issues": [
        "%OSPF-5-ADJCHG: OSPF neighbor state changed on Interface {} to DOWN",
        "%OSPF-3-ERROR: OSPF adjacency lost on Interface {} due to retransmission failure",
    ],
    "BGP Issues": [
        "%BGP-3-NBR_RESET: BGP neighbor session reset on Interface {}",
        "%BGP-5-PEERDOWN: BGP peer down on Interface {} due to connection failure",
    ],
    "MPLS Issues": [
        "%MPLS-4-LABEL_FAIL: MPLS label distribution failure on Interface {}",
        "%MPLS-3-LSP_FAIL: MPLS LSP down on Interface {}",
    ],
}

# Function to generate a random log entry
def generate_log(issue_type, interface):
    msg = random.choice(issues[issue_type])
    device = random.choice(devices)
    severity = random.randint(2, 6)  # Random severity level
    facility = 23  # Local use
    timestamp = datetime.now().isoformat()
    return {
        "hostname": device,
        "app_name": "IOS",
        "msg": msg.format(interface),
        "severity_num": severity,
        "facility": facility,
        "timestamp": timestamp,
    }

# Function to send logs to Logstash via UDP socket
def send_to_logstash(log_entry, logstash_host, logstash_port):
    try:
        # Convert log to JSON format
        log_json = json.dumps(log_entry)
        
        # Open a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Send the log entry to Logstash
        sock.sendto(log_json.encode(), (logstash_host, logstash_port))
        
        # Close the socket
        sock.close()
    
    except Exception as e:
        print(f"Error sending log: {e}")

# Infinite log generation
def simulate_interface_issues(logstash_host, logstash_port, interval):
    print(f"Sending logs to Logstash at {logstash_host}:{logstash_port} every {interval} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            # Generate root cause (Interface Errors)
            interface = random.choice(interfaces)
            root_log = generate_log("Interface Errors", interface)
            send_to_logstash(root_log, logstash_host, logstash_port)

            time.sleep(interval)  # Wait before sending next batch

    except KeyboardInterrupt:
        print("\nStopped sending logs.")

# Run the infinite log sender
LOGSTASH_HOST = "172.31.20.40"  # Replace with your actual Logstash IP
LOGSTASH_PORT = 514  # Replace with the UDP port your Logstash is listening to
INTERVAL = 5  # Set time interval in seconds

simulate_interface_issues(LOGSTASH_HOST, LOGSTASH_PORT, INTERVAL)

