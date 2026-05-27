# app/core/chain_executor.py

from app.utils.tx_logger import log_tx
from app.core.solana_wallet import SolanaWallet

class ChainExecutor:
    def __init__(self, wallet: SolanaWallet):
        self.wallet = wallet

    def send_transaction(self, tx: dict):
        signed = self.wallet.sign_transaction(tx)

        # simulate broadcast result (replace with real RPC later if needed)
        tx_hash = "SOL_" + signed["signature"]

        log_tx(tx_hash)

        return {
            "success": True,
            "tx_hash": tx_hash,
            "explorer": f"https://explorer.solana.com/tx/{tx_hash}"
        }