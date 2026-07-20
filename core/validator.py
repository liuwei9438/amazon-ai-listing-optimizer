
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
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;-–—")


def normalize_compatibility(text: str, compatibility_phrase: str) -> str:
    value = clean(text)
    for pattern in COMPATIBILITY_PATTERNS:
        value = re.sub(pattern, compatibility_phrase, value, flags=re.I)

    # Remove duplicated prepositions such as "for Compatible with".
    value = re.sub(
        rf"\b(?:for|pour|para|per|voor|für)\s+({re.escape(compatibility_phrase)})\b",
        r"\1",
        value,
        flags=re.I,
    )
    value = re.sub(
        rf"(?:{re.escape(compatibility_phrase)}\s+){{2,}}",
        f"{compatibility_phrase} ",
        value,
        flags=re.I,
    )
    return clean(value)


def remove_forbidden(text: str) -> str:
    value = clean(text)
    for term in FORBIDDEN_TERMS:
        value = re.sub(re.escape(term), "", value, flags=re.I)
    return clean(value)


def _brand_pattern(brand: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(clean(brand))}(?![A-Za-z0-9])",
        flags=re.I,
    )


def _compat_before_brand(text: str, brand_start: int, compatibility_phrase: str) -> bool:
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
    value = normalize_compatibility(text, compatibility_phrase)
    for brand in brands:
        brand = clean(brand)
        if not brand:
            continue
        matches = list(_brand_pattern(brand).finditer(value))
        for match in reversed(matches):
            if _compat_before_brand(value, match.start(), compatibility_phrase):
                continue
            value = (
                value[:match.start()]
                + f"{compatibility_phrase} {value[match.start():match.end()]}"
                + value[match.end():]
            )
    return clean(value)


def local_repair(
    data: dict[str, str],
    facts: dict[str, Any],
    compatibility_phrase: str,
) -> dict[str, str]:
    brands = [
        clean(value)
        for value in facts.get("third_party_brands", [])
        if clean(value)
    ]
    result: dict[str, str] = {}
    for key in [
        "title", "short_title", "bullet1", "bullet2", "bullet3",
        "bullet4", "bullet5", "description",
    ]:
        value = remove_forbidden(data.get(key, ""))
        if key == "short_title":
            # Item Highlights should not contain brands/models/compatibility text.
            value = normalize_compatibility(value, compatibility_phrase)
        else:
            value = ensure_brand_compatibility(value, brands, compatibility_phrase)
        result[key] = clean(value)

    parts = [
        part.strip()
        for part in result.get("short_title", "").split(",")
        if part.strip() and not re.fullmatch(r"\d+", part.strip())
    ]
    result["short_title"] = ", ".join(parts)
    return result


def validate_body(data: dict[str, str], facts: dict[str, Any], compatibility_phrase: str) -> tuple[bool, str]:
    bullets = [clean(data.get(f"bullet{i}", "")) for i in range(1, 6)]
    description = clean(data.get("description", ""))
    if any(not bullet for bullet in bullets):
        return False, "五点描述不足5条"
    if not description:
        return False, "详情为空"
    return _validate_compliance(
        {**{f"要点{i}": bullets[i - 1] for i in range(1, 6)}, "详情": description},
        facts,
        compatibility_phrase,
    )


def validate_title(
    title: str,
    facts: dict[str, Any],
    compatibility_phrase: str,
    title_limit: int,
) -> tuple[bool, str]:
    value = clean(title)
    if not value:
        return False, "标题为空"
    if len(value) > title_limit:
        return False, f"标题超过{title_limit}字符"
    if re.search(rf"\bfor\s+{re.escape(compatibility_phrase)}\b", value, flags=re.I):
        return False, "标题出现重复兼容介词"
    return _validate_compliance({"标题": value}, facts, compatibility_phrase)


def validate_highlights(short_title: str, highlights_limit: int) -> tuple[bool, str]:
    value = clean(short_title)
    if not value:
        return False, "产品亮点为空"
    if len(value) > highlights_limit:
        return False, f"产品亮点超过{highlights_limit}字符"

    # Item Highlights should normally not consume space with compatibility language.
    if any(re.search(pattern, value, flags=re.I) for pattern in COMPATIBILITY_PATTERNS):
        return False, "产品亮点不应包含兼容品牌表达"
    return True, ""


def validate_listing(
    data: dict[str, str],
    facts: dict[str, Any],
    compatibility_phrase: str,
    title_limit: int,
    highlights_limit: int,
) -> tuple[bool, str]:
    for validator in [
        lambda: validate_title(data.get("title", ""), facts, compatibility_phrase, title_limit),
        lambda: validate_highlights(data.get("short_title", ""), highlights_limit),
        lambda: validate_body(data, facts, compatibility_phrase),
    ]:
        ok, reason = validator()
        if not ok:
            return ok, reason
    return True, ""


def _validate_compliance(
    field_map: dict[str, str],
    facts: dict[str, Any],
    compatibility_phrase: str,
) -> tuple[bool, str]:
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
            for match in _brand_pattern(brand).finditer(text):
                if not _compat_before_brand(text, match.start(), compatibility_phrase):
                    return False, f"{field_name}中的品牌 {brand} 缺少 {compatibility_phrase}"
    return True, ""
