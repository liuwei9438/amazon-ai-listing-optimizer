from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("产品理解结果不是有效 JSON")
    return json.loads(text[start:end + 1])


def analyze_product(client: OpenAI, source: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
Analyze the following product data. Do not write listing copy yet.
Return JSON only with these keys:
product_type, category, third_party_brands, compatible_models, material,
usage_scenarios, functions, factual_selling_points, source_keywords,
quantity, color, dimensions, voltage, power, package_contents.

Rules:
- Extract facts only from the supplied source.
- Never guess missing material, model, quantity, scenario, function or benefit.
- All mentioned brands are third-party compatibility brands, never the seller's brand.
- Remove seller/store/manufacturer/ASIN/ranking/platform noise.
- Keep model numbers exactly as written.

SOURCE:
{json.dumps(source, ensure_ascii=False)}
""".strip()
    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    data = _parse_json(response.output_text)
    defaults = {
        "product_type": "", "category": "", "third_party_brands": [],
        "compatible_models": [], "material": "", "usage_scenarios": [],
        "functions": [], "factual_selling_points": [], "source_keywords": [],
        "quantity": "", "color": "", "dimensions": "", "voltage": "",
        "power": "", "package_contents": [],
    }
    defaults.update(data)
    return defaults
