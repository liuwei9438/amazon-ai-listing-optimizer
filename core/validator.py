from __future__ import annotations

import difflib
import re
from typing import Any

FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "top rated", "hot sale", "promotion",
    "discount", "free shipping", "premium quality", "highest quality",
    "100% satisfaction", "guaranteed", "lifetime warranty",
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

LANGUAGE_MARKERS = {
    "Spanish": {"para", "con", "de", "del", "y", "aleación", "repuesto", "uso", "compatible"},
    "Italian": {"per", "con", "di", "del", "e", "lega", "ricambio", "uso", "compatibile"},
    "Dutch": {"voor", "met", "van", "en", "legering", "vervanging", "gebruik", "compatibel"},
    "German": {"für", "mit", "aus", "und", "ersatz", "verwendung", "kompatibel", "halterung"},
    "French": {"pour", "avec", "de", "du", "et", "alliage", "rechange", "utilisation", "compatible"},
    "Portuguese": {"para", "com", "de", "do", "e", "liga", "reposição", "uso", "compatível"},
    "Swedish": {"för", "med", "av", "och", "legering", "ersättning", "användning", "kompatibel"},
}

ENGLISH_MARKERS = {
    "for", "with", "and", "from", "replacement", "repair", "work", "stand",
    "front", "rear", "mount", "aluminum", "alloy", "design", "use", "parts",
    "support", "strong", "durable", "compatible", "product", "feature",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def shorten_at_word_boundary(text: str, limit: int) -> str:
    text = clean(text).strip(" ,;-–—")
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;-–—")


def similarity(a: str, b: str) -> float:
    a = re.sub(r"\W+", " ", clean(a).lower()).strip()
    b = re.sub(r"\W+", " ", clean(b).lower()).strip()
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def normalize_compatibility(text: str, compat: str) -> str:
    value = clean(text)
    for pattern in COMPATIBILITY_PATTERNS:
        value = re.sub(pattern, compat, value, flags=re.I)
    return clean(value)


def _brand_pattern(brand: str) -> re.Pattern[str]:
    escaped = re.escape(clean(brand))
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", flags=re.I)


def _compat_before_position(text: str, position: int, compat: str) -> bool:
    prefix = text[:position]
    pattern = rf"{re.escape(compat)}\s+[^.!?;:]{{0,80}}$"
    return bool(re.search(pattern, prefix, flags=re.I))


def ensure_brand_compatibility(text: str, brands: list[str], compat: str) -> str:
    value = normalize_compatibility(text, compat)
    for brand in brands:
        brand = clean(brand)
        if not brand:
            continue
        pattern = _brand_pattern(brand)
        for match in reversed(list(pattern.finditer(value))):
            if _compat_before_position(value, match.start(), compat):
                continue
            original_brand = value[match.start():match.end()]
            value = value[:match.start()] + f"{compat} {original_brand}" + value[match.end():]
    return clean(value)


def normalize_output(data: dict[str, Any], compat: str, title_limit: int, short_limit: int) -> dict[str, str]:
    keys = ["title", "short_title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description"]
    result = {key: normalize_compatibility(str(data.get(key, "") or ""), compat) for key in keys}
    # Keep an overlength title intact so validation can request a complete AI rewrite.
    result["short_title"] = shorten_at_word_boundary(result["short_title"], short_limit)
    return result


def _remove_forbidden(text: str) -> str:
    value = clean(text)
    for term in FORBIDDEN_TERMS:
        value = re.sub(re.escape(term), "", value, flags=re.I)
    return clean(value).strip(" ,;-–—")


def _clean_short_title_noise(text: str) -> str:
    parts = [part.strip() for part in clean(text).split(",")]
    parts = [part for part in parts if part and not re.fullmatch(r"\d+", part)]
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        key = part.casefold()
        if key not in seen:
            seen.add(key)
            result.append(part)
    return ", ".join(result)


def deterministic_repair(data: dict[str, Any], profile: dict[str, Any], analysis: dict[str, Any]) -> dict[str, str]:
    compat = str(profile["compat"])
    title_limit = int(profile["title_limit"])
    short_limit = int(profile["short_limit"])
    brands = [clean(x) for x in analysis.get("third_party_brands", []) if clean(x)]
    result = normalize_output(data, compat, title_limit, short_limit)

    for key in result:
        result[key] = ensure_brand_compatibility(_remove_forbidden(result[key]), brands, compat)

    result["short_title"] = _clean_short_title_noise(result["short_title"])
    result["short_title"] = shorten_at_word_boundary(result["short_title"], short_limit)

    facts: list[str] = []
    for field in ["functions", "usage_scenarios", "factual_selling_points", "package_contents"]:
        for item in analysis.get(field, []) or []:
            text = clean(item)
            if text and text.casefold() not in {x.casefold() for x in facts}:
                facts.append(text)
    for field in ["material", "quantity", "dimensions", "color", "voltage", "power"]:
        text = clean(analysis.get(field, ""))
        if text and text.casefold() not in {x.casefold() for x in facts}:
            facts.append(text)

    product_type = clean(analysis.get("product_type", "")) or "Product feature"
    for i in range(1, 6):
        key = f"bullet{i}"
        if not result.get(key):
            fallback = facts[i - 1] if i - 1 < len(facts) else product_type
            result[key] = ensure_brand_compatibility(fallback, brands, compat)
    if not result.get("description"):
        result["description"] = ensure_brand_compatibility(". ".join(facts[:6]) or product_type, brands, compat)
    return result


def _tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", clean(text).casefold())


def validate_target_language(data: dict[str, str], profile: dict[str, Any]) -> tuple[bool, str]:
    language = str(profile.get("language", "English"))
    if language == "English":
        return True, ""

    combined = " ".join([
        clean(data.get("title")), clean(data.get("short_title")),
        clean(data.get("bullet1")), clean(data.get("bullet2")),
        clean(data.get("description")),
    ])

    if language == "Japanese":
        if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", combined):
            return True, ""
        return False, "日语结果仍为英语或未充分本地化"

    tokens = _tokens(combined)
    if not tokens:
        return False, f"{language}结果为空或无法识别"

    markers = LANGUAGE_MARKERS.get(language, set())
    target_hits = sum(1 for token in tokens if token in markers)
    english_hits = sum(1 for token in tokens if token in ENGLISH_MARKERS)

    # Require more than a translated compatibility phrase. This catches outputs
    # where only "Compatible con/avec/met" changed but the rest stayed English.
    title_tokens = _tokens(clean(data.get("title")))
    title_target_hits = sum(1 for token in title_tokens if token in markers - {"compatible", "compatibel", "kompatibel", "compatibile", "compatível"})

    if target_hits < 3 or title_target_hits < 1:
        return False, f"{language}结果仍为英语或未充分本地化"
    if english_hits >= 8 and english_hits > target_hits * 1.5:
        return False, f"{language}结果包含过多英语内容"
    return True, ""


def validate_listing(data: dict[str, str], source_title: str, profile: dict[str, Any], analysis: dict[str, Any]) -> tuple[bool, str, int]:
    title = clean(data.get("title"))
    short_title = clean(data.get("short_title"))
    bullets = [clean(data.get(f"bullet{i}")) for i in range(1, 6)]
    desc = clean(data.get("description"))
    title_limit = int(profile["title_limit"])
    short_limit = int(profile["short_limit"])
    compat = str(profile["compat"])

    if not title:
        return False, "标题为空", 0
    if len(title) > title_limit:
        return False, f"标题超过{title_limit}字符", 50
    if not short_title:
        return False, "短标题为空", 70
    if len(short_title) > short_limit:
        return False, f"短标题超过{short_limit}字符", 70
    if any(not x for x in bullets):
        return False, "五点描述不足5条", 65
    if not desc:
        return False, "详情为空", 70

    field_values = {
        "标题": title,
        "短标题": short_title,
        **{f"要点{i}": bullets[i - 1] for i in range(1, 6)},
        "详情": desc,
    }
    all_text = " ".join(field_values.values()).lower()
    bad = [x for x in FORBIDDEN_TERMS if x in all_text]
    if bad:
        return False, "含禁止词：" + ", ".join(bad[:3]), 40
    if re.search(r"\b(fits?|fit for|works? with|suitable for)\b", all_text, flags=re.I):
        return False, f"兼容表达未统一为 {compat}", 55

    brands = [clean(x) for x in analysis.get("third_party_brands", []) if clean(x)]
    for field_name, segment in field_values.items():
        for brand in brands:
            for match in _brand_pattern(brand).finditer(segment):
                if not _compat_before_position(segment, match.start(), compat):
                    return False, f"{field_name}中的品牌 {brand} 缺少 {compat}", 50

    incomplete_endings = {
        "English": {"for", "with", "and", "to", "of", "the"},
        "Spanish": {"para", "con", "de", "del", "y", "la", "el"},
        "Italian": {"per", "con", "di", "del", "e", "la", "il"},
        "Dutch": {"voor", "met", "van", "en", "de", "het"},
        "German": {"für", "mit", "von", "und", "der", "die", "das"},
        "French": {"pour", "avec", "de", "du", "et", "la", "le"},
        "Portuguese": {"para", "com", "de", "do", "e", "a", "o"},
        "Swedish": {"för", "med", "av", "och", "en", "ett"},
    }
    language_name = str(profile.get("language", "English"))
    last_token_match = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", title.casefold())
    if last_token_match and last_token_match[-1] in incomplete_endings.get(language_name, set()):
        return False, "标题结尾不完整，需要重新压缩为完整短句", 45

    language_ok, language_reason = validate_target_language(data, profile)
    if not language_ok:
        return False, language_reason, 45

    score = 100
    if len(title) < 35:
        score -= 8
    if similarity(title, source_title) >= 0.94:
        score -= 12
    if len(set(title.lower().split())) < max(3, int(len(title.split()) * 0.65)):
        score -= 5
    if not analysis.get("product_type"):
        score -= 5
    return True, "", max(0, score)
