
from __future__ import annotations

import re
from typing import Any


FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "top rated", "hot sale",
    "promotion", "discount", "free shipping", "premium quality",
    "highest quality", "100% satisfaction", "guaranteed",
    "lifetime warranty",
]

COMPATIBILITY_PATTERNS = [
    r"\bcompatible\s+with[a-z]*\b",
    r"\bcompatible\s+con\b",
    r"\bcompatible\s+avec\b",
    r"\bkompatibel\s+mit\b",
    r"\bcompatibel\s+met\b",
    r"\bcompatible\s+met\b",
    r"\bkompatibel\s+med\b",
    r"\bcompatible\s+med\b",
    r"\bcompatibile\s+con\b",
    r"\bcompat[ií]vel\s+com\b",
    r"\bcompativel\s+com\b",
    r"\bfits?\s+for\b",
    r"\bfits?\b",
    r"\bfit\s+for\b",
    r"\bworks?\s+with\b",
    r"\bsuitable\s+for\b",
    r"\bdesigned\s+for\s+use\s+with\b",
    r"\bdesigned\s+for\s+compatibility\s+with\b",
    r"\bintended\s+for\s+use\s+with\b",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def normalize_compatibility(text: str, compatibility_phrase: str) -> str:
    value = clean(text)
    for pattern in COMPATIBILITY_PATTERNS:
        value = re.sub(pattern, compatibility_phrase, value, flags=re.I)
    return clean(value)


def remove_forbidden(text: str) -> str:
    value = clean(text)
    for term in FORBIDDEN_TERMS:
        value = re.sub(re.escape(term), "", value, flags=re.I)
    return clean(value)


def normalize_listing(
    data: dict[str, str],
    compatibility_phrase: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for key in [
        "title", "short_title", "bullet1", "bullet2", "bullet3",
        "bullet4", "bullet5", "description",
    ]:
        value = normalize_compatibility(data.get(key, ""), compatibility_phrase)
        result[key] = remove_forbidden(value)
    return result


def _brand_pattern(brand: str) -> re.Pattern[str]:
    escaped = re.escape(clean(brand))
    return re.compile(
        rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])",
        flags=re.I,
    )


def _compat_before_brand(
    text: str,
    brand_start: int,
    compatibility_phrase: str,
) -> bool:
    prefix = text[:brand_start]
    return bool(
        re.search(
            rf"{re.escape(compatibility_phrase)}\s+[^.!?;:]{{0,80}}$",
            prefix,
            flags=re.I,
        )
    )


def ensure_brand_compatibility(
    text: str,
    brands: list[str],
    compatibility_phrase: str,
) -> str:
    value = clean(text)
    for brand in brands:
        if not clean(brand):
            continue
        pattern = _brand_pattern(brand)
        matches = list(pattern.finditer(value))
        for match in reversed(matches):
            if _compat_before_brand(value, match.start(), compatibility_phrase):
                continue
            original_brand = value[match.start():match.end()]
            value = (
                value[:match.start()]
                + f"{compatibility_phrase} {original_brand}"
                + value[match.end():]
            )
    return clean(value)


def local_repair(
    data: dict[str, str],
    facts: dict[str, Any],
    compatibility_phrase: str,
) -> dict[str, str]:
    result = normalize_listing(data, compatibility_phrase)
    brands = [
        clean(value)
        for value in facts.get("third_party_brands", [])
        if clean(value)
    ]
    for key in result:
        result[key] = ensure_brand_compatibility(
            result[key],
            brands,
            compatibility_phrase,
        )

    # Remove isolated short-title numbers, but retain 1/10, 6-in-1, 2PCS, etc.
    parts = [
        part.strip()
        for part in result.get("short_title", "").split(",")
        if part.strip() and not re.fullmatch(r"\d+", part.strip())
    ]
    result["short_title"] = ", ".join(parts)
    return result


def validate_listing(
    data: dict[str, str],
    facts: dict[str, Any],
    compatibility_phrase: str,
    title_limit: int,
    highlights_limit: int,
) -> tuple[bool, str]:
    title = clean(data.get("title", ""))
    short_title = clean(data.get("short_title", ""))
    bullets = [clean(data.get(f"bullet{i}", "")) for i in range(1, 6)]
    description = clean(data.get("description", ""))

    if not title:
        return False, "标题为空"
    if len(title) > title_limit:
        return False, f"标题超过{title_limit}字符"
    if not short_title:
        return False, "产品亮点为空"
    if len(short_title) > highlights_limit:
        return False, f"产品亮点超过{highlights_limit}字符"
    if any(not bullet for bullet in bullets):
        return False, "五点描述不足5条"
    if not description:
        return False, "详情为空"

    field_map = {
        "标题": title,
        "短标题": short_title,
        **{f"要点{i}": bullets[i - 1] for i in range(1, 6)},
        "详情": description,
    }

    all_text = " ".join(field_map.values()).casefold()
    bad = [term for term in FORBIDDEN_TERMS if term.casefold() in all_text]
    if bad:
        return False, "含禁止词：" + ", ".join(bad[:3])

    brands = [
        clean(value)
        for value in facts.get("third_party_brands", [])
        if clean(value)
    ]
    for field_name, text in field_map.items():
        for brand in brands:
            pattern = _brand_pattern(brand)
            for match in pattern.finditer(text):
                if not _compat_before_brand(
                    text,
                    match.start(),
                    compatibility_phrase,
                ):
                    return (
                        False,
                        f"{field_name}中的品牌 {brand} 缺少 {compatibility_phrase}",
                    )

    # Avoid false failures. Validator checks only clear structural/compliance errors.
    return True, ""
