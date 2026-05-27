# app/core/transaction.py

class TransactionBuilder:
    def build(self, action: str, data: dict):
        return {
            "action": action,
            "data": data,
            "timestamp": "auto"
        }