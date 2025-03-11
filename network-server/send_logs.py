import syslog
import json
import time
import datetime
import os
import socket

severity_map = {  # Mapping numeric severity to string severity
    0: "emergency",
    1: "alert",
    2: "critical",
    3: "error",
    4: "warning",
    5: "notice",
    6: "informational",
    7: "debug"
}

severity_map_syslog = {  # Mapping string severity to syslog level
    "emergency": syslog.LOG_EMERG,
    "alert": syslog.LOG_ALERT,
    "critical": syslog.LOG_CRIT,
    "error": syslog.LOG_ERR,
    "warning": syslog.LOG_WARNING,
    "notice": syslog.LOG_NOTICE,
    "informational": syslog.LOG_INFO,
    "debug": syslog.LOG_DEBUG
}

def send_log(host, json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file}'.")
        return

    for log_entry in data:
        try:
            if isinstance(log_entry.get('timestamp'), str):
                try:
                    log_entry['timestamp'] = datetime.datetime.fromisoformat(log_entry['timestamp']).isoformat()
                except ValueError:
                    print(f"Warning: Invalid timestamp format: {log_entry.get('timestamp')}. Using current time.")
                    log_entry['timestamp'] = datetime.datetime.now().isoformat()
            else:
                log_entry['timestamp'] = datetime.datetime.now().isoformat()
        except (ValueError, TypeError) as e:
            print(f"Timestamp Error: {e}")
            log_entry['timestamp'] = datetime.datetime.now().isoformat()

        try:
            numeric_severity = log_entry.get('severity_num')
            severity = severity_map.get(numeric_severity, "informational")  # Default to informational
            log_entry['severity'] = severity #Adding string severity to the log entry
            log_message = json.dumps(log_entry)

            syslog_level = severity_map_syslog.get(severity, syslog.LOG_INFO)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(log_message.encode(), (host, 514))
            except Exception as e:
                print(f"Error sending message via socket: {e}")
            finally:
                sock.close()

            #syslog.syslog(syslog_level, log_message) # For local syslog (optional)

        except TypeError as e:
            print(f"JSON Encoding Error: {e}")
            print(f"Problematic log entry: {log_entry}")
        except Exception as e:
            print(f"Syslog/General Error: {e}")


if __name__ == "__main__":
    elk_host = "172.31.20.40"  # Replace with your Logstash host
    json_files = [
        "syslogen_data/cisco_informational.json", # Combined log file
    ]
    while True:
        for json_file in json_files:
            send_log(elk_host, json_file)
            time.sleep(10) # Delay so logs aren't sent too fast
