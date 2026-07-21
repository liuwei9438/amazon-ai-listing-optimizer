
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .api_client import create_response_with_backoff


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def generate_highlights(
    client: OpenAI,
    facts: dict[str, Any],
    language_name: str,
    highlights_limit: int,
    retry_reason: str = "",
) -> str:
    prompt = f"""
You write Amazon Item Highlights directly in {language_name}.
Return only the highlights text. No JSON, labels, explanation or markdown.

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

RULES:
1. Maximum {highlights_limit} characters including spaces and punctuation.
2. This is Item Highlights, not a shortened main title.
3. Combine 2-6 concise comma-separated highlights, depending on how many facts exist.
4. Prioritize quantity/specification, core function, material, structure,
   use scenario and verified selling points.
5. Do not include brands, models or compatibility phrases.
6. Do not end with an incomplete phrase.
7. Never invent facts or generic benefits.
8. Write directly in {language_name}; do not translate an English draft word by word.
9. Retry issue to avoid: {retry_reason or "none"}
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=220,
    )
    value = clean(text.strip().strip('"').strip("'"))
    if not value:
        raise ValueError("产品亮点为空")
    if len(value) > highlights_limit:
        raise ValueError(f"产品亮点超过{highlights_limit}字符")
    return value
