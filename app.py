from __future__ import annotations

import hashlib
import json
import pickle
import re
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st
from openai import OpenAI

APP_NAME = "Amazon AI Listing Optimizer V1.1 Test"
MODEL = "gpt-5.6-luna"
TITLE_LIMIT = 75
MAX_RETRIES = 3
CHECKPOINT_DIR = Path("/tmp/amazon_ai_optimizer_tasks")
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

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
SKU_COLUMNS = ["SKU", "sku", "子SKU", "父SKU(必填)", "父SKU"]

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


def ensure_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, Any, Any, Any | None, list[Any], list[str], Any | None]:
    out = df.copy()
    title_col = find_column(out, TITLE_COLUMNS)
    if title_col is None:
        raise ValueError("没有找到标题列。请确认表格包含“标题(必填)”或 Title。")
    desc_col = find_column(out, DESCRIPTION_COLUMNS)
    color_col = find_column(out, COLOR_COLUMNS)
    input_bullet_cols = find_bullet_columns(out)
    if desc_col is None:
        desc_col = "简介"
        out[desc_col] = ""
    for index in range(1, 6):
        name = f"要点{index}"
        if name not in out.columns:
            out[name] = ""
    output_bullet_cols = [f"要点{i}" for i in range(1, 6)]
    for col in ["优化状态", "失败原因", "重试次数"]:
        if col not in out.columns:
            out[col] = "" if col != "重试次数" else 0
    sku_col = find_column(out, SKU_COLUMNS)
    return out, title_col, desc_col, color_col, input_bullet_cols, output_bullet_cols, sku_col


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


def optimize_row(client: OpenAI, country: dict[str, str], source: str) -> tuple[dict[str, Any] | None, list[str], int]:
    retry_note = ""
    last_errors: list[str] = []
    for attempt in range(1, MAX_RETRIES + 1):
        data = call_openai(client, country, source, retry_note)
        data = postprocess_result(data, country)
        errors = qa_check(source, data, country)
        if not errors:
            return data, [], attempt
        last_errors = errors
        retry_note = "Previous output failed quality checks. Correct every issue: " + "; ".join(errors)
        time.sleep(0.4)
    return None, last_errors, MAX_RETRIES


def build_source(row: pd.Series, title_col: Any, desc_col: Any, color_col: Any | None, bullet_cols: list[Any]) -> str:
    source_parts = [
        f"Title: {clean_source_text(row.get(title_col, ''))}",
        f"Variation/Color: {clean_source_text(row.get(color_col, '')) if color_col else ''}",
    ]
    for bullet_col in bullet_cols:
        source_parts.append(f"Bullet: {clean_source_text(row.get(bullet_col, ''))}")
    source_parts.append(f"Description: {clean_source_text(row.get(desc_col, ''))}")
    return "\n".join(part for part in source_parts if part.strip())


def read_excel_safely(uploaded_file: Any) -> tuple[pd.DataFrame, bytes]:
    raw = uploaded_file.getvalue()
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            bad = zf.testzip()
            if bad:
                raise ValueError(f"Excel文件损坏：{bad}")
    except zipfile.BadZipFile as exc:
        raise ValueError("Excel文件损坏或不是有效的 .xlsx 文件，请重新导出或另存为 .xlsx。") from exc
    try:
        return pd.read_excel(BytesIO(raw), engine="openpyxl"), raw
    except Exception as exc:
        raise ValueError(f"无法读取Excel：{exc}") from exc


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="导入产品模板")
    return buffer.getvalue()


def make_task_id(raw: bytes, country_name: str) -> str:
    return hashlib.sha256(raw + country_name.encode("utf-8")).hexdigest()[:24]


def checkpoint_path(task_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", task_id)
    return CHECKPOINT_DIR / f"{safe}.pkl"


def save_checkpoint(task: dict[str, Any]) -> None:
    path = checkpoint_path(task["task_id"])
    tmp = path.with_suffix(".tmp")
    with tmp.open("wb") as f:
        pickle.dump(task, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)


def load_checkpoint(task_id: str) -> dict[str, Any] | None:
    path = checkpoint_path(task_id)
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            task = pickle.load(f)
        if isinstance(task, dict) and task.get("task_id") == task_id:
            return task
    except Exception:
        return None
    return None


def clear_checkpoint(task_id: str) -> None:
    path = checkpoint_path(task_id)
    if path.exists():
        path.unlink()


def task_summary(df: pd.DataFrame) -> tuple[int, int, int]:
    status = df["优化状态"].fillna("").astype(str)
    success = int((status == "成功").sum())
    failed = int((status == "需人工检查").sum())
    pending = int(len(df) - success - failed)
    return success, failed, pending


def failure_indices(df: pd.DataFrame) -> list[Any]:
    return list(df.index[df["优化状态"].fillna("").astype(str) == "需人工检查"])


def display_row_label(df: pd.DataFrame, idx: Any, sku_col: Any | None, title_col: Any) -> str:
    sku = value_text(df.at[idx, sku_col]) if sku_col else ""
    title = value_text(df.at[idx, title_col])
    prefix = sku or f"第{list(df.index).index(idx)+1}行"
    return f"{prefix}｜{title[:55]}"


def run_rows(task: dict[str, Any], indices: Iterable[Any], api_key: str, label: str) -> None:
    indices = list(indices)
    if not indices:
        st.info("没有需要处理的产品。")
        return
    df: pd.DataFrame = task["df"]
    client = OpenAI(api_key=api_key)
    progress = st.progress(0)
    status = st.empty()
    for pos, idx in enumerate(indices, start=1):
        row = df.loc[idx]
        source = build_source(row, task["title_col"], task["desc_col"], task["color_col"], task["input_bullet_cols"])
        status.write(f"{label}：{pos}/{len(indices)}")
        try:
            result, errors, attempts = optimize_row(client, COUNTRIES[task["country_name"]], source)
            previous_retries = int(pd.to_numeric(df.at[idx, "重试次数"], errors="coerce") or 0)
            df.at[idx, "重试次数"] = previous_retries + attempts
            if result:
                df.at[idx, task["title_col"]] = result["title"]
                for i, column in enumerate(task["output_bullet_cols"], start=1):
                    df.at[idx, column] = result[f"bullet{i}"]
                df.at[idx, task["desc_col"]] = result["description"]
                df.at[idx, "优化状态"] = "成功"
                df.at[idx, "失败原因"] = ""
            else:
                df.at[idx, "优化状态"] = "需人工检查"
                df.at[idx, "失败原因"] = "；".join(errors)
        except Exception as exc:
            df.at[idx, "优化状态"] = "需人工检查"
            df.at[idx, "失败原因"] = str(exc)[:500]
        task["df"] = df
        task["updated_at"] = time.time()
        save_checkpoint(task)
        st.session_state["task"] = task
        progress.progress(pos / len(indices))
    status.empty()
    st.rerun()


st.set_page_config(page_title=APP_NAME, page_icon="🛒", layout="wide")
st.title(APP_NAME)
st.caption("测试版不会影响当前正式网址。优化失败项可单独重试，最终统一导出完整表格。")

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = ""
if not api_key:
    st.error("尚未配置 OPENAI_API_KEY。请在 Streamlit 后台的 App settings → Secrets 中填写。")
    st.stop()

# 页面刷新后从 URL 中的 task 参数恢复服务端临时检查点。
query_task_id = value_text(st.query_params.get("task", ""))
if "task" not in st.session_state and query_task_id:
    restored = load_checkpoint(query_task_id)
    if restored:
        st.session_state["task"] = restored
        st.toast("已恢复上次任务进度")

country_name = st.selectbox("目标国家", list(COUNTRIES.keys()), index=0, disabled="task" in st.session_state)
uploaded = st.file_uploader("上传采集插件导出的 Excel", type=["xlsx"], disabled="task" in st.session_state)

if uploaded and "task" not in st.session_state:
    try:
        source_df, raw = read_excel_safely(uploaded)
        out, title_col, desc_col, color_col, input_bullet_cols, output_bullet_cols, sku_col = ensure_columns(source_df)
        task_id = make_task_id(raw, country_name)
        task = {
            "version": "1.1-test",
            "task_id": task_id,
            "country_name": country_name,
            "filename": uploaded.name,
            "df": out,
            "title_col": title_col,
            "desc_col": desc_col,
            "color_col": color_col,
            "input_bullet_cols": input_bullet_cols,
            "output_bullet_cols": output_bullet_cols,
            "sku_col": sku_col,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        previous = load_checkpoint(task_id)
        if previous and len(previous.get("df", [])) == len(out):
            st.session_state["pending_restore"] = previous
        else:
            st.session_state["new_task"] = task
        st.success(f"已读取 {len(out)} 行产品")
    except Exception as exc:
        st.error(str(exc))

if "pending_restore" in st.session_state and "task" not in st.session_state:
    st.warning("检测到同一文件的上次任务进度。")
    c1, c2 = st.columns(2)
    if c1.button("继续上次任务", type="primary", use_container_width=True):
        task = st.session_state.pop("pending_restore")
        st.session_state["task"] = task
        st.query_params["task"] = task["task_id"]
        st.rerun()
    if c2.button("重新开始", use_container_width=True):
        old = st.session_state.pop("pending_restore")
        clear_checkpoint(old["task_id"])
        if "new_task" not in st.session_state:
            # 基于上传文件重新创建，页面下一次重跑会完成。
            st.query_params.clear()
        st.rerun()

if "new_task" in st.session_state and "task" not in st.session_state:
    task = st.session_state.pop("new_task")
    st.session_state["task"] = task
    save_checkpoint(task)
    st.query_params["task"] = task["task_id"]
    st.rerun()

if "task" in st.session_state:
    task = st.session_state["task"]
    df: pd.DataFrame = task["df"]
    success, failed, pending = task_summary(df)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("总产品", len(df))
    m2.metric("成功", success)
    m3.metric("失败/需检查", failed)
    m4.metric("尚未处理", pending)

    action1, action2, action3 = st.columns(3)
    if action1.button("开始/继续优化未处理项", type="primary", use_container_width=True):
        pending_indices = list(df.index[~df["优化状态"].fillna("").astype(str).isin(["成功", "需人工检查"])])
        run_rows(task, pending_indices, api_key, "正在优化")
    if action2.button("重新优化全部失败项", disabled=failed == 0, use_container_width=True):
        run_rows(task, failure_indices(df), api_key, "正在重新优化失败项")
    if action3.button("放弃当前任务并上传新表", use_container_width=True):
        clear_checkpoint(task["task_id"])
        st.session_state.pop("task", None)
        st.query_params.clear()
        st.rerun()

    if failed:
        st.subheader("失败项列表")
        failed_df = df.loc[failure_indices(df)].copy()
        show_cols = [c for c in [task["sku_col"], task["title_col"], "失败原因", "重试次数"] if c is not None and c in failed_df.columns]
        st.dataframe(failed_df[show_cols], use_container_width=True, hide_index=True)

        options = {display_row_label(df, idx, task["sku_col"], task["title_col"]): idx for idx in failure_indices(df)}
        selected_labels = st.multiselect("选择需要单独重新优化的产品", list(options.keys()))
        if st.button("重新优化选中项", disabled=not selected_labels, use_container_width=True):
            run_rows(task, [options[label] for label in selected_labels], api_key, "正在重新优化选中项")

    with st.expander("查看当前结果"):
        preview_cols = [c for c in [task["sku_col"], task["title_col"], "优化状态", "失败原因"] if c is not None and c in df.columns]
        st.dataframe(df[preview_cols], use_container_width=True, hide_index=True)

    st.divider()
    output_name = task["filename"].rsplit(".", 1)[0] + "_AI优化完整结果.xlsx"
    st.download_button(
        "导出当前完整表格",
        data=to_excel_bytes(df),
        file_name=output_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption("每处理一行都会自动保存进度。页面刷新后使用同一网址可恢复；服务器重启时，建议使用已导出的当前完整表格继续处理。")
else:
    st.info("上传 Excel 后即可开始。当前正式版不会受到影响。")
