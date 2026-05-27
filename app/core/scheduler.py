import asyncio
from app.database.db import SessionLocal
from app.database.models import Target
from app.agents.loop import agent_cycle, run_scan_for_target

async def autonomous_loop():
    while True:
        db = SessionLocal()
        targets = db.query(Target).filter(Target.enabled == True).all()
        db.close()

        for target in targets:
            decision = await agent_cycle(target.id)

            if decision:
                asyncio.create_task(run_scan_for_target(target.id))

        await asyncio.sleep(60)