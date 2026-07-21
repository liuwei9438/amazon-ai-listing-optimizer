from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

from .models import FieldMap

TITLE_NAMES = ("标题(必填)", "标题", "title", "product title")
SHORT_TITLE_NAMES = ("短标题", "short title", "short_title", "item highlights")
DESC_NAMES = ("简介", "详情", "描述", "description", "product description")
IMAGE_NAMES = (
    "产品图片", "产品图", "图片", "图片链接", "主图", "主图链接",
    "image", "images", "image url", "image urls", "product image",
    "product images", "main image", "main images",
)
SKU_NAMES = ("sku", "seller sku", "子sku", "父sku", "child sku", "parent sku")
LANGUAGE_NAMES = ("语言", "language")
BULLET_GROUPS = tuple(
    (f"要点{i}", f"bullet{i}", f"bullet {i}", f"bullet point {i}")
    for i in range(1, 6)
)

_IMAGE_URL_RE = re.compile(
    r"https?://[^\s|]+(?:\.(?:jpe?g|png|webp|gif|bmp)(?:\?[^\s|]*)?|/[^\s|]*)",
    re.I,
)


def _normalized(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def find_named_column(columns: Iterable[object], candidates: Iterable[str]) -> str | None:
    cols = list(columns)
    exact = {_normalized(c): str(c) for c in cols}
    for candidate in candidates:
        if _normalized(candidate) in exact:
            return exact[_normalized(candidate)]
    for col in cols:
        norm = _normalized(col)
        if any(_normalized(candidate) in norm for candidate in candidates):
            return str(col)
    return None


def _image_content_score(series: pd.Series) -> float:
    values = [str(v).strip() for v in series.tolist() if str(v).strip()]
    if not values:
        return 0.0
    sample = values[:100]
    hits = sum(bool(_IMAGE_URL_RE.search(v)) for v in sample)
    return hits / len(sample)


def detect_image_column(df: pd.DataFrame) -> tuple[str | None, dict[str, float]]:
    named = find_named_column(df.columns, IMAGE_NAMES)
    scores = {str(col): _image_content_score(df[col]) for col in df.columns}
    if named:
        return named, scores
    if scores:
        best_col, best_score = max(scores.items(), key=lambda item: item[1])
        if best_score >= 0.50:
            return best_col, scores
    return None, scores


def detect_fields(df: pd.DataFrame) -> tuple[FieldMap, dict[str, object]]:
    image_col, image_scores = detect_image_column(df)
    bullets = tuple(
        col for group in BULLET_GROUPS
        if (col := find_named_column(df.columns, group)) is not None
    )
    fields = FieldMap(
        title=find_named_column(df.columns, TITLE_NAMES),
        short_title=find_named_column(df.columns, SHORT_TITLE_NAMES),
        description=find_named_column(df.columns, DESC_NAMES),
        images=image_col,
        sku=find_named_column(df.columns, SKU_NAMES),
        language=find_named_column(df.columns, LANGUAGE_NAMES),
        bullets=bullets,
    )
    diagnostics = {
        "column_count": len(df.columns),
        "row_count": len(df),
        "columns": [str(c) for c in df.columns],
        "image_content_scores": image_scores,
    }
    return fields, diagnostics
