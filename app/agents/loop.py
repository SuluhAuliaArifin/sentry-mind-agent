from app.services.ai_engine import analyze_scan_results
from app.database.db import SessionLocal
from app.database.models import Scan

def observe(target_id):
    db = SessionLocal()
    scans = db.query(Scan).filter(Scan.target_id == target_id).all()
    db.close()
    return scans


def reason(state):
    return analyze_scan_results(state)


def decide(analysis):
    return analysis["risk"] == "HIGH"


async def agent_cycle(target_id):
    state = observe(target_id)
    analysis = reason(state)
    return decide(analysis)