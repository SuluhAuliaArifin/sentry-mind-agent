import json
from datetime import datetime

MEMORY_FILE = "agent_memory.json"

def store_result(data: dict):
    try:
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    except:
        memory = []

    memory.append({
        "timestamp": str(datetime.utcnow()),
        "data": data
    })

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def get_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []