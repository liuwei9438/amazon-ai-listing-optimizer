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
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from openai import OpenAI

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")

VERSION = "V1.2-P1-test"
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
    # 只做确定性检查：若输出自行使用 Fits/Fit for/Works with，则不通过。
    if re.search(r"\b(fits?|fit for|works with|suitable for|designed for)\b", all_text, flags=re.I):
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


def process_main_image(img: Image.Image) -> Image.Image:
    # P1：不生成新产品、不做背景抠图。透明区域转白；保持比例，1600×1600 白色画布；轻度清晰度增强。
    background = Image.new("RGBA", img.size, "white")
    background.alpha_composite(img)
    img = background.convert("RGB")
    img = ImageOps.contain(img, (1420, 1420), Image.Resampling.LANCZOS)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.03)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))
    canvas = Image.new("RGB", IMAGE_SIZE, "white")
    x = (IMAGE_SIZE[0] - img.width) // 2
    y = (IMAGE_SIZE[1] - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def image_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


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


def init_state() -> None:
    defaults = {
        "result_df": None,
        "fail_indices": [],
        "image_files": {},
        "logs": [],
        "source_name": "",
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
            source = {
                "title": clean_text(row.get(title_col, "")),
                "bullet_points": [clean_text(row.get(c, "")) for c in bullet_cols],
                "description": clean_text(row.get(desc_col, "")),
                "color_or_variant": clean_text(row.get("颜色", "")),
            }
            success, reason, data = False, "", None
            for attempt in range(3):
                try:
                    data = call_ai(client, source, country, reason)
                    success, reason = qa_text(data, source["title"], country)
                    if success:
                        break
                except Exception as exc:
                    reason = f"AI错误：{exc}"
                time.sleep(0.3)

            if success and data:
                result.at[idx, title_col] = clean_text(data["title"])
                for i, c in enumerate(bullet_cols, start=1):
                    result.at[idx, c] = clean_text(data[f"bullet{i}"])
                result.at[idx, desc_col] = clean_text(data["description"])
                result.at[idx, "优化状态"] = "成功"
                result.at[idx, "失败原因"] = ""
            else:
                failures.append(idx)
                result.at[idx, "优化状态"] = "需重新优化"
                result.at[idx, "失败原因"] = reason

            if image_col:
                images = split_images(row.get(image_col, ""))
                sku = clean_text(row.get(sku_col, "")) if sku_col else str(idx)
                images = stable_shuffle_secondary(images, sku)
                result.at[idx, image_col] = IMAGE_SEPARATOR.join(images)
                if optimize_image and images:
                    try:
                        processed = process_main_image(download_image(images[0]))
                        filename = f"optimized_main_images/{re.sub(r'[^A-Za-z0-9_-]+', '_', sku or str(idx))}.jpg"
                        image_files[filename] = image_bytes(processed)
                        result.at[idx, "首图处理状态"] = "已生成，待上传图片存储"
                        result.at[idx, "首图本地文件"] = filename
                    except Exception as exc:
                        result.at[idx, "首图处理状态"] = "失败"
                        result.at[idx, "首图失败原因"] = str(exc)
                elif image_col:
                    result.at[idx, "首图处理状态"] = "未启用"

            logs.append(f"{pos}/{len(result)} - {'成功' if success else '失败'} - {source['title'][:45]}")
            progress.progress(pos / len(result))

        st.session_state.result_df = result
        st.session_state.fail_indices = failures
        st.session_state.image_files = image_files
        st.session_state.logs = logs
        st.session_state.source_name = uploaded.name
        st.success(f"处理完成：成功 {len(result)-len(failures)}，失败 {len(failures)}")

if st.session_state.result_df is not None:
    result_df = st.session_state.result_df
    st.subheader("处理结果")
    c1, c2, c3 = st.columns(3)
    c1.metric("总数", len(result_df))
    c2.metric("成功", int((result_df.get("优化状态", "") == "成功").sum()) if "优化状态" in result_df else 0)
    c3.metric("需重新优化", len(st.session_state.fail_indices))

    if st.session_state.fail_indices:
        st.warning("失败项已保留在完整表格中，可在下一阶段加入单独重试按钮。")
        show_cols = [c for c in [find_col(result_df, SKU_NAMES), find_col(result_df, TITLE_NAMES), "失败原因"] if c]
        st.dataframe(result_df.loc[st.session_state.fail_indices, show_cols], use_container_width=True)

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
        st.info("P1 暂不自动替换首图链接：线上生成的图片需要接入 Cloudinary、R2、S3 或 Supabase Storage 后才能获得永久网址。")

    with st.expander("运行日志"):
        st.code("\n".join(st.session_state.logs[-500:]))
