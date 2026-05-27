# app/core/onchain.py

from app.core.wallet import Wallet
from app.utils.tx_logger import log_tx

class OnChainEngine:
    def __init__(self, wallet: Wallet):
        self.wallet = wallet

    def sign_and_send(self, tx):
        signed_tx = self.wallet.sign(tx)

        # simulate sending to blockchain
        signature = f"tx_{hash(signed_tx)}"

        log_tx(signature)

        return {
            "signature": signature,
            "status": "broadcasted"
        }