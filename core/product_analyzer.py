from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

ANALYSIS_FIELDS = {
    "product_type": "",
    "core_product_name": "",
    "category": "",
    "main_keyword": "",
    "secondary_keywords": [],
    "third_party_brands": [],
    "compatible_models": [],
    "material": "",
    "usage_scenarios": [],
    "functions": [],
    "structural_features": [],
    "factual_selling_points": [],
    "source_keywords": [],
    "quantity": "",
    "color": "",
    "dimensions": "",
    "voltage": "",
    "power": "",
    "package_contents": [],
    "evidence": {},
    "unknown_points": [],
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
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                if str(nested_key).strip().lower() not in NOISE_KEYS and str(nested_value or "").strip():
                    parts.append(f"{nested_key}: {nested_value}")
        elif isinstance(value, list):
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
        r"\b(?=[A-Z0-9-]{2,24}\b)(?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)*\b",
        text,
        flags=re.I,
    )
    blocked = {"1600", "2024", "2025", "2026", "100", "120", "220", "240"}
    units = re.compile(r"^\d+(?:\.\d+)?(?:G|KG|OZ|LB|MM|CM|M|V|W|MAH|PCS?|SET)$", re.I)
    result: list[str] = []
    for value in candidates:
        upper = value.upper().strip("-")
        if upper in blocked or upper.isdigit() or units.fullmatch(upper):
            continue
        if not re.search(r"[A-Z]", upper) or not re.search(r"\d", upper):
            continue
        result.append(value)
    return _dedupe_strings(result)


def _supported_exactly(value: str, source_text: str) -> bool:
    value = re.sub(r"\s+", " ", value).strip()
    return bool(value and value.casefold() in source_text.casefold())


def _evidence_supported(field: str, value: str, evidence: dict[str, Any], source_text: str) -> bool:
    field_evidence = evidence.get(field, {}) if isinstance(evidence, dict) else {}
    quote = ""
    if isinstance(field_evidence, dict):
        quote = str(field_evidence.get(value, "") or "")
    elif isinstance(field_evidence, list):
        for item in field_evidence:
            if isinstance(item, dict) and str(item.get("value", "")).casefold() == value.casefold():
                quote = str(item.get("quote", "") or "")
                break
    return _supported_exactly(quote, source_text)


def _sanitize_analysis(data: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    source_text = _source_text(source)
    output = dict(ANALYSIS_FIELDS)
    output.update(data or {})

    list_fields = [
        "secondary_keywords", "third_party_brands", "compatible_models",
        "usage_scenarios", "functions", "structural_features",
        "factual_selling_points", "source_keywords", "package_contents",
        "unknown_points", "analysis_notes",
    ]
    for field in list_fields:
        output[field] = _dedupe_strings(output.get(field, []))

    local_models = _extract_model_candidates(source_text)
    output["compatible_models"] = _dedupe_strings([*output["compatible_models"], *local_models])
    output["compatible_models"] = [
        item for item in output["compatible_models"]
        if _supported_exactly(item, source_text)
    ]

    for field in ["material", "quantity", "color", "dimensions", "voltage", "power"]:
        value = re.sub(r"\s+", " ", str(output.get(field, "") or "")).strip()
        output[field] = value if _supported_exactly(value, source_text) else ""

    for field in ["product_type", "core_product_name", "category", "main_keyword"]:
        output[field] = re.sub(r"\s+", " ", str(output.get(field, "") or "")).strip()[:120]

    output["third_party_brands"] = [
        item for item in output["third_party_brands"]
        if _supported_exactly(item, source_text)
    ]

    evidence = output.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    output["evidence"] = evidence

    # Normalized concepts are permitted only when the analyzer also provides an
    # exact supporting quote from the source.
    for field in [
        "usage_scenarios", "functions", "structural_features",
        "factual_selling_points", "package_contents",
    ]:
        output[field] = [
            item for item in output[field]
            if _supported_exactly(item, source_text)
            or _evidence_supported(field, item, evidence, source_text)
        ]

    output["secondary_keywords"] = output["secondary_keywords"][:10]
    output["source_keywords"] = output["source_keywords"][:12]
    output["unknown_points"] = output["unknown_points"][:10]
    output["analysis_notes"] = output["analysis_notes"][:8]
    return output


def analyze_product(client: OpenAI, source: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
You are the product-fact engine for an Amazon listing system.
Your job is to understand the product before any listing copy is written.
Return JSON only. Do not write a title, bullets or description.

Required keys:
product_type, core_product_name, category, main_keyword, secondary_keywords,
third_party_brands, compatible_models, material, usage_scenarios, functions,
structural_features, factual_selling_points, source_keywords, quantity, color,
dimensions, voltage, power, package_contents, evidence, unknown_points,
analysis_notes.

FACT-FIRST RULES:
1. Read the title, all five bullet points, description and every supplied source field together.
2. Identify the actual item being sold, not merely the appliance, vehicle or device it works with.
3. product_type/core_product_name/main_keyword must be precise buyer-facing product nouns.
4. Copy brands, models, quantities, dimensions, material, color, voltage, power and package contents exactly from SOURCE.
5. Never infer or improve a fact. Do not add durability, corrosion resistance, stronger performance, professional quality, easy installation or any benefit unless SOURCE explicitly supports it.
6. A normalized function, scenario, structural feature or factual selling point may be returned only when evidence contains an exact quote from SOURCE supporting it.
7. evidence must be a JSON object. For each normalized list field, map each returned concept to an exact source quote, for example:
   "evidence": {{"functions": {{"Wet Dry Use": "wet dry shaving"}}}}
8. Every source brand is a third-party compatibility brand, not the seller's own brand.
9. Keep every model and part number exactly as written.
10. Put uncertain or contradictory claims in unknown_points instead of treating them as facts.
11. source_keywords and secondary_keywords may normalize wording but cannot introduce a new product type, function, material or use.
12. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service/platform noise.
13. Use empty strings, arrays or objects when information is absent.

SOURCE:
{json.dumps(source, ensure_ascii=False)}
""".strip()
    response = client.responses.create(model="gpt-4.1", input=prompt)
    return _sanitize_analysis(_parse_json(response.output_text), source)
