import hashlib
import io
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

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")

VERSION = "V1.2-P1.2-test"
MAX_TITLE_LEN = 75
IMAGE_SIZE = (1600, 1600)
IMAGE_SEPARATOR = " | "

COUNTRIES = {
    "美国": {"language": "English (US)", "compat": "Compatible with"},
    "英国": {"language": "English (UK)", "compat": "Compatible with"},
    "加拿大": {"language": "English (Canada)", "compat": "Compatible with"},
    "德国": {"language": "German", "compat": "Kompatibel mit"},
    "法国": {"language": "French", "compat": "Compatible avec"},
    "西班牙": {"language": "Spanish (Spain)", "compat": "Compatible con"},
    "意大利": {"language": "Italian", "compat": "Compatibile con"},
    "墨西哥": {"language": "Spanish (Mexico)", "compat": "Compatible con"},
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


def build_prompt(source: dict[str, Any], country: str, retry_reason: str = "") -> str:
    cfg = COUNTRIES[country]
    extra = f"\nPrevious output failed QA because: {retry_reason}\n" if retry_reason else ""
    return f"""
You are an Amazon listing SEO and compliance writer for {country}.
Write in {cfg['language']}.
Return JSON only with keys: title, bullet1, bullet2, bullet3, bullet4, bullet5, description.

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
{extra}
SOURCE DATA:
{json.dumps(source, ensure_ascii=False)}
""".strip()


def call_ai(client: OpenAI, source: dict[str, Any], country: str, retry_reason: str = "") -> dict[str, str]:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=build_prompt(source, country, retry_reason),
    )
    return parse_json(response.output_text)


def normalize_compatibility_text(text: str, country: str) -> str:
    """Normalize common AI compatibility variants before QA.

    This avoids false failures such as `Compatible Withr LG` while still
    enforcing one fixed compatibility phrase in exported copy.
    """
    if not text:
        return ""
    compat = COUNTRIES[country]["compat"]
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


def normalize_ai_output(data: dict[str, Any], country: str) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key in ["title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description"]:
        normalized[key] = normalize_compatibility_text(str(data.get(key, "") or ""), country)
    return normalized


def shorten_title_at_word_boundary(title: str, max_len: int = MAX_TITLE_LEN) -> str:
    title = re.sub(r"\s+", " ", title).strip(" ,;-–—")
    if len(title) <= max_len:
        return title
    cut = title[: max_len + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;-–—")


def qa_text(data: dict[str, str], original_title: str, country: str) -> tuple[bool, str]:
    cfg = COUNTRIES[country]
    title = clean_text(data.get("title", ""))
    bullets = [clean_text(data.get(f"bullet{i}", "")) for i in range(1, 6)]
    desc = clean_text(data.get("description", ""))
    if not title:
        return False, "标题为空"
    if title.strip().lower() == clean_text(original_title).strip().lower():
        return False, "标题未重新编写"
    if len(title) > MAX_TITLE_LEN:
        return False, f"标题超过 {MAX_TITLE_LEN} 字符"
    if any(not b for b in bullets):
        return False, "五点描述不足5条"
    if not desc:
        return False, "详情为空"
    all_text = " ".join([title, *bullets, desc]).lower()
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
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
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
    title_col: str,
    bullet_cols: list[str],
    desc_col: str,
    country: str,
    max_attempts: int = 4,
) -> tuple[bool, str]:
    row = result.loc[idx]
    source = {
        "title": clean_text(row.get(title_col, "")),
        "bullet_points": [clean_text(row.get(c, "")) for c in bullet_cols],
        "description": clean_text(row.get(desc_col, "")),
        "color_or_variant": clean_text(row.get("颜色", "")),
    }
    reason = ""
    data: dict[str, str] | None = None
    success = False
    for attempt in range(max_attempts):
        try:
            raw_data = call_ai(client, source, country, reason)
            data = normalize_ai_output(raw_data, country)
            # Last-attempt deterministic safety for an otherwise valid but slightly long title.
            if attempt == max_attempts - 1 and len(data.get("title", "")) > MAX_TITLE_LEN:
                data["title"] = shorten_title_at_word_boundary(data["title"])
            success, reason = qa_text(data, source["title"], country)
            if success:
                break
        except Exception as exc:
            reason = f"AI错误：{exc}"
        time.sleep(0.35)

    if success and data:
        result.at[idx, title_col] = clean_text(data["title"])
        for i, c in enumerate(bullet_cols, start=1):
            result.at[idx, c] = clean_text(data[f"bullet{i}"])
        result.at[idx, desc_col] = clean_text(data["description"])
        result.at[idx, "优化状态"] = "成功"
        result.at[idx, "失败原因"] = ""
        return True, ""

    result.at[idx, "优化状态"] = "需重新优化"
    result.at[idx, "失败原因"] = reason or "未知质检失败"
    return False, reason or "未知质检失败"


def refresh_fail_indices(result: pd.DataFrame) -> list[Any]:
    if "优化状态" not in result.columns:
        return []
    return result.index[result["优化状态"].astype(str) != "成功"].tolist()


def retry_indices(
    indices: list[Any],
    country: str,
    title_col: str,
    bullet_cols: list[str],
    desc_col: str,
) -> None:
    if not indices:
        st.info("当前没有需要重新优化的记录。")
        return
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    result = st.session_state.result_df.copy()
    progress = st.progress(0)
    status = st.empty()
    for pos, idx in enumerate(indices, start=1):
        status.write(f"重新优化 {pos}/{len(indices)}")
        success, reason = optimize_row_text(client, result, idx, title_col, bullet_cols, desc_col, country)
        sku_col = find_col(result, SKU_NAMES)
        sku = clean_text(result.at[idx, sku_col]) if sku_col else str(idx)
        st.session_state.logs.append(f"重试 {sku} - {'成功' if success else '失败'} - {reason}")
        progress.progress(pos / len(indices))
    st.session_state.result_df = result
    st.session_state.fail_indices = refresh_fail_indices(result)
    st.success(f"重试完成：剩余失败 {len(st.session_state.fail_indices)} 条")


def init_state() -> None:
    defaults = {
        "result_df": None,
        "fail_indices": [],
        "image_files": {},
        "logs": [],
        "source_name": "",
        "title_col": None,
        "desc_col": None,
        "bullet_cols": [],
        "country": "美国",
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

country = st.selectbox("目标国家", list(COUNTRIES.keys()), index=0)
optimize_image = st.checkbox("优化首图（测试功能）", value=False)
if optimize_image and not cloudinary_ready():
    st.warning("已勾选首图优化，但尚未配置 Cloudinary Secrets；图片处理会失败并保留原首图链接。")
uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded:
    raw = uploaded.getvalue()
    df = pd.read_excel(io.BytesIO(raw)).fillna("")
    title_col = find_col(df, TITLE_NAMES)
    desc_col = find_col(df, DESC_NAMES)
    image_col = find_col(df, IMAGE_NAMES)
    sku_col = find_col(df, SKU_NAMES)
    bullet_cols = [find_col(df, names) for names in BULLET_NAMES]

    if not title_col:
        st.error("没有识别到标题列。")
        st.stop()
    if not desc_col:
        desc_col = "简介"
        df[desc_col] = ""
    for i, col in enumerate(bullet_cols):
        if not col:
            new_col = f"要点{i + 1}"
            df[new_col] = ""
            bullet_cols[i] = new_col

    st.success(f"已读取 {len(df)} 行")
    st.dataframe(df.head(8), use_container_width=True)

    if st.button("开始优化", type="primary"):
        client = OpenAI(api_key=api_key)
        result = df.copy()
        failures: list[int] = []
        image_files: dict[str, bytes] = {}
        logs: list[str] = []
        progress = st.progress(0)
        status = st.empty()

        for pos, (idx, row) in enumerate(result.iterrows(), start=1):
            status.write(f"正在处理 {pos}/{len(result)}")
            original_title = clean_text(row.get(title_col, ""))
            success, reason = optimize_row_text(
                client, result, idx, title_col, bullet_cols, desc_col, country
            )
            if not success:
                failures.append(idx)

            if image_col:
                images = split_images(row.get(image_col, ""))
                sku = clean_text(row.get(sku_col, "")) if sku_col else str(idx)
                images = stable_shuffle_secondary(images, sku)
                if optimize_image and images:
                    try:
                        original_main_url = images[0]
                        processed, image_strategy = process_main_image(
                            download_image(original_main_url), f"{sku}|{original_main_url}"
                        )
                        processed_bytes = image_bytes(processed)
                        filename = f"optimized_main_images/{re.sub(r'[^A-Za-z0-9_-]+', '_', sku or str(idx))}.jpg"
                        image_files[filename] = processed_bytes
                        cloudinary_url = upload_main_image_to_cloudinary(
                            processed_bytes, sku or str(idx), original_main_url
                        )
                        # Only replace the first image. Secondary image links remain unchanged
                        # apart from de-duplication and deterministic reordering.
                        images[0] = cloudinary_url
                        result.at[idx, "首图处理状态"] = "成功"
                        result.at[idx, "优化后首图链接"] = cloudinary_url
                        result.at[idx, "首图失败原因"] = ""
                        result.at[idx, "首图处理方式"] = image_strategy
                    except Exception as exc:
                        # Keep the original first image URL if processing/upload fails.
                        result.at[idx, "首图处理状态"] = "失败"
                        result.at[idx, "首图失败原因"] = str(exc)
                        result.at[idx, "首图处理方式"] = ""
                elif image_col:
                    result.at[idx, "首图处理状态"] = "未启用"
                result.at[idx, image_col] = IMAGE_SEPARATOR.join(images)

            logs.append(f"{pos}/{len(result)} - {'成功' if success else '失败'} - {original_title[:45]}")
            progress.progress(pos / len(result))

        st.session_state.result_df = result
        st.session_state.fail_indices = failures
        st.session_state.image_files = image_files
        st.session_state.logs = logs
        st.session_state.source_name = uploaded.name
        st.session_state.title_col = title_col
        st.session_state.desc_col = desc_col
        st.session_state.bullet_cols = bullet_cols
        st.session_state.country = country
        st.success(f"处理完成：成功 {len(result)-len(failures)}，失败 {len(failures)}")

if st.session_state.result_df is not None:
    result_df = st.session_state.result_df
    st.subheader("处理结果")
    c1, c2, c3 = st.columns(3)
    c1.metric("总数", len(result_df))
    c2.metric("成功", int((result_df.get("优化状态", "") == "成功").sum()) if "优化状态" in result_df else 0)
    c3.metric("需重新优化", len(st.session_state.fail_indices))

    if st.session_state.fail_indices:
        st.warning("失败项已保留在完整表格中，可以全部重试或选择指定记录重试。")
        sku_col_now = find_col(result_df, SKU_NAMES)
        title_col_now = st.session_state.title_col or find_col(result_df, TITLE_NAMES)
        show_cols = [c for c in [sku_col_now, title_col_now, "失败原因"] if c]
        failed_view = result_df.loc[st.session_state.fail_indices, show_cols].copy()
        failed_view.insert(0, "行索引", failed_view.index.astype(str))
        st.dataframe(failed_view, use_container_width=True)

        labels = {}
        for idx in st.session_state.fail_indices:
            sku = clean_text(result_df.at[idx, sku_col_now]) if sku_col_now else str(idx)
            title = clean_text(result_df.at[idx, title_col_now]) if title_col_now else ""
            labels[f"{idx} | {sku} | {title[:55]}"] = idx

        selected_labels = st.multiselect(
            "选择需要单独重新优化的失败项",
            options=list(labels.keys()),
            placeholder="可选择一条或多条",
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button("重新优化全部失败项", type="primary", use_container_width=True):
                retry_indices(
                    list(st.session_state.fail_indices),
                    st.session_state.country,
                    st.session_state.title_col,
                    st.session_state.bullet_cols,
                    st.session_state.desc_col,
                )
                st.rerun()
        with b2:
            if st.button("重新优化选中失败项", use_container_width=True, disabled=not selected_labels):
                retry_indices(
                    [labels[x] for x in selected_labels],
                    st.session_state.country,
                    st.session_state.title_col,
                    st.session_state.bullet_cols,
                    st.session_state.desc_col,
                )
                st.rerun()

    st.download_button(
        "导出完整 Excel",
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
        st.success("已上传 Cloudinary 的首图会以完整 HTTPS 链接替换 Excel 产品图字段中的第一张图片。")

    with st.expander("运行日志"):
        st.code("\n".join(st.session_state.logs[-500:]))
