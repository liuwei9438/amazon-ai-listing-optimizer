from __future__ import annotations

import json
from typing import Any

import requests

class AIClientError(RuntimeError):
    pass

class OpenAIResponsesClient:
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini", timeout: int = 120):
        if not api_key or not api_key.strip():
            raise AIClientError("缺少 OpenAI API Key")
        self.api_key = api_key.strip()
        self.model = model.strip() or "gpt-4.1-mini"
        self.timeout = timeout

    def create_json(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            "temperature": 0.1,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "product_profile",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload, timeout=self.timeout,
        )
        if response.status_code >= 400:
            try: detail = response.json().get("error", {}).get("message", response.text)
            except Exception: detail = response.text
            raise AIClientError(f"OpenAI 请求失败（{response.status_code}）：{detail}")
        data = response.json()
        text = data.get("output_text", "")
        if not text:
            parts = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in ("output_text", "text") and content.get("text"):
                        parts.append(content["text"])
            text = "".join(parts)
        if not text:
            raise AIClientError("OpenAI 未返回可解析的商品画像")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIClientError(f"OpenAI 返回的 JSON 无法解析：{exc}") from exc
