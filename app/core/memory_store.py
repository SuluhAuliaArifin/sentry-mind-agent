# app/core/memory_store.py

import json
import os

class MemoryStore:
    """
    Simple persistent memory (file-based fallback Redis)
    """

    def __init__(self, path="memory.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r") as f:
            return json.load(f)

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def set(self, key, value):
        self.data[key] = value
        self._save()

    def get(self, key):
        return self.data.get(key)

    def append(self, key, value):
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        self._save()