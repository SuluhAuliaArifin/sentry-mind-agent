import asyncio
from app.tasks.scan_tasks import run_scan_cycle

class AutonomousAgent:
    def __init__(self):
        self.running = True

    async def start(self):
        print("[AGENT] Autonomous loop started")

        while self.running:
            try:
                await run_scan_cycle()
            except Exception as e:
                print(f"[AGENT ERROR] {e}")

            # interval scan otomatis
            await asyncio.sleep(60)  # 1 menit

    def stop(self):
        self.running = False