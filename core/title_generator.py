from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .api_client import create_response_with_backoff


FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "premium quality", "guaranteed",
]

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
    value = value.replace("，", ",").replace("；", ";").replace("：", ":")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*[/|]\s*", "/", value)
    return value.strip(" ,;-–—")


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
    """Accept strict JSON first, then recover from numbered/plain-line output."""
    text = str(text or "").strip()
    candidates: list[str] = []

    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            values = data.get("titles", [])
            if isinstance(values, list):
                candidates.extend(str(value) for value in values)
        except Exception:
            pass

    if not candidates:
        for line in text.splitlines():
            line = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", line).strip()
            line = line.strip('"').strip("'")
            if line and not line.startswith(("```", "{", "}", "[")):
                candidates.append(line)

    return _dedupe(candidates)


def _ends_incomplete(title: str, language_name: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", title.casefold())
    return bool(words and words[-1] in INCOMPLETE_ENDINGS.get(language_name, set()))


def _remove_forbidden(title: str) -> str:
    value = clean(title)
    for term in FORBIDDEN_TERMS:
        value = re.sub(re.escape(term), "", value, flags=re.I)
    return clean(value)


def _compact_candidate(
    title: str,
    *,
    title_limit: int,
    language_name: str,
) -> str:
    """Conservative local compression; removes wording, never adds facts."""
    value = _remove_forbidden(title)
    value = re.sub(r"\s*\([^)]{1,45}\)\s*", " ", value)
    value = re.sub(r"\b(?:Series|Serie|Série|Reihe)\b", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"([,;/])(?:\s*\1)+", r"\1", value)
    value = clean(value)

    if len(value) <= title_limit and not _ends_incomplete(value, language_name):
        return value

    # Remove low-priority trailing comma/semicolon segments first.
    segments = [clean(x) for x in re.split(r"\s*[,;]\s*", value) if clean(x)]
    while len(segments) > 1:
        candidate = ", ".join(segments)
        if len(candidate) <= title_limit and not _ends_incomplete(candidate, language_name):
            return candidate
        segments.pop()
    value = segments[0] if segments else value

    # Reduce slash-separated model lists from the right.
    while "/" in value and len(value) > title_limit:
        parts = value.split("/")
        if len(parts) <= 1:
            break
        parts.pop()
        value = clean("/".join(parts))

    if len(value) <= title_limit and not _ends_incomplete(value, language_name):
        return value

    # Final word-boundary reduction. Do not cut through a word.
    words = value.split()
    while len(words) > 2 and len(" ".join(words)) > title_limit:
        words.pop()
    value = clean(" ".join(words))

    while value and _ends_incomplete(value, language_name):
        words = value.split()
        if len(words) <= 2:
            break
        words.pop()
        value = clean(" ".join(words))

    return value if len(value) <= title_limit else ""


def _fact_values(facts: dict[str, Any], key: str) -> list[str]:
    value = facts.get(key, [])
    if not isinstance(value, list):
        value = [value] if value else []
    return _dedupe([str(x) for x in value])


def _build_fact_fallback(
    facts: dict[str, Any],
    *,
    compatibility_phrase: str,
    title_limit: int,
    language_name: str,
) -> str:
    """Build a safe title only from analyzer facts when all AI candidates are long."""
    core = clean(facts.get("core_keyword") or facts.get("product_type"))
    if not core:
        return ""

    brands = _fact_values(facts, "third_party_brands")
    models = _fact_values(facts, "compatible_models")
    quantity = clean(facts.get("quantity"))
    material = clean(facts.get("material"))

    prefixes = []
    if quantity:
        prefixes.append(f"{quantity} {core}")
    prefixes.append(core)

    for prefix in _dedupe(prefixes):
        candidates = [prefix]

        if brands:
            brand = brands[0]
            for model_count in range(min(4, len(models)), -1, -1):
                compatibility = f"{compatibility_phrase} {brand}"
                if model_count:
                    compatibility += " " + " ".join(models[:model_count])
                candidates.append(f"{prefix} {compatibility}")

        if material:
            candidates.append(f"{prefix}, {material}")

        for candidate in candidates:
            candidate = _compact_candidate(
                candidate,
                title_limit=title_limit,
                language_name=language_name,
            )
            if candidate and len(candidate) <= title_limit:
                return candidate

    return ""


def _score_title(
    title: str,
    *,
    title_limit: int,
    language_name: str,
    compatibility_phrase: str,
    facts: dict[str, Any],
) -> int:
    if not title or len(title) > title_limit:
        return -10000

    lower = title.casefold()
    if any(term.casefold() in lower for term in FORBIDDEN_TERMS):
        return -10000
    if re.search(rf"\bfor\s+{re.escape(compatibility_phrase)}\b", title, flags=re.I):
        return -10000
    if _ends_incomplete(title, language_name):
        return -10000

    score = 100
    # Prefer useful titles close to, but not forced against, the limit.
    score += min(15, len(title) // 5)

    core_terms = [
        clean(facts.get("core_keyword")),
        clean(facts.get("product_type")),
    ]
    if any(term and term.casefold() in lower for term in core_terms):
        score += 20

    brands = _fact_values(facts, "third_party_brands")
    for brand in brands:
        if brand.casefold() in lower:
            if re.search(
                rf"{re.escape(compatibility_phrase)}\s+[^,;:.]{{0,65}}{re.escape(brand)}",
                title,
                flags=re.I,
            ):
                score += 8
            else:
                return -10000

    if title.endswith((",", ";", ":", "-", "–", "—", "/")):
        return -10000
    return score


def generate_title(
    client: OpenAI,
    facts: dict[str, Any],
    language_name: str,
    compatibility_phrase: str,
    title_limit: int,
    retry_reason: str = "",
) -> str:
    prompt = f"""
You are an Amazon title specialist writing directly in {language_name}.
Return JSON only:
{{"titles": ["candidate 1", "candidate 2", "candidate 3", "candidate 4",
"candidate 5", "candidate 6", "candidate 7", "candidate 8"]}}

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

RULES:
1. Produce exactly eight materially different Amazon title candidates.
2. Target 50-{title_limit} characters. Every candidate must be at most
   {title_limit} characters including spaces and punctuation.
3. Put the exact local product noun/core search keyword near the beginning.
4. Use only 2-4 highest-value verified facts.
5. If many compatible models exist, use only 1-3 representative models.
6. Every third-party brand mention must use exactly: {compatibility_phrase}
7. Never write 'for {compatibility_phrase}' or duplicate compatibility prepositions.
8. Never mechanically truncate and never end with an incomplete phrase.
9. Never use Original, Genuine, Official, OEM, Best Seller, #1,
   Premium Quality, promotion, guarantee or authorization language.
10. Never invent facts.
11. Write directly for Amazon shoppers in {language_name}; do not translate
    an English draft word by word.
12. Keep model lists compact. Do not try to include every model.
13. Retry issue to avoid: {retry_reason or "none"}
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=700,
    )

    raw_candidates = _parse_candidates(text)
    candidates: list[str] = []

    # Score both original and conservatively compressed versions.
    for raw in raw_candidates:
        candidates.append(raw)
        compact = _compact_candidate(
            raw,
            title_limit=title_limit,
            language_name=language_name,
        )
        if compact:
            candidates.append(compact)

    fallback = _build_fact_fallback(
        facts,
        compatibility_phrase=compatibility_phrase,
        title_limit=title_limit,
        language_name=language_name,
    )
    if fallback:
        candidates.append(fallback)

    scored = [
        (
            _score_title(
                title,
                title_limit=title_limit,
                language_name=language_name,
                compatibility_phrase=compatibility_phrase,
                facts=facts,
            ),
            title,
        )
        for title in _dedupe(candidates)
    ]
    scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)

    if scored and scored[0][0] > -10000:
        return scored[0][1]

    raise ValueError(f"没有生成符合{title_limit}字符要求的完整标题")
