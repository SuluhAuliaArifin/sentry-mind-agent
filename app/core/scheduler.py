import asyncio
from app.agent.loop import AutonomousAgent

agent = AutonomousAgent()

async def start_scheduler():
    print("[SCHEDULER] Starting autonomous agent...")

    asyncio.create_task(agent.start())