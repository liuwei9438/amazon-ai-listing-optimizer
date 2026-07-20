
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI


FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "top rated", "hot sale",
    "promotion", "discount", "free shipping", "premium quality",
    "highest quality", "100% satisfaction", "guaranteed",
    "lifetime warranty",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Listing 结果不是有效 JSON")
    return json.loads(text[start:end + 1])


def build_listing_prompt(
    source: dict[str, Any],
    facts: dict[str, Any],
    language_name: str,
    language_label: str,
    compatibility_phrase: str,
    title_limit: int,
    highlights_limit: int,
    retry_reason: str = "",
    previous_output: dict[str, Any] | None = None,
) -> str:
    return f"""
You are a senior Amazon listing editor for the {language_name} marketplace.

Return JSON only with keys:
title, short_title, bullet1, bullet2, bullet3, bullet4, bullet5, description.

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

ORIGINAL SOURCE:
{json.dumps(source, ensure_ascii=False, default=str)}

PREVIOUS OUTPUT:
{json.dumps(previous_output or {}, ensure_ascii=False)}

RETRY REASON:
{retry_reason or "none"}

CORE WORKFLOW:
1. Understand VERIFIED PRODUCT FACTS before writing.
2. Independently write the listing directly in {language_name}.
3. Do not translate an English draft sentence by sentence.
4. Use ORIGINAL SOURCE only to preserve facts, not to copy its wording.

AMAZON MAIN TITLE:
5. Maximum {title_limit} characters including spaces and punctuation.
6. Rewrite as a complete, natural Amazon search title; never mechanically truncate.
7. Put the strongest local product noun and core buyer keyword near the beginning.
8. Use only the highest-value facts: precise product noun, critical function/specification,
   material when important, and compatibility/model information.
9. If more than four models exist, use only 2-4 representative models in the title.
10. English must also be newly reorganized; do not simply return the source title.
11. Never finish with an incomplete preposition, conjunction, or article.

PRODUCT HIGHLIGHTS / short_title:
12. short_title is Amazon Item Highlights, not a shorter copy of the title.
13. Maximum {highlights_limit} characters.
14. When the source supports enough facts, combine 3-6 concise highlights separated by commas.
15. Prioritize quantity/specification, material, core function, structure, use scenario,
    and factual selling points.
16. Do not output only a material, only the product noun, or a copied title.
17. If only one or two reliable highlights exist, use only those; never invent filler.

FIVE BULLETS:
18. Write exactly five useful, non-repetitive bullets.
19. Suggested responsibilities:
    bullet1 = core function/use;
    bullet2 = compatibility and models when present;
    bullet3 = verified material/structure/specification;
    bullet4 = verified use scenario or operation;
    bullet5 = package contents/quantity or another verified fact.
20. If one category is absent, use another verified fact. Never invent a fact to fill a bullet.

DESCRIPTION:
21. Write a concise factual product description using verified product information.
22. Remove store, seller, manufacturer, ASIN, rank, shipping, customer-service, and platform noise.

COMPLIANCE:
23. This is a non-original compatibility product.
24. Every occurrence of a third-party brand must be introduced with the exact phrase:
    {compatibility_phrase}
25. Never use: {", ".join(FORBIDDEN_TERMS)}.
26. Never imply authorization, official status, original manufacture, or guaranteed performance.

FACT PROTECTION:
27. Never change or invent quantity, color, dimensions, material, voltage, power,
    models, part numbers, package contents, function, usage, or benefits.
28. Do not add corrosion resistance, stronger performance, improved balance,
    professional grade, easy installation, perfect fit, or enhanced durability
    unless explicitly supported by VERIFIED PRODUCT FACTS.

LOCALIZATION:
29. Write all normal-language content directly in {language_name}.
30. Brand names, model numbers, measurements, and standard abbreviations may remain unchanged.
31. Use natural Amazon search wording for {language_label}, not literal translation syntax.

FINAL SELF-CHECK:
32. Count title characters and rewrite until it is <= {title_limit}.
33. Confirm the title is complete and meaningfully reorganized.
34. Confirm short_title contains real product highlights rather than a shortened title.
35. Confirm every factual statement comes from VERIFIED PRODUCT FACTS.
36. Confirm every brand mention uses exactly: {compatibility_phrase}
""".strip()


def generate_listing(
    client: OpenAI,
    source: dict[str, Any],
    facts: dict[str, Any],
    language_name: str,
    language_label: str,
    compatibility_phrase: str,
    title_limit: int,
    highlights_limit: int,
    retry_reason: str = "",
    previous_output: dict[str, Any] | None = None,
) -> dict[str, str]:
    prompt = build_listing_prompt(
        source=source,
        facts=facts,
        language_name=language_name,
        language_label=language_label,
        compatibility_phrase=compatibility_phrase,
        title_limit=title_limit,
        highlights_limit=highlights_limit,
        retry_reason=retry_reason,
        previous_output=previous_output,
    )
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
    )
    raw = _parse_json(response.output_text)
    return {
        key: clean(raw.get(key, ""))
        for key in [
            "title", "short_title", "bullet1", "bullet2", "bullet3",
            "bullet4", "bullet5", "description",
        ]
    }
