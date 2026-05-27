import asyncio
from app.database.db import SessionLocal
from app.database.models import Target
from app.agents.loop import agent_cycle
from app.agents.core import run_scan_for_target

class AutonomousEngine:
    def __init__(self):
        self.running = True

    async def run(self):
        print("[AUTONOMOUS] engine started")

        while self.running:
            db = SessionLocal()
            targets = db.query(Target).filter(Target.enabled == True).all()
            db.close()

            for target in targets:
                should_scan = await agent_cycle(target.id)

                if should_scan:
                    print(f"[AUTO] scanning target {target.id}")
                    asyncio.create_task(run_scan_for_target(target.id))
                else:
                    print(f"[SKIP] target {target.id}")

            await asyncio.sleep(60)

    def stop(self):
        self.running = False


engine = AutonomousEngine()