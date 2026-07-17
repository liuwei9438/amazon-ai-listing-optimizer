from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

ANALYSIS_FIELDS = {
    "product_type": "",
    "category": "",
    "third_party_brands": [],
    "compatible_models": [],
    "material": "",
    "usage_scenarios": [],
    "functions": [],
    "factual_selling_points": [],
    "source_keywords": [],
    "quantity": "",
    "color": "",
    "dimensions": "",
    "voltage": "",
    "power": "",
    "package_contents": [],
    "analysis_notes": [],
}

NOISE_KEYS = {
    "manufacturer", "asin", "item model number", "best sellers rank",
    "seller", "store", "date first available", "customer reviews",
}


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("产品理解结果不是有效 JSON")
    return json.loads(text[start:end + 1])


def _source_text(source: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in source.items():
        if str(key).strip().lower() in NOISE_KEYS:
            continue
        if isinstance(value, list):
            parts.extend(str(x) for x in value if str(x).strip())
        elif str(value or "").strip():
            parts.append(str(value))
    return "\n".join(parts)


def _dedupe_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = [values] if values else []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = re.sub(r"\s+", " ", str(value or "")).strip(" ,;|")
        if not text:
            continue
        key = text.casefold()
        if key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _extract_model_candidates(text: str) -> list[str]:
    candidates = re.findall(
        r"\b(?=[A-Z0-9-]{2,20}\b)(?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)*\b",
        text,
        flags=re.I,
    )
    blocked = {"1600", "2024", "2025", "2026", "100", "120", "220", "240"}
    units = re.compile(r"^\d+(?:\.\d+)?(?:G|KG|OZ|LB|MM|CM|M|V|W|MAH|PCS?|SET)$", re.I)
    safe: list[str] = []
    for value in candidates:
        upper = value.upper().strip("-")
        if upper in blocked or upper.isdigit() or units.fullmatch(upper):
            continue
        # A useful model/part number normally contains at least one letter and one digit.
        if not re.search(r"[A-Z]", upper) or not re.search(r"\d", upper):
            continue
        safe.append(value)
    return _dedupe_strings(safe)


def _supported_in_source(value: str, source_text: str) -> bool:
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return False
    return value.casefold() in source_text.casefold()


def _sanitize_analysis(data: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    source_text = _source_text(source)
    output = dict(ANALYSIS_FIELDS)
    output.update(data or {})

    for field in [
        "third_party_brands", "compatible_models", "usage_scenarios", "functions",
        "factual_selling_points", "source_keywords", "package_contents", "analysis_notes",
    ]:
        output[field] = _dedupe_strings(output.get(field, []))

    # Models must be copied exactly from source. Add locally detected models, then drop hallucinations.
    local_models = _extract_model_candidates(source_text)
    output["compatible_models"] = _dedupe_strings([*output["compatible_models"], *local_models])
    output["compatible_models"] = [x for x in output["compatible_models"] if _supported_in_source(x, source_text)]

    # Strict factual fields are blanked when the exact value is not supported by source text.
    for field in ["material", "quantity", "color", "dimensions", "voltage", "power"]:
        value = re.sub(r"\s+", " ", str(output.get(field, "") or "")).strip()
        output[field] = value if value and _supported_in_source(value, source_text) else ""

    # Product type/category can be normalized concepts, but must remain concise.
    output["product_type"] = re.sub(r"\s+", " ", str(output.get("product_type", "") or "")).strip()[:100]
    output["category"] = re.sub(r"\s+", " ", str(output.get("category", "") or "")).strip()[:100]

    # Brands must occur in source. This prevents invented compatibility brands.
    output["third_party_brands"] = [x for x in output["third_party_brands"] if _supported_in_source(x, source_text)]

    # Keep source-supported phrases; concepts that are paraphrases remain allowed but are marked for conservative use.
    for field in ["usage_scenarios", "functions", "factual_selling_points", "package_contents"]:
        safe: list[str] = []
        for item in output[field]:
            if _supported_in_source(item, source_text):
                safe.append(item)
        output[field] = safe

    # Source keywords can be normalized, but cap count to avoid noisy prompts.
    output["source_keywords"] = output["source_keywords"][:12]
    output["analysis_notes"] = output["analysis_notes"][:8]
    return output


def analyze_product(client: OpenAI, source: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
You are the product-understanding layer of an Amazon listing system.
Do NOT write listing copy. Return JSON only.

Required keys:
product_type, category, third_party_brands, compatible_models, material,
usage_scenarios, functions, factual_selling_points, source_keywords,
quantity, color, dimensions, voltage, power, package_contents, analysis_notes.

STRICT RULES:
1. Extract only facts supported by SOURCE. Never infer a material, quantity, model, color, size, voltage, power, package item, function, scenario or benefit.
2. Keep every model/part number exactly as written in SOURCE.
3. Every brand in SOURCE is a third-party compatibility brand, never the seller's own brand.
4. product_type must identify the actual item, not a vague category such as "part" or "accessory" when a more precise noun is available.
5. category is the appliance/product family the item belongs to.
6. source_keywords should contain concise, source-supported product nouns and buyer search phrases; do not add unsupported marketing language.
7. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service/platform noise.
8. Use empty strings or empty arrays when a fact is absent.

SOURCE:
{json.dumps(source, ensure_ascii=False)}
""".strip()
    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return _sanitize_analysis(_parse_json(response.output_text), source)
