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


11. Extract product identity using product_identity.

product_identity describes the actual product structure.

Do not put the complete source title into product_identity.name.

Separate product information into:

name:
The core product name only.
Remove usage scenarios, application objects, materials,
design descriptions and marketing words.

context:
Application object, target user, device or environment.

design_features:
Physical design characteristics.

functional_features:
Confirmed product functions.

usage_scenarios:
How or where the product is used.


FACT PROTECTION RULE:

The AI must separate confirmed facts from assumptions.

Only extract information that is directly supported by SOURCE.

Do not improve, enrich, complete, or guess product information
based on general product knowledge.

If a feature is not explicitly supported by SOURCE,
leave the field empty.


12. Classify product features into different categories.

Do not mix product identity, functions, usage scenarios,
materials and specifications.

Classify information as:

materials:
Confirmed product materials only.

design_features:
Physical design characteristics.

functional_features:
Confirmed functions or operating features.

usage_scenarios:
Where or how the product is used.

specifications:
Size, voltage, dimensions, model-related or measurable facts.


DESIGN FEATURE RULE:

Only extract design_features that are explicitly supported by SOURCE.

Do not infer design features from common product structures.

Do not add ergonomic, comfortable, anti-slip, durable,
or similar benefit descriptions unless SOURCE explicitly states them.


FUNCTION RULE:

Only include functions explicitly confirmed by SOURCE.

Do not convert design descriptions into functions.

Do not assume a product capability only because the product
is commonly used for that purpose.


CONTEXT AND USAGE RULE:

Only include context and usage_scenarios directly supported by SOURCE.

Do not expand the usage scope based on general knowledge.


Do not put usage scenarios into product_identity.name.

Do not put marketing claims into factual_selling_points.



Examples:

SOURCE:
Alicate para Orejas de Cerdo en Forma U Acero Inoxidable


Wrong:

product_identity.name:
Alicate para Orejas de Cerdo en Forma U Acero Inoxidable


Correct:

product_identity.name:
Alicate para Orejas

context:
Animal ear marking

design_features:
U Shape

functional_features:
Mark animal ears



SOURCE:
Vacuum Cleaner Roller Brush Remove Dirt


Wrong:

product_identity.name:
Vacuum Cleaner Roller Brush Remove Dirt


Correct:

product_identity.name:
Vacuum Cleaner Roller Brush

functional_features:
Helps remove dirt and debris



Do not invent unsupported products.

Use empty value only when product identity cannot be determined.


SOURCE:
{json.dumps(source, ensure_ascii=False, default=str)}


VERIFIED FACT LOCK:
{json.dumps(fact_lock, ensure_ascii=False)}


PROFILE TEMPLATE:
{json.dumps(profile_template, ensure_ascii=False)}

""".strip()
