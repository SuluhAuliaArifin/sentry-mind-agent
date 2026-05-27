# app/utils/audit_logger.py

import json
from datetime import datetime

class AuditLogger:
    def __init__(self, path="audit.log"):
        self.path = path

    def log(self, event_type, data):
        entry = {
            "time": str(datetime.utcnow()),
            "type": event_type,
            "data": data
        }

        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")