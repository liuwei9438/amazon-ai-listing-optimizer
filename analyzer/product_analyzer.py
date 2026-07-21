from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

from core.models import ProductRecord

from .analyzer_schema import ProductAnalysis

_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+./-]{1,}")
_MODEL_RE = re.compile(r"\b(?=[A-Z0-9-]{2,18}\b)(?=[A-Z0-9-]*\d)[A-Z][A-Z0-9-]*\b")
_QUANTITY_RE = re.compile(r"\b(\d{1,4}\s*(?:PCS?|PIECES?|PACK|COUNT|CT|个|件|套|只|片))\b", re.I)
_DIMENSION_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?(?:\s*(?:x|×)\s*\d+(?:\.\d+)?)?\s*(?:mm|cm|m|in|inch|inches|ft)?\b",
    re.I,
)
_WEIGHT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|g|kg|oz|lb|lbs|pounds?)\b", re.I)
_SCALE_RE = re.compile(r"\b1\s*/\s*\d{1,3}\b")

MATERIALS = (
    "aluminum alloy", "aluminium alloy", "stainless steel", "carbon steel",
    "steel", "aluminum", "aluminium", "nylon", "plastic", "silicone",
    "rubber", "brass", "copper", "ceramic", "glass", "wood", "abs",
)
COLORS = (
    "black", "white", "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "gray", "grey", "silver", "gold", "brown", "clear", "transparent",
)
BRANDS = (
    "Dyson", "Traxxas", "Axial", "BMW", "Honda", "Yamaha", "Kawasaki",
    "Suzuki", "Epson", "Canon", "Brother", "HP", "LG", "Samsung",
    "Thermomix", "Vorwerk", "DeWalt", "Makita", "Milwaukee", "Bosch",
)
STOPWORDS = {
    "with", "without", "from", "into", "your", "this", "that", "these", "those",
    "compatible", "compatibility", "product", "item", "parts", "part", "accessory",
    "accessories", "replacement", "for", "and", "the", "a", "an", "of", "to",
    "in", "on", "is", "are", "set", "pack", "pcs", "piece", "pieces",
}
PRODUCT_TERMS = (
    "bumper mount", "steering damper", "thread spool", "dust cap", "repair stand",
    "work stand", "skid plate", "gearbox housing", "wheel rim", "power button",
    "print head", "printing head", "filter", "brush", "adapter", "mount", "bracket",
    "cover", "holder", "nozzle", "blade", "motor", "switch", "cable", "connector",
)


def _clean(value: object) -> str:
    return _SPACE_RE.sub(" ", str(value or "").strip())


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean(value)
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return tuple(result)


def _raw_value(record: ProductRecord, aliases: tuple[str, ...]) -> str:
    normalized = {re.sub(r"[\s_\-()（）]+", "", str(k)).lower(): v for k, v in record.raw_data.items()}
    for alias in aliases:
        key = re.sub(r"[\s_\-()（）]+", "", alias).lower()
        if key in normalized and _clean(normalized[key]):
            return _clean(normalized[key])
    return ""


def _source(record: ProductRecord) -> str:
    values = [record.title, *record.bullets, record.description]
    return _clean(" | ".join(value for value in values if _clean(value)))


def _find_phrase(text: str, phrases: Iterable[str]) -> str:
    lower = text.casefold()
    for phrase in phrases:
        if re.search(rf"(?<![A-Za-z]){re.escape(phrase.casefold())}(?![A-Za-z])", lower):
            return phrase
    return ""


def _extract_brand(text: str, explicit: str) -> tuple[str, tuple[str, ...]]:
    found = [brand for brand in BRANDS if re.search(rf"\b{re.escape(brand)}\b", text, re.I)]
    if explicit:
        found.insert(0, explicit)
    unique = _unique(found)
    # Brand is kept separate from compatibility. Compatibility wording is handled by rule engine later.
    return (unique[0] if unique else ""), unique


def _extract_models(text: str, brands: tuple[str, ...]) -> tuple[str, ...]:
    brand_keys = {b.casefold() for b in brands}
    candidates = []
    for token in _MODEL_RE.findall(text):
        if token.casefold() in brand_keys:
            continue
        if token.upper() in {"PCS", "ABS", "LED", "USB", "CNC", "RC"}:
            continue
        candidates.append(token)
    return _unique(candidates)[:20]


def _extract_product_type(text: str) -> str:
    lower = text.casefold()
    for term in PRODUCT_TERMS:
        if term in lower:
            return term.title()
    # Conservative fallback: first meaningful words before compatibility/for clauses.
    head = re.split(r"\b(?:compatible\s+with|for|fits?)\b", text, maxsplit=1, flags=re.I)[0]
    tokens = [t for t in _TOKEN_RE.findall(head) if t.casefold() not in STOPWORDS]
    return " ".join(tokens[-5:]) if tokens else ""


def _extract_keywords(text: str, product_type: str, material: str) -> tuple[str, ...]:
    tokens = [token.casefold() for token in _TOKEN_RE.findall(text)]
    counts = Counter(token for token in tokens if token not in STOPWORDS and len(token) >= 3)
    seeded = list(_TOKEN_RE.findall(product_type)) + list(_TOKEN_RE.findall(material))
    ranked = seeded + [token for token, _ in counts.most_common(20)]
    return _unique(ranked)[:12]


def analyze_record(record: ProductRecord) -> ProductAnalysis:
    text = _source(record)
    explicit_brand = _raw_value(record, ("品牌", "brand", "brand name"))
    explicit_material = _raw_value(record, ("材料", "材质", "material"))
    explicit_color = _raw_value(record, ("颜色", "color", "colour"))
    explicit_dimensions = _raw_value(record, ("尺寸", "规格", "dimensions", "dimension", "size"))
    explicit_weight = _raw_value(record, ("重量", "产品重量", "weight", "item weight"))

    material = explicit_material or _find_phrase(text, MATERIALS)
    color = explicit_color or _find_phrase(text, COLORS)
    quantity_match = _QUANTITY_RE.search(text)
    dimension_match = _DIMENSION_RE.search(text)
    weight_match = _WEIGHT_RE.search(text)
    brand, compatible_brands = _extract_brand(text, explicit_brand)
    compatible_models = _extract_models(text, compatible_brands)
    product_type = _extract_product_type(text)
    applications = _unique(_SCALE_RE.findall(text))

    values = {
        "product_type": product_type,
        "brand": brand,
        "compatible_brands": compatible_brands,
        "compatible_models": compatible_models,
        "material": material,
        "color": color,
        "quantity": quantity_match.group(1) if quantity_match else "",
        "dimensions": explicit_dimensions or (dimension_match.group(0) if dimension_match else ""),
        "weight": explicit_weight or (weight_match.group(0) if weight_match else ""),
        "applications": applications,
    }
    evidence: dict[str, tuple[str, ...]] = {}
    for field, value in values.items():
        items = value if isinstance(value, tuple) else ((value,) if value else ())
        evidence[field] = tuple(item for item in items if item and item.casefold() in text.casefold())
        if field in {"brand", "material", "color", "dimensions", "weight"} and value and not evidence[field]:
            # Explicit structured source column is valid evidence even if absent from title/body.
            evidence[field] = (f"结构化字段：{value}",)

    return ProductAnalysis(
        row_number=record.row_number,
        sku=record.sku,
        product_type=product_type,
        brand=brand,
        compatible_brands=compatible_brands,
        compatible_models=compatible_models,
        material=material,
        color=color,
        quantity=quantity_match.group(1) if quantity_match else "",
        dimensions=explicit_dimensions or (dimension_match.group(0) if dimension_match else ""),
        weight=explicit_weight or (weight_match.group(0) if weight_match else ""),
        applications=applications,
        keywords=_extract_keywords(text, product_type, material),
        evidence=evidence,
        source_text=text,
    )


def analyze_records(records: Iterable[ProductRecord]) -> tuple[ProductAnalysis, ...]:
    return tuple(analyze_record(record) for record in records)
