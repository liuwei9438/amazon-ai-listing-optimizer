from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .keyword_library import keywords_for
from .language_profiles import get_language_profile
from .product_analyzer import analyze_product
from .retry_engine import run_with_retries
from .short_title import fallback_short_title
from .validator import normalize_output, validate_listing


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 返回内容不是有效 JSON")
    return json.loads(text[start:end + 1])


def _generate(client: OpenAI, source: dict[str, Any], analysis: dict[str, Any], language: str, reason: str) -> dict[str, Any]:
    profile = get_language_profile(language)
    local_keywords = keywords_for(str(analysis.get("product_type", "")), language)
    prompt = f"""
You are an Amazon listing SEO and compliance writer.
Target language: {profile['language']}.
Return JSON only with keys: title, short_title, bullet1, bullet2, bullet3, bullet4, bullet5, description.

VERIFIED PRODUCT UNDERSTANDING:
{json.dumps(analysis, ensure_ascii=False)}

LOCAL SEO VOCABULARY:
{json.dumps(local_keywords, ensure_ascii=False)}
Use these terms only when they accurately describe product_type. Never turn an optional keyword into a new product fact.

SOURCE DATA:
{json.dumps(source, ensure_ascii=False)}

HARD RULES:
1. This is always a non-original compatibility product.
2. Every third-party brand mention must use the exact phrase: {profile['compat']}.
3. Never claim Original, Genuine, Official, OEM, Authentic, authorization, rankings, promotions or unverifiable superiority.
4. Preserve facts exactly. Never invent material, scenario, function, benefit, quantity, model, size, color, voltage, power or package contents.
5. Rewrite from the verified product understanding; do not translate sentence by sentence.
6. Lead the title with the strongest local product noun. Do not begin with vague marketing wording.
7. Title must be natural, locally searchable and <= {profile['title_limit']} characters including spaces.
8. Short title must summarize only source-supported product/material/scenario/function/benefit and <= {profile['short_limit']} characters.
9. Produce exactly five factual bullets and a clean description.
10. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service noise.
11. If many models exist, keep 2-4 representative models in title and put the complete list in bullets/description.
12. Do not use a material, function, scenario or selling point unless it appears in VERIFIED PRODUCT UNDERSTANDING.
13. Previous QA issue to correct: {reason or 'none'}.
""".strip()
    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return _parse_json(response.output_text)


def optimize_listing(client: OpenAI, source: dict[str, Any], language: str, analysis: dict[str, Any] | None = None, attempts: int = 4) -> dict[str, Any]:
    profile = get_language_profile(language)
    analysis = analysis or analyze_product(client, source)
    local_keywords = keywords_for(str(analysis.get("product_type", "")), language)

    def operation(reason: str) -> tuple[dict[str, Any], bool, str, int]:
        raw = _generate(client, source, analysis, language, reason)
        data = normalize_output(raw, str(profile["compat"]), int(profile["title_limit"]), int(profile["short_limit"]))
        if not data.get("short_title"):
            data["short_title"] = fallback_short_title(analysis, profile, local_keywords)
        ok, qa_reason, score = validate_listing(data, str(source.get("title", "")), profile, analysis)
        return data, ok, qa_reason, score

    data, success, reason, score = run_with_retries(operation, attempts=attempts)
    return {
        "data": data,
        "success": success,
        "reason": reason,
        "seo_score": score,
        "analysis": analysis,
        "keywords": local_keywords,
        "analysis_summary": {
            "product_type": analysis.get("product_type", ""),
            "category": analysis.get("category", ""),
            "brands": analysis.get("third_party_brands", []),
            "models": analysis.get("compatible_models", []),
            "material": analysis.get("material", ""),
            "functions": analysis.get("functions", []),
            "scenarios": analysis.get("usage_scenarios", []),
        },
    }
