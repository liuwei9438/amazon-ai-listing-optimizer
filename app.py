import hashlib
import io
import difflib
import json
import random
import re
import time
import zipfile
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
import streamlit as st
import cloudinary
import cloudinary.uploader
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from openai import OpenAI
from core.ai_pipeline import optimize_listing

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")

VERSION = "V2.0-core-P1.2-test"
MAX_TITLE_LEN = 75
MAX_SHORT_TITLE_LEN = 60
SHORT_TITLE_NAMES = ["短标题", "Short Title", "short_title"]
IMAGE_SIZE = (1600, 1600)
IMAGE_SEPARATOR = " | "
TITLE_SIMILARITY_LIMIT = 0.94
MAX_MODELS_IN_TITLE = 4


LANGUAGES = {
    "英语": {"language": "English", "compat": "Compatible with"},
    "西班牙语": {"language": "Spanish", "compat": "Compatible con"},
    "意大利语": {"language": "Italian", "compat": "Compatibile con"},
    "荷兰语": {"language": "Dutch", "compat": "Compatibel met"},
    "日语": {"language": "Japanese", "compat": "に対応"},
    "德语": {"language": "German", "compat": "Kompatibel mit"},
    "法语": {"language": "French", "compat": "Compatible avec"},
    "葡萄牙语": {"language": "Portuguese", "compat": "Compatível com"},
    "瑞典语": {"language": "Swedish", "compat": "Kompatibel med"},
}

FORBIDDEN_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized",
    "best seller", "bestseller", "#1", "top rated", "hot sale", "promotion",
    "discount", "free shipping", "premium quality", "highest quality",
    "100% satisfaction", "guaranteed", "lifetime warranty",
]

NOISE_PATTERNS = [
    r"manufacturer\s*[:：]?.*", r"asin\s*[:：]?\s*[A-Z0-9]{10}.*",
    r"item model number\s*[:：]?.*", r"best sellers rank\s*[:：]?.*",
    r"date first available\s*[:：]?.*", r"seller\s*[:：]?.*",
    r"welcome to .*store.*", r"thank you for choosing.*", r"our store.*",
    r"customer service.*", r"contact us.*", r"shipping.*", r"delivery.*",
]

TITLE_NAMES = ["标题(必填)", "标题", "Title", "Product Title"]
DESC_NAMES = ["简介", "详情", "描述", "Description", "Product Description"]
IMAGE_NAMES = ["产品图", "图片", "Images", "Product Images"]
SKU_NAMES = ["SKU", "sku", "子SKU"]
BULLET_NAMES = [[f"要点{i}", f"Bullet{i}", f"Bullet Point {i}"] for i in range(1, 6)]


@dataclass
class RowResult:
    index: int
    status: str
    reason: str = ""


def clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).replace("\r", "\n")
    lines = []
    for raw in re.split(r"\n+", text):
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        low = line.lower()
        if any(re.search(p, low, flags=re.I) for p in NOISE_PATTERNS):
            continue
        for term in FORBIDDEN_TERMS:
            line = re.sub(re.escape(term), "", line, flags=re.I)
        line = re.sub(r"\s{2,}", " ", line).strip(" -–—,.;:")
        if line:
            lines.append(line)
    return "\n".join(lines)


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    exact = {str(c).strip().lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in exact:
            return exact[name.lower()]
    for c in df.columns:
        cn = str(c).strip().lower()
        if any(name.lower() in cn for name in candidates):
            return c
    return None


def parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 返回内容不是有效 JSON")
    return json.loads(text[start:end + 1])


def extract_model_tokens(text: str) -> list[str]:
    """Extract likely product model/part-number tokens conservatively."""
    if not text:
        return []
    tokens = re.findall(r"\b[A-Z]{0,4}\d[A-Z0-9-]{1,14}\b", text, flags=re.I)
    blocked = {"1600", "2024", "2025", "2026"}
    out=[]
    for t in tokens:
        u=t.upper().strip('-')
        if u in blocked or len(u)<2:
            continue
        if u not in out:
            out.append(u)
    return out


def title_similarity(a: str, b: str) -> float:
    a=re.sub(r"\W+"," ",clean_text(a).lower()).strip()
    b=re.sub(r"\W+"," ",clean_text(b).lower()).strip()
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None,a,b).ratio()


def seo_score(data: dict[str,str], language: str) -> int:
    score=100
    title=clean_text(data.get("title",""))
    short_title=clean_text(data.get("short_title",""))
    bullets=[clean_text(data.get(f"bullet{i}","")) for i in range(1,6)]
    desc=clean_text(data.get("description",""))
    all_text=" ".join([title,short_title,*bullets,desc]).lower()
    if not title: score-=35
    if len(title)>MAX_TITLE_LEN: score-=20
    if len(title)<35: score-=8
    if not short_title: score-=10
    if len(short_title)>MAX_SHORT_TITLE_LEN: score-=10
    if any(not b for b in bullets): score-=20
    if not desc: score-=15
    if any(t in all_text for t in FORBIDDEN_TERMS): score-=25
    if re.search(r"\b(fits?|fit for|works? with|suitable for)\b", all_text): score-=15
    if len(set(w.lower() for w in title.split())) < max(3, int(len(title.split())*0.65)): score-=5
    return max(0,min(100,score))


def stable_cache_key(source: dict[str,Any], language: str) -> str:
    payload=json.dumps({"schema":"v2.0-core-p1.1","language":language,"source":source},ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def build_prompt(source: dict[str, Any], language: str, retry_reason: str = "") -> str:
    cfg = LANGUAGES[language]
    extra = f"\nPrevious output failed QA because: {retry_reason}\n" if retry_reason else ""
    return f"""
You are an Amazon listing SEO and compliance writer. Target output language: {language}.
Write in {cfg['language']}.
Return JSON only with keys: title, short_title, bullet1, bullet2, bullet3, bullet4, bullet5, description.

NON-NEGOTIABLE RULES:
1. Every product is a non-original compatibility product.
2. Every time a third-party brand appears, it must be introduced with the exact local compatibility phrase: {cfg['compat']}.
3. Never use Original, Genuine, Official, OEM, Authentic, authorized-brand implications, promotions, rankings, best-seller claims or unverifiable superlatives.
4. Understand all supplied product information as one whole, then rewrite title, five bullets and description. Do not translate sentence by sentence.
5. Preserve facts exactly: quantity, color, dimensions, material, voltage, power, package contents, compatible models and part numbers.
6. Remove seller/store/manufacturer/ASIN/Best Sellers Rank/shipping/customer-service/platform noise.
7. Title must be newly rewritten, natural, search-focused and no longer than {MAX_TITLE_LEN} characters including spaces.
8. Produce exactly five useful, factual bullet points.
9. Do not invent missing facts.
10. If more than four compatible model numbers are supplied, keep only 2-4 representative models in the title and place the complete model list in bullets or description.
11. The rewritten title must be materially different in wording/order from the source while preserving facts.
12. short_title must be a concise merchandising/search summary no longer than {MAX_SHORT_TITLE_LEN} characters including spaces.
13. Build short_title from the complete product information. Include only facts actually present, prioritizing: core product noun, material, use scenario, main function, strongest factual benefit, and high-value search keywords.
14. Do not mechanically copy the long title. Do not invent material, scenario, function, benefit, or keywords. Omit any category that is not supported by the source.
15. If a third-party brand appears in short_title, apply the same exact local compatibility phrase: {cfg['compat']}.
{extra}
SOURCE DATA:
{json.dumps(source, ensure_ascii=False)}
""".strip()


def call_ai(client: OpenAI, source: dict[str, Any], language: str, retry_reason: str = "") -> dict[str, str]:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=build_prompt(source, language, retry_reason),
    )
    return parse_json(response.output_text)


def normalize_compatibility_text(text: str, language: str) -> str:
    """Normalize common AI compatibility variants before QA.

    This avoids false failures such as `Compatible Withr LG` while still
    enforcing one fixed compatibility phrase in exported copy.
    """
    if not text:
        return ""
    compat = LANGUAGES[language]["compat"]
    value = clean_text(text)
    # Fix misspellings/case variants beginning with Compatible With...
    value = re.sub(r"\bcompatible\s+with[a-z]*\b", compat, value, flags=re.I)
    # Convert alternative compatibility wording to the fixed phrase.
    alternatives = [
        r"\bfits?\s+for\b", r"\bfits?\b", r"\bfit\s+for\b",
        r"\bworks?\s+with\b", r"\bsuitable\s+for\b",
        r"\bdesigned\s+for\s+use\s+with\b",
        r"\bdesigned\s+for\s+compatibility\s+with\b",
        r"\bintended\s+for\s+use\s+with\b",
    ]
    for pattern in alternatives:
        value = re.sub(pattern, compat, value, flags=re.I)
    value = re.sub(r"\s{2,}", " ", value).strip()
    return value


def normalize_ai_output(data: dict[str, Any], language: str) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key in ["title", "short_title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description"]:
        normalized[key] = normalize_compatibility_text(str(data.get(key, "") or ""), language)
    return normalized


def shorten_title_at_word_boundary(title: str, max_len: int = MAX_TITLE_LEN) -> str:
    title = re.sub(r"\s+", " ", title).strip(" ,;-–—")
    if len(title) <= max_len:
        return title
    cut = title[: max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;-–—")


def qa_text(data: dict[str, str], original_title: str, language: str) -> tuple[bool, str]:
    cfg = LANGUAGES[language]
    title = clean_text(data.get("title", ""))
    short_title = clean_text(data.get("short_title", ""))
    bullets = [clean_text(data.get(f"bullet{i}", "")) for i in range(1, 6)]
    desc = clean_text(data.get("description", ""))
    if not title:
        return False, "标题为空"
    similarity = title_similarity(title, original_title)
    if similarity >= TITLE_SIMILARITY_LIMIT:
        return False, f"标题改写不足，相似度 {similarity:.0%}"
    if len(title) > MAX_TITLE_LEN:
        return False, f"标题超过 {MAX_TITLE_LEN} 字符"
    if not short_title:
        return False, "短标题为空"
    if len(short_title) > MAX_SHORT_TITLE_LEN:
        return False, f"短标题超过 {MAX_SHORT_TITLE_LEN} 字符"
    original_models = extract_model_tokens(original_title)
    title_models = extract_model_tokens(title)
    if len(original_models) > MAX_MODELS_IN_TITLE and len(title_models) > MAX_MODELS_IN_TITLE:
        return False, "标题型号堆砌，需压缩到4个以内"
    if any(not b for b in bullets):
        return False, "五点描述不足5条"
    if not desc:
        return False, "详情为空"
    all_text = " ".join([title, short_title, *bullets, desc]).lower()
    bad = [term for term in FORBIDDEN_TERMS if term in all_text]
    if bad:
        return False, "含禁止词：" + ", ".join(bad[:3])
    # 标准化后仍出现替代兼容表达才判定失败。不要把普通的“designed for easy use”误判为品牌兼容错误。
    if re.search(r"\b(fits?\s+for|fit\s+for|works?\s+with|suitable\s+for)\b", all_text, flags=re.I):
        return False, f"兼容表达未统一为 {cfg['compat']}"
    return True, ""


def split_images(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    parts = [p.strip() for p in re.split(r"\s*\|\s*|\n+", str(value)) if p.strip()]
    seen, result = set(), []
    for url in parts:
        normalized = url.strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def stable_shuffle_secondary(images: list[str], sku: str) -> list[str]:
    if len(images) <= 2:
        return images
    first, rest = images[0], images[1:]
    seed_text = sku or first
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    rng.shuffle(rest)
    return [first, *rest]


def download_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def _near_white_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Return the bounding box of the visible product on a white/near-white background."""
    rgb = img.convert("RGB")
    # A pixel belongs to the product when at least one channel is clearly below white.
    mask = rgb.point(lambda value: 255 if value < 242 else 0).convert("L")
    return mask.getbbox()


def _edge_density(img: Image.Image) -> float:
    """Small heuristic used to avoid mirroring images that probably contain text/labels."""
    small = ImageOps.contain(img.convert("L"), (420, 420), Image.Resampling.LANCZOS)
    edges = small.filter(ImageFilter.FIND_EDGES)
    hist = edges.histogram()
    strong = sum(hist[70:])
    total = max(1, small.width * small.height)
    return strong / total


def _symmetry_score(img: Image.Image) -> float:
    """Lower values mean the object is more horizontally symmetric and safer to mirror."""
    small = ImageOps.contain(img.convert("L"), (360, 360), Image.Resampling.LANCZOS)
    flipped = ImageOps.mirror(small)
    diff = ImageOps.grayscale(Image.blend(small.convert("RGB"), flipped.convert("RGB"), 0.5))
    # Compare original and flipped through a difference image without NumPy.
    from PIL import ImageChops
    delta = ImageChops.difference(small, flipped)
    hist = delta.histogram()
    weighted = sum(i * count for i, count in enumerate(hist))
    return weighted / max(1, 255 * small.width * small.height)


def _prepare_product(img: Image.Image) -> Image.Image:
    background = Image.new("RGBA", img.size, "white")
    background.alpha_composite(img)
    rgb = background.convert("RGB")
    bbox = _near_white_bbox(rgb)
    if bbox:
        # Keep a small safety margin around the detected product.
        left, top, right, bottom = bbox
        pad_x = max(8, int((right - left) * 0.035))
        pad_y = max(8, int((bottom - top) * 0.035))
        bbox = (
            max(0, left - pad_x), max(0, top - pad_y),
            min(rgb.width, right + pad_x), min(rgb.height, bottom + pad_y),
        )
        rgb = rgb.crop(bbox)
    return rgb


def _enhance_clarity(img: Image.Image) -> Image.Image:
    # Stronger than P1.2, but still avoids inventing product details.
    img = ImageOps.autocontrast(img, cutoff=0.35)
    img = ImageEnhance.Contrast(img).enhance(1.07)
    img = ImageEnhance.Brightness(img).enhance(1.015)
    img = ImageEnhance.Color(img).enhance(1.025)
    img = ImageEnhance.Sharpness(img).enhance(1.40)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.55, percent=145, threshold=2))
    return img


def process_main_image(img: Image.Image, seed_text: str = "") -> tuple[Image.Image, str]:
    """Create a visibly differentiated 1600x1600 white-background main image.

    The strategy is deterministic for the same SKU/source. It prefers a tasteful angle
    change when the product shape allows it. If a stronger rotation would look awkward,
    it uses a horizontal mirror only when the image appears safe (low text-like edge
    density or high left/right symmetry). Product facts are never generated or redrawn.
    """
    product = _prepare_product(img)
    w, h = product.size
    aspect = max(w, h) / max(1, min(w, h))
    occupancy = (w * h) / max(1, img.width * img.height)
    edge_density = _edge_density(product)
    symmetry = _symmetry_score(product)

    seed = int(hashlib.sha256((seed_text or f"{w}x{h}").encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    # Text/label-heavy images should not be mirrored. Elongated items get a smaller angle.
    likely_text = edge_density > 0.115
    mirror_safe = (not likely_text) and (symmetry < 0.19 or edge_density < 0.075)

    if aspect <= 1.85:
        angle = rng.choice([-10, -8, 8, 10])
    elif aspect <= 2.8:
        angle = rng.choice([-6, -5, 5, 6])
    else:
        angle = rng.choice([-4, 4])

    # Large, already tightly composed objects can look awkward with rotation.
    rotation_awkward = occupancy > 0.78 or (aspect > 3.2 and abs(angle) > 4)
    use_mirror = rotation_awkward and mirror_safe
    # Create more visible differentiation for a subset of safe images.
    if mirror_safe and rng.random() < 0.30:
        use_mirror = True

    transform_parts = []
    if use_mirror:
        product = ImageOps.mirror(product)
        transform_parts.append("镜像")
        # Mirror-only is visually clear; add only a tiny angle for natural composition.
        if aspect < 2.5 and rng.random() < 0.35:
            tiny = rng.choice([-3, 3])
            product = product.rotate(tiny, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white")
            transform_parts.append(f"旋转{tiny}°")
    else:
        product = product.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white")
        transform_parts.append(f"旋转{angle}°")

    # Re-crop the white corners created by rotation, then fit to a larger product area.
    bbox = _near_white_bbox(product)
    if bbox:
        product = product.crop(bbox)
    product = ImageOps.contain(product, (1460, 1460), Image.Resampling.LANCZOS)
    product = _enhance_clarity(product)

    canvas = Image.new("RGB", IMAGE_SIZE, "white")
    x = (IMAGE_SIZE[0] - product.width) // 2
    y = (IMAGE_SIZE[1] - product.height) // 2
    canvas.paste(product, (x, y))
    return canvas, "+".join(transform_parts) + "+高清增强"


def image_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


def cloudinary_ready() -> bool:
    required = ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]
    return all(bool(st.secrets.get(k, "")) for k in required)


def configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_main_image_to_cloudinary(data: bytes, sku: str, source_url: str) -> str:
    """Upload processed main image and return Cloudinary's complete HTTPS URL.

    The public ID is deterministic, so reprocessing the same SKU overwrites the old
    asset instead of generating unlimited duplicates.
    """
    if not cloudinary_ready():
        raise RuntimeError("未配置 Cloudinary Secrets")
    configure_cloudinary()
    safe_sku = re.sub(r"[^A-Za-z0-9_-]+", "_", sku or "product").strip("_") or "product"
    source_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:10]
    public_id = f"{safe_sku}_{source_hash}"
    buffer = io.BytesIO(data)
    result = cloudinary.uploader.upload(
        buffer,
        resource_type="image",
        asset_folder="optimized_main_images",
        public_id=public_id,
        overwrite=True,
        unique_filename=False,
        format="jpg",
        invalidate=True,
        tags=["amazon-main-image", safe_sku],
    )
    secure_url = str(result.get("secure_url", "")).strip()
    if not secure_url.startswith("https://"):
        raise RuntimeError("Cloudinary 未返回有效 HTTPS 图片链接")
    return secure_url


def output_excel(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    export_df = df.drop(columns=[c for c in df.columns if str(c).startswith("__")], errors="ignore")
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False)
    return out.getvalue()


def build_image_zip(files: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return out.getvalue()


def optimize_row_text(
    client: OpenAI,
    result: pd.DataFrame,
    idx: Any,
    source_row: pd.Series,
    title_col: str,
    bullet_cols: list[str],
    desc_col: str,
    short_title_col: str,
    language: str,
    max_attempts: int = 4,
) -> tuple[bool, str]:
    source = {
        "title": clean_text(source_row.get(title_col, "")),
        "bullet_points": [clean_text(source_row.get(c, "")) for c in bullet_cols],
        "description": clean_text(source_row.get(desc_col, "")),
        "color_or_variant": clean_text(source_row.get("颜色", "")),
    }
    cache_key = stable_cache_key(source, language)
    cached = get_session_dict("text_cache").get(cache_key)
    if cached:
        data = cached.get("data", cached).copy()
        success, reason = qa_text(data, source["title"], language)
        if success:
            result.at[idx, title_col] = shorten_title_at_word_boundary(clean_text(data["title"]), MAX_TITLE_LEN)
            result.at[idx, short_title_col] = shorten_title_at_word_boundary(clean_text(data.get("short_title", "")), MAX_SHORT_TITLE_LEN)
            for i, c in enumerate(bullet_cols, start=1):
                result.at[idx, c] = clean_text(data[f"bullet{i}"])
            result.at[idx, desc_col] = clean_text(data["description"])
            result.at[idx, "优化状态"] = "成功"
            result.at[idx, "失败原因"] = ""
            result.at[idx, "SEO评分"] = int(cached.get("seo_score", seo_score(data, language))) if isinstance(cached, dict) else seo_score(data, language)
            result.at[idx, "标题相似度"] = round(title_similarity(data["title"], source["title"]), 4)
            result.at[idx, "缓存命中"] = "是"
            return True, ""

    analysis_key = hashlib.sha256(json.dumps(source, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    analysis = get_session_dict("product_analysis_cache").get(analysis_key)
    try:
        pipeline = optimize_listing(client, source, language, analysis=analysis, attempts=max_attempts)
        data = pipeline.get("data", {})
        if pipeline.get("analysis"):
            get_session_dict("product_analysis_cache")[analysis_key] = pipeline["analysis"]
        success = bool(pipeline.get("success"))
        reason = str(pipeline.get("reason", ""))
    except Exception as exc:
        data, success, reason, pipeline = {}, False, f"AI错误：{exc}", {}

    if success and data:
        result.at[idx, title_col] = shorten_title_at_word_boundary(clean_text(data["title"]), MAX_TITLE_LEN)
        result.at[idx, short_title_col] = shorten_title_at_word_boundary(clean_text(data.get("short_title", "")), MAX_SHORT_TITLE_LEN)
        for i, c in enumerate(bullet_cols, start=1):
            result.at[idx, c] = clean_text(data[f"bullet{i}"])
        result.at[idx, desc_col] = clean_text(data["description"])
        result.at[idx, "优化状态"] = "成功"
        result.at[idx, "失败原因"] = ""
        result.at[idx, "SEO评分"] = int(pipeline.get("seo_score", seo_score(data, language)))
        result.at[idx, "标题相似度"] = round(title_similarity(data["title"], source["title"]), 4)
        result.at[idx, "缓存命中"] = "否"
        analysis_data = pipeline.get("analysis", {})
        result.at[idx, "产品类型"] = clean_text(analysis_data.get("product_type", ""))
        result.at[idx, "产品类目"] = clean_text(analysis_data.get("category", ""))
        result.at[idx, "识别品牌"] = " | ".join(analysis_data.get("third_party_brands", [])[:5])
        result.at[idx, "识别型号"] = " | ".join(analysis_data.get("compatible_models", [])[:20])
        result.at[idx, "识别材质"] = clean_text(analysis_data.get("material", ""))
        result.at[idx, "识别功能"] = " | ".join(analysis_data.get("functions", [])[:6])
        result.at[idx, "使用场景"] = " | ".join(analysis_data.get("usage_scenarios", [])[:6])
        result.at[idx, "本地关键词"] = " | ".join(pipeline.get("keywords", [])[:6])
        get_session_dict("text_cache")[cache_key] = {
            "data": data.copy(),
            "seo_score": int(pipeline.get("seo_score", 0)),
        }
        return True, ""

    if data:
        if data.get("title"):
            result.at[idx, title_col] = shorten_title_at_word_boundary(clean_text(data["title"]), MAX_TITLE_LEN)
        if data.get("short_title"):
            result.at[idx, short_title_col] = shorten_title_at_word_boundary(clean_text(data["short_title"]), MAX_SHORT_TITLE_LEN)
    result.at[idx, "优化状态"] = "需重新优化"
    result.at[idx, "失败原因"] = reason or "未知质检失败"
    result.at[idx, "SEO评分"] = int(pipeline.get("seo_score", seo_score(data or {}, language))) if isinstance(pipeline, dict) else seo_score(data or {}, language)
    result.at[idx, "标题相似度"] = round(title_similarity((data or {}).get("title", ""), source["title"]), 4) if data else ""
    result.at[idx, "缓存命中"] = "否"
    if isinstance(pipeline, dict):
        analysis_data = pipeline.get("analysis", {})
        result.at[idx, "产品类型"] = clean_text(analysis_data.get("product_type", ""))
        result.at[idx, "产品类目"] = clean_text(analysis_data.get("category", ""))
        result.at[idx, "识别品牌"] = " | ".join(analysis_data.get("third_party_brands", [])[:5])
        result.at[idx, "识别型号"] = " | ".join(analysis_data.get("compatible_models", [])[:20])
        result.at[idx, "识别材质"] = clean_text(analysis_data.get("material", ""))
        result.at[idx, "识别功能"] = " | ".join(analysis_data.get("functions", [])[:6])
        result.at[idx, "使用场景"] = " | ".join(analysis_data.get("usage_scenarios", [])[:6])
        result.at[idx, "本地关键词"] = " | ".join(pipeline.get("keywords", [])[:6])
    return False, reason or "未知质检失败"

def refresh_fail_indices(result: pd.DataFrame) -> list[Any]:
    if "优化状态" not in result.columns:
        return []
    mask = result["__生成行"].astype(str).eq("是") if "__生成行" in result.columns else pd.Series(True, index=result.index)
    return result.index[mask & result["优化状态"].astype(str).ne("成功")].tolist()


def retry_indices(indices: list[Any]) -> None:
    if not indices:
        st.info("当前没有需要重新优化的记录。")
        return
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    result = st.session_state.result_df.copy()
    source_df = st.session_state.source_df
    title_col = st.session_state.title_col
    bullet_cols = st.session_state.bullet_cols
    desc_col = st.session_state.desc_col
    short_title_col = st.session_state.short_title_col
    progress = st.progress(0)
    status = st.empty()
    sku_col = find_col(result, SKU_NAMES)
    for pos, idx in enumerate(indices, start=1):
        status.write(f"重新优化 {pos}/{len(indices)}")
        source_idx = int(result.at[idx, "__源行索引"])
        language = str(result.at[idx, "__目标语言"])
        source_row = source_df.loc[source_idx]
        success, reason = optimize_row_text(client, result, idx, source_row, title_col, bullet_cols, desc_col, short_title_col, language)
        sku = clean_text(result.at[idx, sku_col]) if sku_col else str(idx)
        st.session_state.logs.append(f"重试 {sku}/{language} - {'成功' if success else '失败'} - {reason}")
        progress.progress(pos / len(indices))
    st.session_state.result_df = result
    st.session_state.fail_indices = refresh_fail_indices(result)
    st.success(f"重试完成：剩余失败 {len(st.session_state.fail_indices)} 条")


def retry_image_sources(source_indices: list[int]) -> None:
    if not source_indices:
        st.info("当前没有需要重新处理的图片。")
        return
    result = st.session_state.result_df.copy()
    source_df = st.session_state.source_df
    image_col = st.session_state.image_col
    sku_col = find_col(source_df, SKU_NAMES)
    if not image_col:
        st.error("没有识别到产品图列。")
        return
    progress = st.progress(0)
    remaining = []
    for pos, source_idx in enumerate(source_indices, start=1):
        try:
            source_row = source_df.loc[source_idx]
            images = stable_shuffle_secondary(split_images(source_row.get(image_col, "")), clean_text(source_row.get(sku_col, "")) if sku_col else str(source_idx))
            if not images:
                raise RuntimeError("产品图为空")
            sku = clean_text(source_row.get(sku_col, "")) if sku_col else str(source_idx)
            original = images[0]
            key = hashlib.sha256(original.encode("utf-8")).hexdigest()
            cached = get_session_dict("image_cache").get(key)
            if cached:
                url = cached["url"]
                strategy = cached["strategy"] + "+缓存"
            else:
                processed, strategy = process_main_image(download_image(original), f"{sku}|{original}")
                data = image_bytes(processed)
                url = upload_main_image_to_cloudinary(data, sku or str(source_idx), original)
                get_session_dict("image_cache")[key] = {"url": url, "strategy": strategy}
            images[0] = url
            image_value = IMAGE_SEPARATOR.join(images)
            mask = result["__源行索引"].astype(str).eq(str(source_idx)) & result["__生成行"].astype(str).eq("是")
            result.loc[mask, image_col] = image_value
            result.loc[mask, "首图处理状态"] = "成功"
            result.loc[mask, "优化后首图链接"] = url
            result.loc[mask, "首图失败原因"] = ""
            result.loc[mask, "首图处理方式"] = strategy
        except Exception as exc:
            remaining.append(source_idx)
            mask = result["__源行索引"].astype(str).eq(str(source_idx)) & result["__生成行"].astype(str).eq("是")
            result.loc[mask, "首图处理状态"] = "失败"
            result.loc[mask, "首图失败原因"] = str(exc)
        progress.progress(pos / len(source_indices))
    st.session_state.result_df = result
    st.session_state.image_fail_sources = remaining
    st.success(f"图片重试完成：剩余失败 {len(remaining)} 个产品")

def get_session_dict(key: str) -> dict:
    """Return a session-state dictionary, recreating it after refresh/reboot if needed."""
    value = st.session_state.get(key)
    if not isinstance(value, dict):
        value = {}
        st.session_state[key] = value
    return value


def init_state() -> None:
    defaults = {
        "result_df": None,
        "source_df": None,
        "fail_indices": [],
        "image_files": {},
        "image_fail_sources": [],
        "logs": [],
        "source_name": "",
        "title_col": None,
        "desc_col": None,
        "image_col": None,
        "bullet_cols": [],
        "short_title_col": "短标题",
        "selected_languages": ["英语"],
        "text_cache": {},
        "image_cache": {},
        "product_analysis_cache": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)

api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.error("尚未配置 OPENAI_API_KEY，请在 Streamlit App Settings → Secrets 中配置。")
    st.stop()

selected_languages = st.multiselect(
    "优化语言（可多选）",
    options=list(LANGUAGES.keys()),
    default=["英语"],
    help="每个原产品会按所选顺序生成对应语言的新行，SKU和父SKU保持不变。",
)
optimize_image = st.checkbox("优化首图（测试功能）", value=False)
if optimize_image and not cloudinary_ready():
    st.warning("已勾选首图优化，但尚未配置 Cloudinary Secrets；图片处理会失败并保留原首图链接。")
uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded:
    raw = uploaded.getvalue()
    df = pd.read_excel(io.BytesIO(raw)).fillna("")
    title_col = find_col(df, TITLE_NAMES)
    short_title_col = find_col(df, SHORT_TITLE_NAMES)
    if not short_title_col:
        short_title_col = "短标题"
        # Insert immediately after the main title column to match the export template.
        title_pos = list(df.columns).index(title_col) if title_col in df.columns else len(df.columns) - 1
        df.insert(title_pos + 1, short_title_col, "")
    desc_col = find_col(df, DESC_NAMES)
    image_col = find_col(df, IMAGE_NAMES)
    sku_col = find_col(df, SKU_NAMES)
    language_col = find_col(df, ["语言", "Language"])
    bullet_cols = [find_col(df, names) for names in BULLET_NAMES]

    if not title_col:
        st.error("没有识别到标题列。")
        st.stop()
    if not desc_col:
        desc_col = "简介"
        df[desc_col] = ""
    if not language_col:
        language_col = "语言"
        df[language_col] = ""
    for i, col in enumerate(bullet_cols):
        if not col:
            new_col = f"要点{i + 1}"
            df[new_col] = ""
            bullet_cols[i] = new_col

    st.success(f"已读取 {len(df)} 个原始产品")
    st.dataframe(df.head(8), use_container_width=True)

    if st.button("开始多语言优化", type="primary", disabled=not selected_languages):
        client = OpenAI(api_key=api_key)
        source_df = df.copy()
        generated_rows: list[dict[str, Any]] = []
        image_fail_sources: list[int] = []
        image_files: dict[str, bytes] = {}
        logs: list[str] = []
        total_tasks = len(source_df) * len(selected_languages)
        done_tasks = 0
        progress = st.progress(0)
        status = st.empty()

        # 图片只按原产品处理一次，随后复用到所有语言行。
        image_values: dict[int, dict[str, str]] = {}
        for source_idx, source_row in source_df.iterrows():
            sku = clean_text(source_row.get(sku_col, "")) if sku_col else str(source_idx)
            images = stable_shuffle_secondary(split_images(source_row.get(image_col, "")), sku) if image_col else []
            image_info = {"value": IMAGE_SEPARATOR.join(images), "status": "未启用", "url": "", "reason": "", "strategy": ""}
            if optimize_image and images:
                try:
                    original_main_url = images[0]
                    image_key = hashlib.sha256(original_main_url.encode("utf-8")).hexdigest()
                    cached = get_session_dict("image_cache").get(image_key)
                    if cached:
                        cloudinary_url = cached["url"]
                        strategy = cached["strategy"] + "+缓存"
                        processed_bytes = b""
                    else:
                        processed, strategy = process_main_image(download_image(original_main_url), f"{sku}|{original_main_url}")
                        processed_bytes = image_bytes(processed)
                        cloudinary_url = upload_main_image_to_cloudinary(processed_bytes, sku or str(source_idx), original_main_url)
                        get_session_dict("image_cache")[image_key] = {"url": cloudinary_url, "strategy": strategy}
                    if processed_bytes:
                        filename = f"optimized_main_images/{re.sub(r'[^A-Za-z0-9_-]+', '_', sku or str(source_idx))}.jpg"
                        image_files[filename] = processed_bytes
                    images[0] = cloudinary_url
                    image_info = {"value": IMAGE_SEPARATOR.join(images), "status": "成功", "url": cloudinary_url, "reason": "", "strategy": strategy}
                except Exception as exc:
                    image_fail_sources.append(int(source_idx))
                    image_info = {"value": IMAGE_SEPARATOR.join(images), "status": "失败", "url": "", "reason": str(exc), "strategy": ""}
            image_values[int(source_idx)] = image_info

        # 原表保持在上方；所有优化行按原产品顺序及语言勾选顺序追加到下方。
        for source_idx, source_row in source_df.iterrows():
            for language in selected_languages:
                done_tasks += 1
                status.write(f"正在生成 {done_tasks}/{total_tasks}：第 {source_idx + 1} 个产品 / {language}")
                row_dict = source_row.to_dict()
                row_dict[language_col] = language
                row_dict["__生成行"] = "是"
                row_dict["__源行索引"] = int(source_idx)
                row_dict["__目标语言"] = language
                if image_col:
                    info = image_values[int(source_idx)]
                    row_dict[image_col] = info["value"]
                    row_dict["首图处理状态"] = info["status"]
                    row_dict["优化后首图链接"] = info["url"]
                    row_dict["首图失败原因"] = info["reason"]
                    row_dict["首图处理方式"] = info["strategy"]
                generated_rows.append(row_dict)
                temp = pd.DataFrame(generated_rows)
                idx = temp.index[-1]
                success, reason = optimize_row_text(client, temp, idx, source_row, title_col, bullet_cols, desc_col, short_title_col, language)
                generated_rows[-1] = temp.loc[idx].to_dict()
                sku = clean_text(source_row.get(sku_col, "")) if sku_col else str(source_idx)
                logs.append(f"{done_tasks}/{total_tasks} - {sku}/{language} - {'成功' if success else '失败'} - {reason}")
                progress.progress(done_tasks / total_tasks)

        # 仅保留已经优化生成的多语言结果。原始表格只保存在 source_df 中，
        # 用于失败重试和事实校验，不再写入最终导出的 Excel。
        generated_df = pd.DataFrame(generated_rows).fillna("")
        result = generated_df.reset_index(drop=True)

        st.session_state.source_df = source_df
        st.session_state.result_df = result
        st.session_state.fail_indices = refresh_fail_indices(result)
        st.session_state.image_files = image_files
        st.session_state.image_fail_sources = sorted(set(image_fail_sources))
        st.session_state.logs = logs
        st.session_state.source_name = uploaded.name
        st.session_state.title_col = title_col
        st.session_state.desc_col = desc_col
        st.session_state.short_title_col = short_title_col
        st.session_state.image_col = image_col
        st.session_state.bullet_cols = bullet_cols
        st.session_state.selected_languages = list(selected_languages)
        generated_success = len(generated_df) - len(st.session_state.fail_indices)
        st.success(f"处理完成：生成 {len(generated_df)} 条多语言结果，成功 {generated_success}，失败 {len(st.session_state.fail_indices)}")

if st.session_state.result_df is not None:
    result_df = st.session_state.result_df
    generated_mask = result_df["__生成行"].astype(str).eq("是") if "__生成行" in result_df.columns else pd.Series(True, index=result_df.index)
    generated_count = int(generated_mask.sum())
    st.subheader("处理结果")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("源产品数", len(st.session_state.source_df) if st.session_state.source_df is not None else 0)
    c2.metric("生成语言行", generated_count)
    c3.metric("文案失败", len(st.session_state.fail_indices))
    c4.metric("图片失败产品", len(st.session_state.image_fail_sources))
    st.caption("导出的 Excel 仅包含已生成的优化语言行，原始内容不会重复导出。")

    if st.session_state.fail_indices:
        st.warning("失败项按语言独立保留，可全部重试或选择指定产品/语言重试。")
        sku_col_now = find_col(result_df, SKU_NAMES)
        title_col_now = st.session_state.title_col or find_col(result_df, TITLE_NAMES)
        show_cols = [c for c in [sku_col_now, "语言", title_col_now, st.session_state.short_title_col, "失败原因"] if c and c in result_df.columns]
        failed_view = result_df.loc[st.session_state.fail_indices, show_cols].copy()
        failed_view.insert(0, "行索引", failed_view.index.astype(str))
        st.dataframe(failed_view, use_container_width=True)

        labels = {}
        for idx in st.session_state.fail_indices:
            sku = clean_text(result_df.at[idx, sku_col_now]) if sku_col_now else str(idx)
            language = clean_text(result_df.at[idx, "__目标语言"])
            title = clean_text(result_df.at[idx, title_col_now]) if title_col_now else ""
            labels[f"{idx} | {sku} | {language} | {title[:45]}"] = idx

        selected_labels = st.multiselect("选择需要单独重新优化的失败项", options=list(labels.keys()))
        b1, b2 = st.columns(2)
        with b1:
            if st.button("重新优化全部失败项", type="primary", use_container_width=True):
                retry_indices(list(st.session_state.fail_indices))
                st.rerun()
        with b2:
            if st.button("重新优化选中失败项", use_container_width=True, disabled=not selected_labels):
                retry_indices([labels[x] for x in selected_labels])
                st.rerun()

    if st.session_state.image_fail_sources:
        st.warning(f"有 {len(st.session_state.image_fail_sources)} 个原产品首图处理失败；重试成功后会同步更新该产品的全部语言行。")
        if st.button("重新处理全部失败图片", use_container_width=True):
            retry_image_sources(list(st.session_state.image_fail_sources))
            st.rerun()

    st.download_button(
        "导出已优化 Excel",
        data=output_excel(result_df),
        file_name=re.sub(r"\.xlsx$", "", st.session_state.source_name, flags=re.I) + f"_{VERSION}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if st.session_state.image_files:
        st.download_button(
            "下载已处理首图 ZIP",
            data=build_image_zip(st.session_state.image_files),
            file_name="optimized_main_images.zip",
            mime="application/zip",
        )

    with st.expander("运行日志"):
        st.code("\n".join(st.session_state.logs[-1000:]))
