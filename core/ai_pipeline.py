from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .keyword_library import keywords_for
from .language_profiles import get_language_profile
from .product_analyzer import analyze_product
from .short_title import fallback_short_title
from .validator import deterministic_repair, validate_listing


def _parse_json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 返回内容不是有效 JSON")
    return json.loads(text[start:end + 1])


def _generation_strategy(retry_round: int) -> str:
    if retry_round <= 0:
        return "Create a new Amazon listing from the verified product facts."
    if retry_round == 1:
        return "Rewrite only what failed QA while preserving all verified facts."
    if retry_round == 2:
        return "Use a shorter and more conservative Amazon structure."
    return "Return the safest complete compliant version using only verified facts."


def _verified_fact_count(analysis: dict[str, Any]) -> int:
    count = 0
    for field in ["quantity", "dimensions", "material", "color", "voltage", "power"]:
        if str(analysis.get(field, "") or "").strip():
            count += 1
    for field in [
        "functions", "structural_features", "usage_scenarios",
        "factual_selling_points", "package_contents",
    ]:
        count += len(analysis.get(field, []) or [])
    return count


def _highlight_count(text: str) -> int:
    parts = [part.strip() for part in re.split(r"[,;|•]+", str(text or "")) if part.strip()]
    return len(parts)


def _quality_gate(
    data: dict[str, Any],
    source: dict[str, Any],
    analysis: dict[str, Any],
    language: str,
) -> tuple[bool, str]:
    profile = get_language_profile(language)
    title = str(data.get("title", "") or "").strip()
    short_title = str(data.get("short_title", "") or "").strip()
    source_title = str(source.get("title", "") or "").strip()

    if len(title) > int(profile["title_limit"]):
        return False, f"标题超过{profile['title_limit']}字符，必须重新写成完整标题"

    if title.casefold() == source_title.casefold():
        return False, "标题与原标题完全相同，必须重新组织关键词"

    if str(profile["language"]) == "English" and source_title:
        source_words = set(re.findall(r"[a-z0-9]+", source_title.casefold()))
        title_words = set(re.findall(r"[a-z0-9]+", title.casefold()))
        if source_words and len(source_words & title_words) / max(1, len(source_words)) > 0.92:
            return False, "英文标题改写不足，不能只是轻微删减原标题"

    fact_count = _verified_fact_count(analysis)
    if fact_count >= 3 and _highlight_count(short_title) < 3:
        return False, "短标题未充分提取产品亮点，至少组合3项已验证信息"
    if fact_count >= 2 and _highlight_count(short_title) < 2:
        return False, "短标题不能只保留一个材质或产品词"

    product_name = str(
        analysis.get("core_product_name")
        or analysis.get("product_type")
        or analysis.get("main_keyword")
        or ""
    ).strip()
    if product_name and product_name.casefold() not in title.casefold():
        # This is a soft but important SEO requirement. The model may use a valid
        # localized synonym, so only reject when local keywords also do not appear.
        local_keywords = keywords_for(str(analysis.get("product_type", "")), language)
        if not any(keyword.casefold() in title.casefold() for keyword in local_keywords[:4]):
            return False, "标题缺少明确的核心产品词"

    return True, ""


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
You are a senior Amazon listing editor for the {profile['language']} marketplace.
Return JSON only with keys:
title, short_title, bullet1, bullet2, bullet3, bullet4, bullet5, description.

VERIFIED PRODUCT FACTS:
{json.dumps(analysis, ensure_ascii=False)}

SOURCE MATERIAL:
{json.dumps(source, ensure_ascii=False)}

LOCAL PRODUCT VOCABULARY:
{json.dumps(local_keywords, ensure_ascii=False)}

PREVIOUS OUTPUT:
{json.dumps(previous_output or {}, ensure_ascii=False)}

RETRY ROUND: {retry_round}
STRATEGY: {strategy}
QA FAILURE TO FIX: {reason or 'none'}

WORKFLOW:
A. First identify the precise item being sold and its main buyer search term from VERIFIED PRODUCT FACTS.
B. Decide which 2-4 facts deserve title space under the 75-character limit.
C. Create Item Highlights from the remaining high-value verified facts.
D. Write five non-repetitive bullets, each with a distinct purpose.
E. Write a concise factual description.

MAIN TITLE RULES:
1. Maximum {profile['title_limit']} characters including spaces and punctuation.
2. Write a complete, natural Amazon search title. Never truncate text mechanically.
3. Put the strongest local product noun near the beginning.
4. Use only the highest-value facts: product noun, essential specification/function, material when important, and compatibility.
5. Do not copy, lightly edit or translate the source title word by word.
6. English must also be newly rewritten.
7. If many models are provided, include only 2-4 representative models in the title.
8. Never end with an incomplete preposition, article or conjunction.

ITEM HIGHLIGHTS / short_title RULES:
9. short_title is Amazon Item Highlights, not a shorter main title.
10. Maximum {profile['short_limit']} characters.
11. Combine 3-6 concise, comma-separated, source-supported highlights when available.
12. Prioritize: quantity/specification, material, core functions, structure, use scenario and factual selling points.
13. Do not output only a material, only a product noun, or a copied title.
14. Omit unsupported facts instead of filling space.

BULLET RULES:
15. Produce exactly five useful bullets with distinct roles:
    bullet1 = core function/use;
    bullet2 = compatibility/models when present, otherwise second core function;
    bullet3 = verified material/structure/specification;
    bullet4 = verified use scenario or operation;
    bullet5 = package contents/quantity or another verified fact.
16. Do not repeat the title or repeat the same claim across bullets.

COMPLIANCE AND FACT PROTECTION:
17. This is a non-original compatibility product.
18. Every mention of a third-party brand must use the exact phrase: {profile['compat']}.
19. Never use Original, Genuine, Official, OEM, Authentic, Best Seller, #1, Premium Quality, promotions, guarantees or authorization claims.
20. Never invent or upgrade material, quantity, size, color, model, voltage, power, package contents, function, benefit or use scenario.
21. Never add generic claims such as corrosion resistance, stronger performance, professional grade, ideal fit, improved balance, easy installation or enhanced durability unless explicitly verified.
22. Remove seller/store/manufacturer/ASIN/ranking/shipping/customer-service noise.

LOCALIZATION:
23. Write every normal-language phrase directly for Amazon shoppers in {profile['language']}.
24. Do not generate English first and then translate sentence by sentence.
25. Brand names, model numbers, measurements and standard technical abbreviations may remain unchanged.
26. Use natural local word order and marketplace terminology.

FINAL SELF-CHECK BEFORE RETURNING JSON:
27. Count title characters and rewrite if over the limit.
28. Confirm title is complete and materially different from SOURCE title.
29. Confirm short_title contains multiple verified highlights when the facts exist.
30. Confirm every factual claim can be traced to VERIFIED PRODUCT FACTS.
31. Confirm every brand mention has the exact compatibility phrase.
""".strip()

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
    )
    return _parse_json(response.output_text)


def optimize_listing(
    client: OpenAI,
    source: dict[str, Any],
    language: str,
    analysis: dict[str, Any] | None = None,
    attempts: int = 3,
    retry_round: int = 0,
    previous_output: dict[str, Any] | None = None,
    previous_reason: str = "",
) -> dict[str, Any]:
    profile = get_language_profile(language)
    analysis = analysis or analyze_product(client, source)
    local_keywords = keywords_for(str(analysis.get("product_type", "")), language)

    if previous_output:
        repaired = deterministic_repair(previous_output, profile, analysis)
        if not repaired.get("short_title"):
            repaired["short_title"] = fallback_short_title(analysis, profile, local_keywords)

        qa_ok, qa_reason = _quality_gate(repaired, source, analysis, language)
        valid_ok, valid_reason, score = validate_listing(
            repaired,
            str(source.get("title", "")),
            profile,
            analysis,
        )
        if qa_ok and valid_ok:
            return {
                "data": repaired,
                "success": True,
                "reason": "",
                "seo_score": score,
                "analysis": analysis,
                "keywords": local_keywords,
                "repair_mode": "local",
            }
        previous_reason = qa_reason or valid_reason or previous_reason

    data: dict[str, Any] = {}
    reason = previous_reason
    score = 0

    for _ in range(max(1, attempts)):
        raw = _generate(
            client,
            source,
            analysis,
            language,
            reason,
            retry_round,
            previous_output,
        )
        data = deterministic_repair(raw, profile, analysis)
        if not data.get("short_title"):
            data["short_title"] = fallback_short_title(analysis, profile, local_keywords)

        qa_ok, qa_reason = _quality_gate(data, source, analysis, language)
        valid_ok, valid_reason, score = validate_listing(
            data,
            str(source.get("title", "")),
            profile,
            analysis,
        )

        if qa_ok and valid_ok:
            return {
                "data": data,
                "success": True,
                "reason": "",
                "seo_score": score,
                "analysis": analysis,
                "keywords": local_keywords,
                "repair_mode": "ai",
            }

        reason = qa_reason or valid_reason or "未知质检失败"
        previous_output = data

    return {
        "data": data,
        "success": False,
        "reason": reason or "未知质检失败",
        "seo_score": score,
        "analysis": analysis,
        "keywords": local_keywords,
        "repair_mode": "failed",
    }
