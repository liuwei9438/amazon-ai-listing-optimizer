from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .api_client import create_response_with_backoff


INCOMPLETE_ENDINGS = {
    "English": {"for", "with", "and", "to", "of", "the", "a", "an"},
    "Spanish": {"para", "con", "de", "del", "y", "la", "el"},
    "Italian": {"per", "con", "di", "del", "e", "la", "il"},
    "Dutch": {"voor", "met", "van", "en", "de", "het"},
    "German": {"für", "mit", "von", "und", "der", "die", "das"},
    "French": {"pour", "avec", "de", "du", "et", "la", "le"},
    "Portuguese": {"para", "com", "de", "do", "e", "a", "o"},
    "Swedish": {"för", "med", "av", "och", "en", "ett"},
}


def clean(value: Any) -> str:
    value = str(value or "")
    value = value.replace("，", ",").replace("；", ";")
    return re.sub(r"\s+", " ", value).strip(" ,;-–—")


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean(value).strip('"').strip("'")
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _parse_candidates(text: str) -> list[str]:
    text = str(text or "").strip()
    result: list[str] = []

    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            values = data.get("highlights", [])
            if isinstance(values, list):
                result.extend(str(value) for value in values)
        except Exception:
            pass

    if not result:
        for line in text.splitlines():
            line = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", line).strip()
            line = line.strip('"').strip("'")
            if line and not line.startswith(("```", "{", "}", "[")):
                result.append(line)

    return _dedupe(result)


def _ends_incomplete(value: str, language_name: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", value.casefold())
    return bool(words and words[-1] in INCOMPLETE_ENDINGS.get(language_name, set()))


def _compact_highlights(
    value: str,
    *,
    highlights_limit: int,
    language_name: str,
) -> str:
    value = clean(value)
    if len(value) <= highlights_limit and not _ends_incomplete(value, language_name):
        return value

    # Prefer keeping complete comma-separated highlight phrases.
    parts = [clean(x) for x in re.split(r"\s*[,;|]\s*", value) if clean(x)]
    kept: list[str] = []
    for part in parts:
        candidate = ", ".join(kept + [part])
        if len(candidate) <= highlights_limit:
            kept.append(part)
        else:
            break

    if kept:
        value = ", ".join(kept)
        if not _ends_incomplete(value, language_name):
            return value

    # Final word-boundary shortening.
    words = clean(parts[0] if parts else value).split()
    while len(words) > 2 and len(" ".join(words)) > highlights_limit:
        words.pop()
    value = clean(" ".join(words))

    while value and _ends_incomplete(value, language_name):
        words = value.split()
        if len(words) <= 2:
            break
        words.pop()
        value = clean(" ".join(words))

    return value if len(value) <= highlights_limit else ""


def _fact_fallback(
    facts: dict[str, Any],
    *,
    highlights_limit: int,
    language_name: str,
) -> str:
    values: list[str] = []

    for scalar in ["quantity", "material", "dimensions"]:
        value = clean(facts.get(scalar))
        if value:
            values.append(value)

    for field in [
        "functions", "structural_features", "usage_scenarios",
        "verified_selling_points", "package_contents",
    ]:
        items = facts.get(field, [])
        if not isinstance(items, list):
            items = [items] if items else []
        values.extend(clean(x) for x in items if clean(x))

    values = _dedupe(values)
    result: list[str] = []
    for value in values:
        candidate = ", ".join(result + [value])
        if len(candidate) <= highlights_limit:
            result.append(value)
        if len(result) >= 5:
            break

    fallback = ", ".join(result)
    return _compact_highlights(
        fallback,
        highlights_limit=highlights_limit,
        language_name=language_name,
    )


def _score(value: str, highlights_limit: int, language_name: str) -> int:
    if not value or len(value) > highlights_limit:
        return -10000
    if _ends_incomplete(value, language_name):
        return -10000
    item_count = len([x for x in value.split(",") if clean(x)])
    score = 100 + min(20, item_count * 4)
    score += min(10, len(value) // 12)
    return score


def generate_highlights(
    client: OpenAI,
    facts: dict[str, Any],
    language_name: str,
    highlights_limit: int,
    retry_reason: str = "",
) -> str:
    prompt = f"""
You write Amazon Item Highlights directly in {language_name}.
Return JSON only:
{{"highlights": ["candidate 1", "candidate 2", "candidate 3",
"candidate 4", "candidate 5"]}}

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

RULES:
1. Produce five materially different Item Highlights candidates.
2. Target 70-{highlights_limit} characters. Every candidate must be at most
   {highlights_limit} characters including spaces and punctuation.
3. This is Item Highlights, not a shortened main title.
4. Combine 2-5 concise comma-separated verified highlights.
5. Prioritize quantity/specification, core function, material, structure,
   use scenario, package contents and verified selling points.
6. Do not include brands, compatible models or compatibility phrases.
7. Do not end with an incomplete phrase.
8. Never invent facts or generic benefits.
9. Write directly in {language_name}; do not translate an English draft word by word.
10. Retry issue to avoid: {retry_reason or "none"}
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=550,
    )

    candidates: list[str] = []
    for raw in _parse_candidates(text):
        candidates.append(raw)
        compact = _compact_highlights(
            raw,
            highlights_limit=highlights_limit,
            language_name=language_name,
        )
        if compact:
            candidates.append(compact)

    fallback = _fact_fallback(
        facts,
        highlights_limit=highlights_limit,
        language_name=language_name,
    )
    if fallback:
        candidates.append(fallback)

    scored = [
        (_score(value, highlights_limit, language_name), value)
        for value in _dedupe(candidates)
    ]
    scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)

    if scored and scored[0][0] > -10000:
        return scored[0][1]

    raise ValueError(f"产品亮点未能压缩到{highlights_limit}字符以内")
