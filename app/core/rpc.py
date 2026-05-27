# app/core/rpc.py

import os
import requests
from typing import Any, Dict

class SynapseRPC:
    """
    RPC abstraction layer untuk semua on-chain / agent interaction.
    Bisa diarahkan ke Synapse RPC atau fallback endpoint.
    """

    def __init__(self):
        self.primary_rpc = os.getenv("SYNAPSE_RPC_URL")
        self.fallback_rpc = os.getenv("FALLBACK_RPC_URL", "https://api.mainnet-beta.solana.com")

    def _get_endpoint(self):
        return self.primary_rpc if self.primary_rpc else self.fallback_rpc

    def post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic RPC call wrapper
        """
        url = self._get_endpoint()

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=15
            )
            response.raise_for_status()

            return {
                "success": True,
                "data": response.json(),
                "endpoint": url
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "endpoint": url
            }

    def get_balance(self, pubkey: str):
        return self.post({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [pubkey]
        })

    def send_transaction(self, tx: str):
        return self.post({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [tx]
        })