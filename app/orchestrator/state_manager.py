# app/orchestrator/state_manager.py

from app.orchestrator.memory import AgentMemory

state = AgentMemory()


def save_state(key, value):
    state.set(key, value)


def get_state(key):
    return state.get(key)


def log_state(event):
    state.update("events", event)