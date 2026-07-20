
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from openai import OpenAI


EMPTY_FACTS: dict[str, Any] = {
    "product_type": "",
    "core_keyword": "",
    "secondary_keywords": [],
    "third_party_brands": [],
    "compatible_models": [],
    "material": "",
    "quantity": "",
    "dimensions": "",
    "color": "",
    "functions": [],
    "structural_features": [],
    "usage_scenarios": [],
    "package_contents": [],
    "verified_selling_points": [],
    "unknown_or_conflicting": [],
    "evidence": {},
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def source_fingerprint(source: dict[str, Any]) -> str:
    payload = json.dumps(source, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("产品分析结果不是有效 JSON")
    return json.loads(text[start:end + 1])


def _dedupe(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = [values] if values else []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean(value).strip(" ,;|")
        if text and text.casefold() not in seen:
            seen.add(text.casefold())
            result.append(text)
    return result


def normalize_facts(data: dict[str, Any]) -> dict[str, Any]:
    result = dict(EMPTY_FACTS)
    result.update(data or {})

    for field in [
        "secondary_keywords", "third_party_brands", "compatible_models",
        "functions", "structural_features", "usage_scenarios",
        "package_contents", "verified_selling_points",
        "unknown_or_conflicting",
    ]:
        result[field] = _dedupe(result.get(field, []))

    for field in [
        "product_type", "core_keyword", "material", "quantity",
        "dimensions", "color",
    ]:
        result[field] = clean(result.get(field, ""))

    if not isinstance(result.get("evidence"), dict):
        result["evidence"] = {}

    return result


def analyze_product(client: OpenAI, source: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
You are the product-fact analyst for an Amazon listing optimization system.

Do NOT write an Amazon title, bullets, highlights, or description.
First understand the item being sold from all provided source fields together.

Return JSON only with these keys:
product_type, core_keyword, secondary_keywords, third_party_brands,
compatible_models, material, quantity, dimensions, color, functions,
structural_features, usage_scenarios, package_contents,
verified_selling_points, unknown_or_conflicting, evidence.

STRICT FACT PROTECTION:
1. Use the title, all bullet points, description, and every supplied source field together.
2. Identify the actual item being sold, not only the machine/device/vehicle it fits.
3. Never guess material, quantity, size, color, models, function, use scenario,
   package contents, performance, durability, installation difficulty, or benefits.
4. Every normalized function, structure, scenario, or selling point must have an exact
   source quotation in evidence.
5. Brand names found in the source are third-party compatibility brands unless the
   source explicitly proves they are the seller's own brand.
6. Preserve model and part numbers exactly.
7. Remove seller/store/manufacturer/ASIN/rank/shipping/customer-service noise.
8. Put uncertain or contradictory information into unknown_or_conflicting.
9. Empty information must remain an empty string, array, or object.
10. Do not add generic claims such as corrosion resistance, stronger performance,
    professional quality, easy installation, ideal fit, or enhanced durability.

SOURCE DATA:
{json.dumps(source, ensure_ascii=False, default=str)}
""".strip()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return normalize_facts(_parse_json(response.output_text))
