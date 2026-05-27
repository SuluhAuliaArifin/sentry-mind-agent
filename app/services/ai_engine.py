def analyze_scan_results(results):
    """
    Simulasi AI reasoning layer
    (bisa diganti OpenAI / LLM nanti)
    """

    risk_score = 0

    for r in results:
        if r.get("status") == "vulnerable":
            risk_score += 1

    if risk_score > 5:
        return {
            "risk": "HIGH",
            "action": "immediate_recheck"
        }

    return {
        "risk": "LOW",
        "action": "normal"
    }