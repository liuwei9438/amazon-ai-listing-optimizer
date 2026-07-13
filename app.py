from __future__ import annotations

import json
import re
import time
import zipfile
from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st
from openai import OpenAI

APP_NAME = "Amazon AI Listing Optimizer"
MODEL = "gpt-5.6-luna"
TITLE_LIMIT = 75
MAX_RETRIES = 3

COUNTRIES: dict[str, dict[str, str]] = {
    "美国 Amazon.com": {"language": "English (US)", "market": "Amazon United States", "compat": "Compatible with"},
    "英国 Amazon.co.uk": {"language": "English (UK)", "market": "Amazon United Kingdom", "compat": "Compatible with"},
    "加拿大 Amazon.ca": {"language": "English (Canada)", "market": "Amazon Canada", "compat": "Compatible with"},
    "德国 Amazon.de": {"language": "German", "market": "Amazon Germany", "compat": "Kompatibel mit"},
    "法国 Amazon.fr": {"language": "French", "market": "Amazon France", "compat": "Compatible avec"},
    "西班牙 Amazon.es": {"language": "Spanish (Spain)", "market": "Amazon Spain", "compat": "Compatible con"},
    "意大利 Amazon.it": {"language": "Italian", "market": "Amazon Italy", "compat": "Compatibile con"},
    "墨西哥 Amazon.com.mx": {"language": "Spanish (Mexico)", "market": "Amazon Mexico", "compat": "Compatible con"},
}

TITLE_COLUMNS = ["标题(必填)", "标题", "Product Title", "Title", "title", "产品标题"]
DESCRIPTION_COLUMNS = ["简介", "详情", "描述", "Product Description", "Description", "description"]
COLOR_COLUMNS = ["颜色", "Color", "Variation", "variation"]

PROHIBITED_TERMS = [
    "original", "genuine", "official", "oem", "authentic", "authorized", "brand authorized",
    "best seller", "bestseller", "#1", "no.1", "top rated", "hot sale", "promotion",
    "discount", "free shipping", "premium quality", "guaranteed", "lifetime warranty",
    "100% satisfaction", "best quality", "sale price",
]

NOISE_TERMS = [
    "manufacturer", "asin", "item model number", "best sellers rank", "customer reviews",
    "date first available", "seller", "welcome to our store", "our store", "our company",
    "customer service", "shipping", "delivery", "returns", "brand story",
    "thank you for choosing", "if you have any questions",
]

ALT_COMPAT_PHRASES = [
    "fits", "fit for", "works with", "suitable for", "designed for use with",
    "intended for use with", "replacement for",
]

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "bullet1": {"type": "string"},
        "bullet2": {"type": "string"},
        "bullet3": {"type": "string"},
        "bullet4": {"type": "string"},
        "bullet5": {"type": "string"},
        "description": {"type": "string"},
        "brand_terms": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description", "brand_terms"],
    "additionalProperties": False,
}


def value_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_source_text(value: Any) -> str:
    text = value_text(value).replace("|", "\n")
    kept: list[str] = []
    for line in re.split(r"[\r\n]+", text):
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        low = line.lower()
        if any(term in low for term in NOISE_TERMS):
            continue
        for term in PROHIBITED_TERMS:
            line = re.sub(re.escape(term), "", line, flags=re.I)
        line = re.sub(r"\s+", " ", line).strip(" -;,，。")
        if line:
            kept.append(line)
    return "\n".join(kept)[:8000]


def find_column(df: pd.DataFrame, candidates: list[str]) -> Any | None:
    exact = {str(col).strip().lower(): col for col in df.columns}
    for name in candidates:
        if name.lower() in exact:
            return exact[name.lower()]
    for col in df.columns:
        col_text = str(col).strip().lower()
        for name in candidates:
            if name.lower() in col_text:
                return col
    return None


def find_bullet_columns(df: pd.DataFrame) -> list[Any]:
    found: list[Any] = []
    for index in range(1, 6):
        col = find_column(df, [f"要点{index}", f"Bullet{index}", f"Bullet {index}", f"bullet{index}"])
        if col is not None and col not in found:
            found.append(col)
    return found[:5]


def extract_facts(text: str) -> dict[str, set[str]]:
    return {
        "quantity": set(re.findall(r"\b\d+\s?(?:pcs?|pieces?|pack|packs|set|sets|个|件|套)\b", text, flags=re.I)),
        "models": set(re.findall(r"\b[A-Z]{1,6}[- ]?\d[A-Z0-9\-]{1,12}\b", text, flags=re.I)),
        "sizes": set(re.findall(r"\b\d+(?:\.\d+)?\s?(?:mm|cm|m|inch|inches|in|ft|v|w|a|mah|ml|l|oz|lb|lbs)\b", text, flags=re.I)),
        "colors": set(re.findall(r"\b(?:black|white|red|blue|green|yellow|grey|gray|silver|gold|brown|orange|pink|purple)\b", text, flags=re.I)),
    }


def normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", value_text(text)).strip()


def field_has_compatible_brand(field: str, brand: str, compat_phrase: str) -> bool:
    if not brand or not re.search(rf"(?<!\w){re.escape(brand)}(?!\w)", field, flags=re.I):
        return True
    for match in re.finditer(rf"(?<!\w){re.escape(brand)}(?!\w)", field, flags=re.I):
        prefix = field[max(0, match.start() - 80):match.start()]
        if not re.search(rf"{re.escape(compat_phrase)}\s*$", prefix, flags=re.I):
            return False
    return True


def postprocess_result(data: dict[str, Any], country: dict[str, str]) -> dict[str, Any]:
    result = dict(data)
    keys = ["title", "bullet1", "bullet2", "bullet3", "bullet4", "bullet5", "description"]
    compat = country["compat"]
    brands = [normalize_phrase(x) for x in data.get("brand_terms", []) if normalize_phrase(x)]

    for key in keys:
        text = normalize_phrase(data.get(key, ""))
        for term in PROHIBITED_TERMS:
            text = re.sub(re.escape(term), "", text, flags=re.I)
        text = re.sub(r"\s+", " ", text).strip(" -;,，。")
        for brand in sorted(brands, key=len, reverse=True):
            alt = r"(?:fits|fit\s+for|works\s+with|suitable\s+for|designed\s+for(?:\s+use\s+with)?|intended\s+for\s+use\s+with|replacement\s+for|for)"
            text = re.sub(
                rf"\b{alt}\s+({re.escape(brand)})\b",
                lambda match: f"{compat} {match.group(1)}",
                text,
                flags=re.I,
            )
        result[key] = re.sub(r"\s+", " ", text).strip()
    result["brand_terms"] = brands
    return result


def qa_check(source: str, result: dict[str, Any], country: dict[str, str]) -> list[str]:
    errors: list[str] = []
    fields = {
        "标题": value_text(result.get("title")),
        "要点1": value_text(result.get("bullet1")),
        "要点2": value_text(result.get("bullet2")),
        "要点3": value_text(result.get("bullet3")),
        "要点4": value_text(result.get("bullet4")),
        "要点5": value_text(result.get("bullet5")),
        "详情": value_text(result.get("description")),
    }
    combined = " ".join(fields.values())
    low = combined.lower()

    if not fields["标题"]:
        errors.append("标题为空")
    if len(fields["标题"]) > TITLE_LIMIT:
        errors.append(f"标题超过{TITLE_LIMIT}个字符（当前{len(fields['标题'])}个）")
    if any(not fields[f"要点{i}"] for i in range(1, 6)):
        errors.append("五点描述不足5条")
    if not fields["详情"]:
        errors.append("详情为空")

    for term in PROHIBITED_TERMS:
        if term in low:
            errors.append(f"含禁止词：{term}")
    for term in NOISE_TERMS:
        if term in low:
            errors.append(f"含无关信息：{term}")

    brands = [value_text(x) for x in result.get("brand_terms", []) if value_text(x)]
    compat = country["compat"]
    for name, field in fields.items():
        for brand in brands:
            if not field_has_compatible_brand(field, brand, compat):
                errors.append(f"{name}中的品牌 {brand} 未使用固定兼容词 {compat}")

    for phrase in ALT_COMPAT_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", combined, flags=re.I):
            errors.append(f"出现非统一兼容表达：{phrase}")

    source_facts = extract_facts(source)
    output_facts = extract_facts(combined)
    for fact_type in ("quantity", "colors"):
        if source_facts[fact_type] and output_facts[fact_type]:
            src = {x.lower() for x in source_facts[fact_type]}
            out = {x.lower() for x in output_facts[fact_type]}
            if not src.intersection(out):
                errors.append("数量或颜色事实可能被修改")
                break

    return list(dict.fromkeys(errors))


def call_openai(client: OpenAI, country: dict[str, str], source: str, retry_note: str = "") -> dict[str, Any]:
    instructions = f"""
You are an Amazon listing SEO and compliance editor for {country['market']}.
Write in {country['language']}.

Hard rules:
1. Treat every product as a non-original, non-official, non-OEM compatible product.
2. Every occurrence of every third-party brand must be immediately introduced by the exact phrase: {country['compat']}.
3. Never use Fits, Fit for, Works with, Suitable for, Designed for use with, Intended for use with, Replacement for, Original, Genuine, Official, OEM, Authentic, Authorized.
4. Rewrite the title, five bullet points, and description using all source information as one product. Do not merely translate sentence by sentence.
5. Preserve facts: quantity, color, size, material, voltage, power, compatible models, package contents, and product purpose. Never invent facts.
6. Remove seller/store/company information, Manufacturer, ASIN, Item model number, Best Sellers Rank, shipping, delivery, returns, warranty, promotion, bestseller and unrelated content.
7. The title must be 75 characters or fewer, including spaces.
8. Produce exactly five useful bullet points and one clean description.
9. Identify all third-party brand names in brand_terms. Do not include generic product words or model numbers in brand_terms.
{retry_note}
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=source,
        text={
            "format": {
                "type": "json_schema",
                "name": "amazon_listing",
                "schema": OUTPUT_SCHEMA,
                "strict": True,
            },
            "verbosity": "low",
        },
    )
    return json.loads(response.output_text)


def optimize_row(client: OpenAI, country: dict[str, str], source: str) -> tuple[dict[str, Any] | None, list[str]]:
    retry_note = ""
    last_errors: list[str] = []
    for _ in range(MAX_RETRIES):
        data = call_openai(client, country, source, retry_note)
        data = postprocess_result(data, country)
        errors = qa_check(source, data, country)
        if not errors:
            return data, []
        last_errors = errors
        retry_note = "Previous output failed quality checks. Correct every issue: " + "; ".join(errors)
        time.sleep(0.4)
    return None, last_errors


def read_excel_safely(uploaded_file: Any) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            bad = zf.testzip()
            if bad:
                raise ValueError(f"Excel文件损坏：{bad}")
    except zipfile.BadZipFile as exc:
        raise ValueError("Excel文件损坏或不是有效的 .xlsx 文件，请重新导出或另存为 .xlsx。") from exc
    try:
        return pd.read_excel(BytesIO(raw), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"无法读取Excel：{exc}") from exc


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="导入产品模板")
    return buffer.getvalue()


st.set_page_config(page_title=APP_NAME, page_icon="🛒", layout="centered")
st.title(APP_NAME)
st.caption("选择国家，上传采集表格，开始优化。")

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = ""

if not api_key:
    st.error("尚未配置 OPENAI_API_KEY。请在 Streamlit 后台的 App settings → Secrets 中填写。")
    st.code('OPENAI_API_KEY = "你的新APIKey"', language="toml")
    st.stop()

country_name = st.selectbox("目标国家", list(COUNTRIES.keys()), index=0)
uploaded = st.file_uploader("上传采集插件导出的 Excel", type=["xlsx"])

if uploaded:
    try:
        df = read_excel_safely(uploaded)
        st.success(f"已读取 {len(df)} 行产品")
        with st.expander("查看前5行"):
            st.dataframe(df.head(5), use_container_width=True)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if st.button("开始优化", type="primary", use_container_width=True):
        title_col = find_column(df, TITLE_COLUMNS)
        desc_col = find_column(df, DESCRIPTION_COLUMNS)
        color_col = find_column(df, COLOR_COLUMNS)
        bullet_cols = find_bullet_columns(df)

        if title_col is None:
            st.error("没有找到标题列。请确认表格包含“标题(必填)”或 Title。")
            st.stop()

        out = df.copy()
        if desc_col is None:
            desc_col = "简介"
            out[desc_col] = ""
        for index in range(1, 6):
            name = f"要点{index}"
            if name not in out.columns:
                out[name] = ""
        output_bullet_cols = [f"要点{i}" for i in range(1, 6)]
        if "优化状态" not in out.columns:
            out["优化状态"] = ""
        if "失败原因" not in out.columns:
            out["失败原因"] = ""

        client = OpenAI(api_key=api_key)
        progress = st.progress(0)
        status = st.empty()
        success_count = 0
        fail_count = 0

        for pos, (idx, row) in enumerate(out.iterrows(), start=1):
            source_parts = [
                f"Title: {clean_source_text(row.get(title_col, ''))}",
                f"Variation/Color: {clean_source_text(row.get(color_col, '')) if color_col else ''}",
            ]
            for bullet_col in bullet_cols:
                source_parts.append(f"Bullet: {clean_source_text(row.get(bullet_col, ''))}")
            source_parts.append(f"Description: {clean_source_text(row.get(desc_col, ''))}")
            source = "\n".join(part for part in source_parts if part.strip())

            status.write(f"正在优化：{pos}/{len(out)}")
            try:
                result, errors = optimize_row(client, COUNTRIES[country_name], source)
                if result:
                    out.at[idx, title_col] = result["title"]
                    for i, column in enumerate(output_bullet_cols, start=1):
                        out.at[idx, column] = result[f"bullet{i}"]
                    out.at[idx, desc_col] = result["description"]
                    out.at[idx, "优化状态"] = "成功"
                    out.at[idx, "失败原因"] = ""
                    success_count += 1
                else:
                    out.at[idx, "优化状态"] = "需人工检查"
                    out.at[idx, "失败原因"] = "；".join(errors)
                    fail_count += 1
            except Exception as exc:
                out.at[idx, "优化状态"] = "需人工检查"
                out.at[idx, "失败原因"] = str(exc)[:500]
                fail_count += 1
            progress.progress(pos / len(out))

        st.session_state["optimized_bytes"] = to_excel_bytes(out)
        st.session_state["optimized_filename"] = uploaded.name.rsplit(".", 1)[0] + "_AI优化后.xlsx"
        st.session_state["summary"] = (success_count, fail_count)
        status.empty()

if "optimized_bytes" in st.session_state:
    success_count, fail_count = st.session_state.get("summary", (0, 0))
    st.success(f"优化完成：成功 {success_count} 行，需人工检查 {fail_count} 行")
    st.download_button(
        "下载优化后的 Excel",
        data=st.session_state["optimized_bytes"],
        file_name=st.session_state["optimized_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
