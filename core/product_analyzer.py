
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from openai import OpenAI

from .api_client import create_response_with_backoff


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


def _trim_source(source: dict[str, Any]) -> dict[str, Any]:
    """Limit prompt size while retaining the product facts needed for analysis."""
    title = clean(source.get("title", ""))[:1200]
    bullets = [clean(item)[:1500] for item in source.get("bullet_points", [])][:5]
    description = clean(source.get("description", ""))[:5000]

    allowed_specs: dict[str, str] = {}
    source_fields = source.get("source_fields", {})
    if isinstance(source_fields, dict):
        useful_names = [
            "材质", "材料", "material", "尺寸", "包装尺寸", "dimensions",
            "颜色", "color", "数量", "quantity", "package", "包装",
            "型号", "model", "兼容", "compatible", "电压", "功率",
            "产品类型", "category", "分类",
        ]
        for key, value in source_fields.items():
            key_text = clean(key)
            if any(name.casefold() in key_text.casefold() for name in useful_names):
                value_text = clean(value)
                if value_text:
                    allowed_specs[key_text] = value_text[:1000]

    return {
        "title": title,
        "bullet_points": bullets,
        "description": description,
        "color_or_variant": clean(source.get("color_or_variant", ""))[:500],
        "useful_source_fields": allowed_specs,
    }


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
    compact_source = _trim_source(source)
    prompt = f"""
You are the product-fact analyst for an Amazon listing system.
Do not write listing copy. Return JSON only.

Required keys:
product_type, core_keyword, secondary_keywords, third_party_brands,
compatible_models, material, quantity, dimensions, color, functions,
structural_features, usage_scenarios, package_contents,
verified_selling_points, unknown_or_conflicting, evidence.

RULES:
1. Read title, all bullets, description and useful source fields together.
2. Identify the exact item being sold, not only the machine or vehicle it fits.
3. Copy brands, models, quantity, material, size, color and package contents exactly.
4. Never guess a fact or generic benefit.
5. Functions, structures, scenarios and selling points require an exact supporting quote
   in evidence. Evidence format:
   {{"functions": {{"Remote Monitoring": "remote monitoring"}}}}
6. Treat source brands as third-party compatibility brands unless own-brand status is proven.
7. Put uncertain or conflicting information in unknown_or_conflicting.
8. Remove store, seller, ASIN, ranking, shipping and service noise.
9. Keep the output concise to reduce token usage.

SOURCE:
{json.dumps(compact_source, ensure_ascii=False)}
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=1000,
    )
    return normalize_facts(_parse_json(text))
