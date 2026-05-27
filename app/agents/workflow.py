class AgentWorkflow:
    def run(self, decision, tools_result, payment_result):
        return {
            "status": "completed",
            "decision": decision,
            "tools": tools_result,
            "payment": payment_result
        }