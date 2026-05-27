# app/integrations/synapse.py

from app.core.rpc import SynapseRPC

rpc = SynapseRPC()

class SynapseClient:
    def send(self, payload):
        return rpc.post({
            "jsonrpc": "2.0",
            "method": "execute",
            "params": payload
        })