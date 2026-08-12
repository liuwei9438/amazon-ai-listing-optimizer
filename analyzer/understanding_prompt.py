from __future__ import annotations

import json

from dataclasses import asdict, is_dataclass

from typing import Any



SYSTEM_PROMPT = """
You are the product understanding layer of an Amazon listing system.

Your task is to analyze the product source information and return ONLY structured product data matching the provided JSON schema.

Rules:

- Do not write titles, bullets, descriptions, or marketing copy.
- Preserve source facts exactly.
- Never invent missing information.
- Use empty strings or empty arrays when information is unavailable.
- Separate product identity, features, usage scenarios, specifications, and identifiers.
- Treat third-party brands as compatibility references unless ownership is proven.
- Never accept claims such as original, genuine, official, OEM, authentic as verified facts.

Return only JSON matching the schema.
""".strip()



def _record_dict(
    record: Any,
) -> dict[str, Any]:


    if is_dataclass(record):

        return asdict(record)


    if isinstance(
        record,
        dict,
    ):

        return dict(record)


    if hasattr(
        record,
        "__dict__",
    ):

        return dict(
            vars(record)
        )


    return {
        "value":
            str(record)
    }




def build_user_prompt(
    record: Any,
    fact_lock: dict[str, Any],
    profile_template: dict[str, Any],
) -> str:


    source = _record_dict(
        record
    )
    return f"""
Analyze the SOURCE as one product and fill the complete Product Profile.


IMPORTANT RULES:


## 1. Fact Protection

Only use information directly supported by SOURCE.

Do not invent:

- quantity
- material
- color
- dimensions
- voltage
- power
- package contents
- compatible models
- part numbers
- product functions
- usage scenarios


If information is missing:

Use:

- empty string
- empty list



## 2. Product Identity Classification


Separate information into:


product_identity.name:

The core product name only.

Do not include:

- usage scenarios
- target users
- materials
- marketing words
- application descriptions


context:

Include:

- device context
- application object
- environment
- target user


design_features:

Only physical design characteristics.


functional_features:

Only confirmed product functions.


usage_scenarios:

Only supported usage situations.



## 3. Identifier Classification


Analyze numbers and codes by product meaning.


Classify into:


model_number:

Product model identifiers.


part_number:

Replacement or manufacturer part identifiers.


series_number:

Product series identifiers.


unknown_code:

Codes that cannot be confirmed.


Do not classify specifications as models.


Do not put:

- voltage
- power
- dimensions
- weight

into identifiers.



## 4. Specification Extraction


Extract measurable facts separately.


Include:


dimensions:

Size information.


weight:

Weight information.


voltage:

Voltage information.


power:

Power rating.


capacity:

Capacity information.



## 5. Brand Handling


For brand information:


If the product is compatible with a third-party brand:

relationship:

unbranded_compatible


Use:

Compatible with + brand


Do not treat:

- original
- genuine
- official
- OEM
- authentic

as verified facts.



## 6. Compatibility


Only keep compatibility information directly supported by SOURCE.


Do not invent:

- models
- brands
- replacements



## 7. Feature Classification


Classify features into:


materials:

Confirmed materials only.


design_features:

Physical structure only.


functional_features:

Confirmed functions only.


specifications:

Measured values or technical parameters.


usage_scenarios:

Supported usage only.



Do not convert assumptions into features.



## 8. Search Strategy


Generate search strategy only from verified information.


title_identifiers:

Only high-value identifiers suitable for title.


bullet_identifiers:

Additional compatibility identifiers.


backend_identifiers:

Remaining verified identifiers.


Do not invent keywords.



## 9. Compliance


Identify risky claims:


- original
- genuine
- official
- OEM
- authentic
- authorized
- best seller
- #1
- premium quality


Return compliance information.



## 10. Output


Return every field required by PROFILE TEMPLATE.


The output must match the JSON schema exactly.



SOURCE:

{json.dumps(
    source,
    ensure_ascii=False,
    default=str
)}


VERIFIED FACT LOCK:

{json.dumps(
    fact_lock,
    ensure_ascii=False
)}


PROFILE TEMPLATE:

{json.dumps(
    profile_template,
    ensure_ascii=False
)}

""".strip()
