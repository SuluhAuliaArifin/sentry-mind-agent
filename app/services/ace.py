# app/services/ace.py

import os
import requests

class AceDataClient:
    """
    Enforce multi-API usage:
    - LLM
    - Embedding
    - Classification / Risk scoring
    """

    def __init__(self):
        self.base_url = os.getenv("ACE_BASE_URL", "https://platform.acedata.cloud")
        self.api_key = os.getenv("ACE_API_KEY")

    def _call(self, endpoint: str, payload: dict):
        url = f"{self.base_url}{endpoint}"

        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=20
        )

        return response.json()

    # 1. LLM reasoning
    def llm(self, prompt: str):
        return self._call("/llm", {
            "prompt": prompt
        })

    # 2. Embedding
    def embedding(self, text: str):
        return self._call("/embedding", {
            "input": text
        })

    # 3. Classification / risk score
    def classify(self, text: str):
        return self._call("/classification", {
            "input": text
        })

    # 🔥 ENFORCER: wajib 3 API dipakai
    def enforce_multi_api(self, text: str):
        llm_result = self.llm(text)
        embed_result = self.embedding(text)
        class_result = self.classify(text)

        return {
            "llm": llm_result,
            "embedding": embed_result,
            "classification": class_result,
            "compliance": "3/3 APIs used"
        }