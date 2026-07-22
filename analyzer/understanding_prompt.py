from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are an e-commerce product information analyst.
Analyze the supplied source content and return a factual ProductProfile JSON object.
Do not write or optimize a listing. Do not invent missing facts.
Unknown information must be an empty string or empty list.
A mentioned compatibility brand is not automatically the product's own brand.
Use relationship=compatible_accessory when the item is described as for/compatible with another brand or model.
Use original only when reliable source fields explicitly prove it.
Never add compatible models, quantities, materials, colors, dimensions, weights, package contents, certifications, or performance claims.
Marketing words such as best, premium, original, genuine, official and #1 are not product features.
Return JSON only and preserve the exact top-level schema."""

def build_user_prompt(record: Any, fact_lock: dict[str, Any], schema_template: dict[str, Any]) -> str:
    source = {
        "sku": getattr(record, "sku", ""),
        "parent_sku": getattr(record, "parent_sku", ""),
        "source_row_index": getattr(record, "row_number", None),
        "title": getattr(record, "title", ""),
        "bullets": list(getattr(record, "bullets", ())),
        "description": getattr(record, "description", ""),
        "language": getattr(record, "language", ""),
        "fact_lock_from_source": fact_lock,
    }
    return "SOURCE DATA:\n" + json.dumps(source, ensure_ascii=False, indent=2) + "\n\nREQUIRED JSON TEMPLATE:\n" + json.dumps(schema_template, ensure_ascii=False, indent=2)
