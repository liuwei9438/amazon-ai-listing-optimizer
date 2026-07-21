
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .api_client import create_response_with_backoff


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("五点和详情结果不是有效 JSON")
    return json.loads(text[start:end + 1])


def generate_body(
    client: OpenAI,
    facts: dict[str, Any],
    language_name: str,
    compatibility_phrase: str,
    retry_reason: str = "",
    previous_output: dict[str, Any] | None = None,
) -> dict[str, str]:
    prompt = f"""
You are a senior Amazon listing editor writing directly in {language_name}.
Return JSON only with keys:
bullet1, bullet2, bullet3, bullet4, bullet5, description.

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

PREVIOUS OUTPUT:
{json.dumps(previous_output or {}, ensure_ascii=False)}

RETRY REASON:
{retry_reason or "none"}

RULES:
1. Write directly for Amazon shoppers in {language_name}; do not translate an English draft.
2. Produce exactly five useful and non-repetitive bullets.
3. Use these responsibilities when facts exist:
   bullet1 core function/use;
   bullet2 compatibility/models;
   bullet3 material/structure/specification;
   bullet4 use scenario/operation;
   bullet5 quantity/package contents or another verified fact.
4. When one category is absent, use another verified fact. Never invent filler.
5. Description must be concise, factual and based only on VERIFIED PRODUCT FACTS.
6. Every third-party brand mention must be introduced with exactly:
   {compatibility_phrase}
7. Do not use Original, Genuine, Official, OEM, Authentic, Best Seller, #1,
   Premium Quality, promotion, guarantee or authorization language.
8. Do not invent durability, corrosion resistance, professional quality,
   easy installation, perfect fit, stronger performance or other generic benefits.
9. Preserve models, measurements and quantities exactly.
10. Remove seller, store, ASIN, rank, shipping and customer-service noise.
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=1400,
    )
    raw = _parse_json(text)
    return {
        key: clean(raw.get(key, ""))
        for key in [
            "bullet1", "bullet2", "bullet3",
            "bullet4", "bullet5", "description",
        ]
    }
