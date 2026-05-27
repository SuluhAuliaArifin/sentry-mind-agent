import json
from datetime import datetime

def log_event(data):
    with open("agent_logs.jsonl", "a") as f:
        f.write(json.dumps({
            "time": str(datetime.utcnow()),
            "data": data
        }) + "\n")