# app/core/recovery.py

class RecoveryEngine:
    """
    Handles retry logic if execution fails
    """

    def should_retry(self, result):
        return not result.get("success", True)

    def retry(self, fn, *args, max_retry=2):
        attempt = 0
        last_result = None

        while attempt < max_retry:
            attempt += 1
            last_result = fn(*args)

            if last_result.get("success", True):
                return last_result

        return {
            "success": False,
            "retries": max_retry,
            "last_result": last_result
        }