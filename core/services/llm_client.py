import json
import os

import requests


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def complete_json(self, prompt: str, temperature: float = 0.0, timeout: int = 60):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a strict evaluator that returns JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "stream": False,
        }

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]

        # sanitize JSON output
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            fixed = text.strip().strip("`").lstrip("json").strip()
            return json.loads(fixed)
