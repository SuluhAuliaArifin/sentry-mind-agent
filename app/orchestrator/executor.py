# app/orchestrator/executor.py

from app.services.ace import AceDataClient
from app.core.rpc import SynapseRPC
from app.core.sentinel import execute_sentinel
from app.core.onchain import OnChainEngine
from app.core.wallet import Wallet
from app.core.transaction import TransactionBuilder
from app.core.chain_executor import ChainExecutor
from app.core.solana_wallet import SolanaWallet
from app.integrations.sentinel_client import SentinelClient


# ✅ Core services
ace = AceDataClient()
rpc = SynapseRPC()

# ✅ Wallet layers (keduanya tetap dipakai)
base_wallet = Wallet()
solana_wallet = SolanaWallet("demo-private-key")

# ✅ Chain engines
onchain = OnChainEngine(base_wallet)
tx_builder = TransactionBuilder()
chain = ChainExecutor(solana_wallet)

# ✅ Sentinel client
sentinel = SentinelClient()


def execute_task(plan: dict):
    results = {
        "task": plan.get("task"),
        "strategy": plan.get("strategy", []),
        "executions": []
    }

    # =========================
    # 🔵 ACE LAYER
    # =========================
    if "ace_analysis" in results["strategy"]:
        ace_result = ace.enforce_multi_api(plan["task"])
        results["executions"].append({
            "type": "ace",
            "data": ace_result
        })
    else:
        # tetap jalankan seperti versi kedua
        ace_result = ace.enforce_multi_api(plan["task"])
        results["executions"].append({
            "type": "ace_auto",
            "data": ace_result
        })

    # =========================
    # 🔵 RPC LAYER
    # =========================
    if "rpc_balance_check" in results["strategy"]:
        rpc_result = rpc.get_balance(base_wallet.public_key)
        results["executions"].append({
            "type": "rpc",
            "data": rpc_result
        })

    # =========================
    # 🔵 SENTINEL LAYER (DUA MODE)
    # =========================
    if "sentinel_execution" in results["strategy"]:
        sentinel_result_core = execute_sentinel(plan)
        results["executions"].append({
            "type": "sentinel_core",
            "data": sentinel_result_core
        })

    # versi client sentinel (tidak dihapus)
    sentinel_result_client = sentinel.execute(plan)
    results["executions"].append({
        "type": "sentinel_client",
        "data": sentinel_result_client
    })

    # =========================
    # 🔴 ON-CHAIN LAYER (DUA ENGINE)
    # =========================

    # 1️⃣ TransactionBuilder + OnChainEngine
    tx_built = tx_builder.build("agent_action", results)
    tx_hash_onchain = onchain.sign_and_send(tx_built)

    results["executions"].append({
        "type": "onchain_engine",
        "tx_hash": tx_hash_onchain
    })

    # 2️⃣ ChainExecutor + SolanaWallet
    tx_simple = {
        "action": plan.get("task"),
        "strategy": plan.get("strategy", [])
    }

    chain_result = chain.send_transaction(tx_simple)

    results["executions"].append({
        "type": "chain_executor",
        "result": chain_result
    })

    return results