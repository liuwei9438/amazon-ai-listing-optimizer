
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
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def _parse_candidates(text: str) -> list[str]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return []
    data = json.loads(text[start:end + 1])
    values = data.get("titles", [])
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        title = clean(value)
        if title and title.casefold() not in {x.casefold() for x in result}:
            result.append(title)
    return result


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

    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", lower)
    if words and words[-1] in INCOMPLETE_ENDINGS.get(language_name, set()):
        return -10000

    score = 100
    score += min(12, len(title) // 8)

    core_terms = [
        str(facts.get("core_keyword", "") or ""),
        str(facts.get("product_type", "") or ""),
    ]
    if any(term and term.casefold() in lower for term in core_terms):
        score += 15

    brands = [str(x) for x in facts.get("third_party_brands", []) or []]
    for brand in brands:
        if brand.casefold() in lower:
            if re.search(
                rf"{re.escape(compatibility_phrase)}\s+[^,;:.]{{0,55}}{re.escape(brand)}",
                title,
                flags=re.I,
            ):
                score += 8
            else:
                return -10000

    if title.endswith((",", ";", ":", "-", "–", "—")):
        score -= 15
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
{{"titles": ["candidate 1", "candidate 2", "candidate 3"]}}

VERIFIED PRODUCT FACTS:
{json.dumps(facts, ensure_ascii=False)}

RULES:
1. Produce exactly three materially different Amazon title candidates.
2. Every candidate must be a complete natural title with at most {title_limit} characters,
   including spaces and punctuation.
3. Put the precise local product noun/core search keyword near the beginning.
4. Use only 2-4 highest-value facts.
5. If many models exist, use only 2-4 representative models.
6. Every brand mention must use exactly: {compatibility_phrase}
7. Never write 'for {compatibility_phrase}' or duplicate compatibility prepositions.
8. Never mechanically truncate.
9. Never end with a preposition, conjunction or article.
10. Never use Original, Genuine, Official, OEM, Best Seller, #1, Premium Quality,
    promotion, guarantee or authorization language.
11. Never invent facts.
12. Write directly for Amazon shoppers in {language_name}; do not translate word by word.
13. Retry issue to avoid: {retry_reason or "none"}
""".strip()

    text = create_response_with_backoff(
        client,
        model="gpt-4.1-mini",
        input_text=prompt,
        max_output_tokens=350,
    )
    candidates = _parse_candidates(text)

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
        for title in candidates
    ]
    scored.sort(reverse=True)
    if scored and scored[0][0] > -10000:
        return scored[0][1]

    raise ValueError(f"没有生成符合{title_limit}字符要求的完整标题")
