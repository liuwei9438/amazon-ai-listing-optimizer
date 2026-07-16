from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .keyword_library import keywords_for
from .language_profiles import get_language_profile
from .product_analyzer import analyze_product
from .short_title import fallback_short_title
from .validator import deterministic_repair, normalize_output, validate_listing


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 返回内容不是有效 JSON")
    return json.loads(text[start:end + 1])


def _generation_strategy(retry_round: int) -> str:
    if retry_round <= 0:
        return "Generate a complete high-quality listing from scratch."
    if retry_round == 1:
        return "Repair only the failed fields. Keep fields that already pass QA unchanged."
    if retry_round == 2:
        return "Use stricter, shorter wording. Prioritize factual product nouns and remove low-value wording."
    return "Produce the safest concise compliant version. Do not use promotional language."


def _generate(
    client: OpenAI,
    source: dict[str, Any],
    analysis: dict[str, Any],
    language: str,
    reason: str,
    retry_round: int,
    previous_output: dict[str, Any] | None,
) -> dict[str, Any]:
    profile = get_language_profile(language)
    local_keywords = keywords_for(str(analysis.get("product_type", "")), language)
    strategy = _generation_strategy(retry_round)
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

PREVIOUS OUTPUT:
{json.dumps(previous_output or {}, ensure_ascii=False)}

RETRY ROUND: {retry_round}
STRATEGY: {strategy}
PREVIOUS QA FAILURE: {reason or 'none'}

HARD RULES:
1. This is always a non-original compatibility product.
2. Every third-party brand mention must use the exact phrase: {profile['compat']}.
3. Never claim Original, Genuine, Official, OEM, Authentic, authorization, rankings, promotions or unverifiable superiority.
4. Preserve facts exactly. Never invent material, scenario, function, benefit, quantity, model, size, color, voltage, power or package contents.
5. Rewrite from the verified product understanding; do not translate sentence by sentence.
6. Lead the main title with the strongest local product noun.
7. Main title must be natural, locally searchable and <= {profile['title_limit']} characters including spaces.
8. short_title is Amazon Item Highlights, not a second main title. It must be <= {profile['short_limit']} characters.
9. Build short_title from verified quantity, material, use scenario, dimensions, functions, factual selling points and high-value search terms. Omit unsupported facts.
10. Produce exactly five factual bullets and a clean description.
11. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service noise.
12. If many models exist, keep 2-4 representative models in title and put the complete list in bullets/description.
13. If retrying, directly correct the stated QA failure instead of repeating the same wording.
14. EVERY human-language phrase must be written in {profile['language']}. Do not leave English sentences or English product wording in a non-English result, except brand names, model numbers, measurements and standard technical abbreviations.
15. The compatibility phrase alone is not enough localization. Translate/localize the product noun, functions, scenarios, bullets and description into {profile['language']}.
""".strip()
    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return _parse_json(response.output_text)


def _safe_fallback(
    source: dict[str, Any],
    analysis: dict[str, Any],
    profile: dict[str, Any],
    local_keywords: list[str],
    previous_output: dict[str, Any] | None,
) -> dict[str, str]:
    previous_output = previous_output or {}
    product_type = str(analysis.get("product_type", "") or "").strip()
    compat = str(profile["compat"])
    brands = [str(x).strip() for x in analysis.get("third_party_brands", []) or [] if str(x).strip()]
    models = [str(x).strip() for x in analysis.get("compatible_models", []) or [] if str(x).strip()]

    title_parts: list[str] = []
    if local_keywords:
        title_parts.append(local_keywords[0])
    elif product_type:
        title_parts.append(product_type)
    if brands:
        title_parts.append(f"{compat} {brands[0]}")
    if models:
        title_parts.extend(models[:3])
    title = " ".join(x for x in title_parts if x).strip() or str(source.get("title", "") or product_type)

    short_title = fallback_short_title(analysis, profile, local_keywords)
    facts: list[str] = []
    for field in ["functions", "usage_scenarios", "factual_selling_points", "package_contents"]:
        for item in analysis.get(field, []) or []:
            text = str(item or "").strip()
            if text and text.casefold() not in {x.casefold() for x in facts}:
                facts.append(text)
    for field in ["quantity", "material", "dimensions", "color", "voltage", "power"]:
        text = str(analysis.get(field, "") or "").strip()
        if text and text.casefold() not in {x.casefold() for x in facts}:
            facts.append(text)

    source_bullets = [str(x or "").strip() for x in source.get("bullet_points", []) or [] if str(x or "").strip()]
    bullet_pool = facts + source_bullets
    if not bullet_pool:
        bullet_pool = [product_type or "Product information"]
    bullets = [bullet_pool[i % len(bullet_pool)] for i in range(5)]
    desc = str(source.get("description", "") or "").strip() or ". ".join(facts[:6]) or product_type

    return {
        "title": title,
        "short_title": short_title,
        **{f"bullet{i+1}": bullets[i] for i in range(5)},
        "description": desc,
    }


def optimize_listing(
    client: OpenAI,
    source: dict[str, Any],
    language: str,
    analysis: dict[str, Any] | None = None,
    attempts: int = 2,
    retry_round: int = 0,
    previous_output: dict[str, Any] | None = None,
    previous_reason: str = "",
) -> dict[str, Any]:
    profile = get_language_profile(language)
    analysis = analysis or analyze_product(client, source)
    local_keywords = keywords_for(str(analysis.get("product_type", "")), language)

    # Fast local repair first. Many failures are length, wording, empty-field or forbidden-word issues.
    if previous_output:
        repaired = deterministic_repair(previous_output, profile, analysis)
        if not repaired.get("short_title"):
            repaired["short_title"] = fallback_short_title(analysis, profile, local_keywords)
        ok, reason, score = validate_listing(repaired, str(source.get("title", "")), profile, analysis)
        if ok:
            return {
                "data": repaired, "success": True, "reason": "", "seo_score": score,
                "analysis": analysis, "keywords": local_keywords, "repair_mode": "local",
            }
        previous_reason = reason or previous_reason

    data: dict[str, Any] = {}
    reason = previous_reason
    score = 0
    for _ in range(max(1, attempts)):
        raw = _generate(client, source, analysis, language, reason, retry_round, previous_output)
        data = deterministic_repair(raw, profile, analysis)
        if not data.get("short_title"):
            data["short_title"] = fallback_short_title(analysis, profile, local_keywords)
        ok, reason, score = validate_listing(data, str(source.get("title", "")), profile, analysis)
        if ok:
            return {
                "data": data, "success": True, "reason": "", "seo_score": score,
                "analysis": analysis, "keywords": local_keywords, "repair_mode": "ai",
            }
        previous_output = data

    # Deterministic fallback is safe only for English. For non-English, an English
    # source-grounded fallback would silently create wrong-language rows.
    if retry_round >= 2 and str(profile.get("language")) == "English":
        fallback = _safe_fallback(source, analysis, profile, local_keywords, previous_output)
        fallback = deterministic_repair(fallback, profile, analysis)
        ok, fallback_reason, fallback_score = validate_listing(
            fallback, str(source.get("title", "")), profile, analysis
        )
        if ok:
            return {
                "data": fallback, "success": True, "reason": "", "seo_score": fallback_score,
                "analysis": analysis, "keywords": local_keywords, "repair_mode": "fallback",
            }
        data, reason, score = fallback, fallback_reason, fallback_score

    return {
        "data": data,
        "success": False,
        "reason": reason or "未知质检失败",
        "seo_score": score,
        "analysis": analysis,
        "keywords": local_keywords,
        "repair_mode": "failed",
    }
