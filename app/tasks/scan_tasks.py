from app.services.scanner import scan_all_targets
from app.services.ai_engine import analyze_scan_results
from app.core.memory import store_result

async def run_scan_cycle():
    print("[TASK] Running scan cycle...")

    results = await scan_all_targets()

    analysis = analyze_scan_results(results)

    store_result({
        "scan": results,
        "analysis": analysis
    })

    print("[TASK] Cycle completed")