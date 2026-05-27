# app/core/solana_wallet.py

import base58

class SolanaWallet:
    def __init__(self, private_key: str):
        """
        private_key = base58 encoded secret key
        """
        self.private_key = private_key

    def sign_transaction(self, tx: dict):
        """
        Simulated real signing interface (ready for solana-py integration)
        """
        payload = str(tx) + self.private_key
        signature = str(abs(hash(payload)))

        return {
            "signed": True,
            "signature": signature
        }