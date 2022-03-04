import boto3
import json
import os
from lib.ddb import AdptDynamoDB
from datetime import datetime
from tcp_latency import measure_latency

# initialization
ddb_table = os.environ["TCP_LATENCY_TABLE"]
defaults = {
    "hostname": "www.google.com",
    "port": 80,
    "iterations": 3,
    "timeout": 5
}
hostname = os.getenv("TARGET_HOSTNAME", defaults["hostname"])
port = int(os.getenv("TARGET_PORT", defaults["port"]))
iterations = int(os.getenv("TARGET_ITERATIONS", defaults["iterations"]))
timeout = int(os.getenv("TARGET_TIMEOUT", defaults["timeout"]))
session = boto3.session.Session()
adpt_ddb = AdptDynamoDB(session, ddb_table)

# helper functions
def build_response(code, body):
    headers = {
        "Content-Type": "application/json"
    }
    response = {
        "isBase64Encoded": False,
        "statusCode": code,
        "headers": headers,
        "body": body
    }
    return response

def get_attrib(event, attrib):
    return event[attrib] if attrib in event else defaults[attrib]

def do_tcp_latency(hostname, port, iterations, timeout):
    return measure_latency(host=hostname, port=port, runs=iterations, timeout=timeout)

def persist(payload):
    item = {
        "hostname": {"S": payload["hostname"]} ,
        "timestamp": {"S": payload["timestamp"]},
        "port": {"N": str(payload["port"])},
        "iterations": {"N": str(payload["iterations"])},
        "timeout": {"N": str(payload["timeout"])},
        "latencies_ms": {"S": json.dumps(payload["latencies_ms"])}
    }
    print(json.dumps(item))
    response = adpt_ddb.put(item)
    if response == 200:
        pass
        # print("successfully persisted {} at {}".format(payload["hostname"], payload["timestamp"]))
    else:
        print("failed to persist {} at {}".format(payload["hostname"], payload["timestamp"]))

def handler(event, context):
    # hostname = get_attrib(event, "hostname")
    # port = get_attrib(event, "port")
    # iterations = get_attrib(event, "iterations")
    # timeout = get_attrib(event, "timeout")
    timestamp = datetime.now().isoformat()
    latencies = do_tcp_latency(hostname, port, iterations, timeout)
    output = {
        "timestamp": timestamp,
        "hostname": hostname,
        "port": port,
        "iterations": iterations,
        "timeout": timeout,
        "latencies_ms": latencies
    }
    persist(output)
    return output
