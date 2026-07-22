from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


SYSTEM_PROMPT = """
You are the product-understanding layer of an Amazon listing system.
Return only data matching the supplied JSON schema.
Do not write a title, bullet points, description, advertising copy, or sales claims.
Preserve all source facts and use empty values when evidence is absent.
""".strip()


def _record_dict(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, dict):
        return dict(record)
    if hasattr(record, "__dict__"):
        return dict(vars(record))
    return {"value": str(record)}


def build_user_prompt(
    record: Any,
    fact_lock: dict[str, Any],
    profile_template: dict[str, Any],
) -> str:
    source = _record_dict(record)
    return f"""
Analyze the SOURCE as one product and fill the complete Product Profile.

NON-NEGOTIABLE RULES:
1. Never invent quantity, material, color, dimensions, voltage, power,
   package contents, compatible brands, models, part numbers, functions,
   scenarios or benefits.
2. Keep model numbers and part numbers exactly as written in SOURCE.
3. Unless SOURCE explicitly proves an owned seller brand, treat named brands
   as third-party compatibility references.
4. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service noise.
5. Flag risky terms such as original, genuine, official, OEM, authentic,
   authorized, best seller, #1, premium quality and unsupported superiority.
6. Use empty strings or empty arrays when a value is absent.
7. Copy SOURCE identity into source_identity. If row number is absent, use 0.
8. Return every field in PROFILE TEMPLATE.
9. The fact_lock field must exactly match VERIFIED FACT LOCK.
10. For brand_info:
    - explicit compatibility wording -> unbranded_compatible
    - no detected third-party brand -> generic
    - third-party brand without compatibility wording -> high_risk_brand_usage
    - never accept original/genuine/official/OEM claims as verified facts

SOURCE:
{json.dumps(source, ensure_ascii=False, default=str)}

VERIFIED FACT LOCK:
{json.dumps(fact_lock, ensure_ascii=False)}

PROFILE TEMPLATE:
{json.dumps(profile_template, ensure_ascii=False)}
""".strip()
