# app/orchestrator/verifier.py

def verify_result(result: dict):
    """
    Verifikasi sederhana:
    - apakah ada execution
    - hitung autonomy score
    """

    executions = result.get("executions", [])

    score = 0.0

    if executions:
        score += 0.4

    types = [e["type"] for e in executions]

    if "ace" in types:
        score += 0.2

    if "rpc" in types:
        score += 0.2

    if "sentinel" in types:
        score += 0.2

    return {
        "verified": True,
        "autonomy_score": round(score, 2),
        "execution_count": len(executions),
        "result": result
    }