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


## 2. Product Identity Classification


Separate product identity information into different levels.


product_identity.name:

The core product name only.

This is the direct name of the product itself.

Do not include:

- usage scenarios
- target users
- materials
- marketing words
- compatibility claims
- application descriptions



buyer_search_identity:

Generate the product identity that best matches how customers search for this product on Amazon.

This field should combine:

- the core product type
- necessary device/application context

The purpose is to answer:

"What is this product for?"


Important:

Do not make it a category label.

Do not use broad seller categories.

Do not use:

- parts
- accessories
- replacement parts


Only include context that helps customers identify the product.


Examples of logic:

A product name alone may describe the component,
but buyer_search_identity should describe the searchable product identity.



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


Analyze numbers, codes, and alphanumeric values according to their actual product role.


Do not classify values only because they contain numbers, letters, or special characters.


Classify into:


model_number:

A value that identifies a specific product model, device model, or compatible machine model.

A model_number should help users distinguish one product identity from another.


part_number:

A manufacturer-defined or replacement part identifier.


series_number:

A product family or series identifier.


unknown_code:

A code whose meaning cannot be safely determined.

Important quantity classification rule:

Do not classify package quantity as identifiers.

Examples:

- 2PCS
- 4PCS
- 6PCS
- 12 pieces
- 3 sets

These values represent package quantity and must be classified as quantity information.

They should not enter:

- model_numbers
- part_numbers
- series_numbers
- unknown_codes

Only classify values as identifiers when they identify a specific product model, part number, or product code.

Decision process:


First determine whether the value identifies a specific product identity.


If the value only describes:

- product capability
- technical performance
- feature level
- configuration count
- protection level
- operating parameter
- measurable specification

do not classify it as model_number.


Classify those values as specification or unknown_code according to their meaning.


Do not put:

- voltage
- power
- dimensions
- weight
- technical specifications

into identifiers.


Only verified product identity information can enter:

- model_numbers
- part_numbers
- series_numbers



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

## Title Information Selection


The Amazon title has limited space.

Select the most valuable information that should appear in the title.


priority_attributes:

Select important attributes that help customers distinguish or choose the product.

Prioritize information that is difficult to recover after removing it from the title.

Examples:

- package quantity
- special configuration
- important design characteristics
- version differences


important_specifications:

Select technical specifications that customers commonly search for.

Examples:

- power
- capacity
- size
- important model-related specifications


important_quantity:

Always keep package quantity when quantity is clearly provided in SOURCE.

Quantity is especially important for:

- replacement parts
- accessories
- multi-piece packages
- consumable products

Examples:

- 2PCS Filter
- 6PCS Tuning Pegs
- 4PCS Replacement Blades


important_context:

Keep important product context required for customer understanding.

Examples:

- device type
- application object
- special usage context


important_compatibility:

Keep important compatibility information supported by SOURCE.

Examples:

- compatible brands
- compatible device families
- important compatible models


Do not select:

- generic seller categories
- marketing words
- unsupported claims
- low-value information that does not help search relevance or purchase decision


The goal is:

Choose the highest-value facts for a limited Amazon title length.

## 8. Search Strategy

Generate search strategy only from verified information.

Primary search identity should be derived from buyer_search_identity when available.

title_identifiers:

Only high-value identifiers suitable for title.
Title identifiers must come only from verified model_number, part_number, or series_number.

Do not use:
- specifications
- features
- performance values
- marketing descriptions

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
