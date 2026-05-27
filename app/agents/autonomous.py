import asyncio
from app.database.db import SessionLocal
from app.database.models import Target
from app.agents.loop import agent_cycle
from app.agents.core import run_scan_for_target
from app.core.rpc import SynapseRPC
from app.core.sap import SAPClient
from app.core.payment import X402Client
from app.services.ace import AceDataClient

# ✅ Infrastructure Clients
rpc = SynapseRPC()
sap = SAPClient()
x402 = X402Client()
ace = AceDataClient()


# ✅ Balance Check (On-chain validation)
def check_balance(wallet_pubkey: str):
    return rpc.get_balance(wallet_pubkey)


# ✅ AI Processing (3 Ace APIs minimum)
async def process_task(task: str):
    result = await ace.enforce_multi_api(task)

    return {
        "decision": result["llm"],           # LLM reasoning
        "embedding": result["embedding"],    # Embedding API
        "risk": result["classification"]     # Classification API
    }


class AutonomousEngine:
    def __init__(self, wallet_pubkey: str):
        self.running = True
        self.wallet = wallet_pubkey

    async def run(self):
        print("[AUTONOMOUS] Engine started")

        # ✅ Ensure agent registered on SAP
        await sap.ensure_registered(self.wallet)

        while self.running:
            db = SessionLocal()
            targets = db.query(Target).filter(Target.enabled == True).all()
            db.close()

            for target in targets:

                # ✅ 1. Agent reasoning
                should_scan = await agent_cycle(target.id)

                if not should_scan:
                    print(f"[SKIP] target {target.id}")
                    continue

                print(f"[AUTO] scanning target {target.id}")

                # ✅ 2. Discover tool via SAP
                tool = await sap.discover_tool("security-scan")

                # ✅ 3. Payment via x402 (Escrow / Facilitator)
                tx_hash = await x402.pay(
                    wallet=self.wallet,
                    amount=tool.price,
                    tool_id=tool.id
                )

                print(f"[PAYMENT] settled tx: {tx_hash}")

                # ✅ 4. Use Synapse Sentinel at least once
                sentinel_result = await sap.call_sentinel(
                    "threat-analysis",
                    {"target_id": target.id}
                )

                print("[SENTINEL]", sentinel_result)

                # ✅ 5. Execute main scan
                asyncio.create_task(run_scan_for_target(target.id))

            await asyncio.sleep(60)

    def stop(self):
        self.running = False


# ✅ Engine instance
engine = AutonomousEngine(wallet_pubkey="YOUR_AGENT_WALLET")