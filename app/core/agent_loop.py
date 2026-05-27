class AgentLoop:
    def __init__(self, analyzer, executor):
        self.analyzer = analyzer
        self.executor = executor

    def run(self, event):
        analysis = self.analyzer.process(event)

        if analysis["action_required"]:
            result = self.executor.execute(analysis["action"])

            return {
                "event": event,
                "analysis": analysis,
                "execution": result
            }

        return {
            "event": event,
            "analysis": analysis,
            "execution": None
        }