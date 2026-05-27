# app/orchestrator/memory.py

class AgentMemory:
    """
    Simple in-memory state store (bisa upgrade ke Redis nanti)
    """

    def __init__(self):
        self.store = {}

    def set(self, key: str, value):
        self.store[key] = value

    def get(self, key: str):
        return self.store.get(key)

    def update(self, key: str, value):
        if key in self.store:
            self.store[key].append(value)
        else:
            self.store[key] = [value]