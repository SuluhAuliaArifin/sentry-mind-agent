import random
from typing import Dict, Any


class AgentBrain:
    """
    Simple decision engine for autonomous agent.
    Ini nanti bisa kamu upgrade ke LLM / SAP tool selector.
    """

    def decide(self, target: Dict[str, Any], tools: list) -> Dict[str, Any]:
        """
        Input:
            target = data target (url, id, dll)
            tools = daftar tool dari SAP / mock

        Output:
            decision = tool + action + reasoning
        """

        if not tools:
            return {
                "tool": None,
                "action": "idle",
                "reason": "No tools available"
            }

        # simple selection logic (bisa diganti LLM nanti)
        selected_tool = random.choice(tools)

        decision = {
            "tool": selected_tool,
            "action": "scan_and_analyze",
            "reason": f"Selected {selected_tool} based on basic heuristic",
            "target_id": target.get("id"),
            "target_url": target.get("url")
        }

        return decision