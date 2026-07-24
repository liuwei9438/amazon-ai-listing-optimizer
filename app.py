from __future__ import annotations

import re

import pandas as pd
import streamlit as st
import json

from analyzer.product_understanding import ProductUnderstandingEngine, UnderstandingError
from analyzer.seo_intent_engine import generate_primary_search
from services.config import get_openai_api_key

from core import export_unchanged, integrity_report, read_workbook

VERSION = "V2.2.3-AI-Product-Understanding"

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")
st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)
st.info(
    "本版本在稳定数据层上新增 AI 商品理解模块。不会生成标题、五点或详情，也不会修改图片。"
    "导出仍与上传文件字节级一致。"
)

uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded is not None:
    try:
        envelope = read_workbook(uploaded.name, uploaded.getvalue())
    except Exception as exc:
        st.error(f"读取失败：{exc}")
        st.stop()

    fields = envelope.fields
    diagnostics = envelope.diagnostics
    st.success(
        f"读取成功：工作表 {envelope.sheet_name}，"
        f"{diagnostics['row_count']} 行，{diagnostics['column_count']} 列。"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("原始列数", diagnostics["column_count"])
    c2.metric("产品记录", diagnostics["record_count"])
    c3.metric("识别字段", diagnostics["matched_field_count"])
    c4.metric("嵌入图片", diagnostics["embedded_image_count"])
    c5.metric("含图片链接记录", diagnostics["records_with_image_urls"])

    st.subheader("字段识别报告")
    report_rows = []
    for label, value in fields.as_dict().items():
        if isinstance(value, tuple):
            display_value = "、".join(value)
        else:
            display_value = value or ""
        report_rows.append(
            {
                "标准字段": label,
                "识别结果": display_value or "未识别",
                "状态": "✓ 已识别" if display_value else "× 未识别",
            }
        )
    st.dataframe(pd.DataFrame(report_rows), hide_index=True, use_container_width=True)

    with st.expander(f"未匹配的原始列（{len(diagnostics['unmatched_columns'])}）"):
        if diagnostics["unmatched_columns"]:
            st.write("、".join(diagnostics["unmatched_columns"]))
        else:
            st.success("所有列均已匹配到标准字段。")

    st.subheader("图片识别诊断")
    if fields.images:
        st.success(
            f"图片链接列：{fields.images}；识别方式：{diagnostics['image_detection_method']}；"
            f"含有效图片链接的记录：{diagnostics['records_with_image_urls']}。"
        )
    elif diagnostics["embedded_image_count"]:
        st.success(
            f"未发现图片链接列，但包含 {diagnostics['embedded_image_count']} 个 Excel 嵌入图片对象。"
            "原样导出会保留这些对象。"
        )
    else:
        st.warning(
            "文件中未检测到图片链接列或 Excel 嵌入图片对象。"
            "这通常表示当前上传文件本身没有保存图片信息。"
        )

    st.subheader("ProductRecord 预览")
    record_preview = []
    for record in envelope.records[:10]:
        record_preview.append(
            {
                "Excel行": record.row_number,
                "SKU": record.sku,
                "父SKU": record.parent_sku,
                "标题": record.title,
                "五点数量": len(record.bullets),
                "图片数量": len(record.image_urls),
                "语言": record.language,
            }
        )
    st.dataframe(pd.DataFrame(record_preview), hide_index=True, use_container_width=True)

    st.subheader("AI Product Understanding")
    st.caption("本阶段只验证商品理解与事实保护，不生成任何上架文案。建议先分析 1–5 个代表产品。")
    saved_api_key = get_openai_api_key()

    if saved_api_key:
        st.success("✅ 已从 Streamlit Secrets 或系统环境变量读取 OpenAI API Key。")
    else:
        st.warning("⚠ 未检测到已保存的 OpenAI API Key，可在下方临时输入。")

    manual_api_key = st.text_input(
        "OpenAI API Key（可留空，默认读取 Secrets）",
        type="password",
        help="优先读取 Streamlit Secrets 或系统环境变量；手动输入仅用于当前会话。",
    )
    api_key = manual_api_key.strip() or saved_api_key

    model = st.text_input("模型", value="gpt-4.1-mini")
    max_products = st.number_input("本次分析产品数", min_value=1, max_value=max(1, min(20, len(envelope.records))), value=min(3, max(1, len(envelope.records))))
    if st.button("开始 AI 商品理解", type="primary"):
        if not api_key.strip():
            st.error("请先填写 OpenAI API Key。")
        else:
            engine = ProductUnderstandingEngine(api_key=api_key, model=model)
            profiles = []
            progress = st.progress(0)
            for i, record in enumerate(envelope.records[:int(max_products)]):
                try:
                    profile = engine.analyze(record)

                    # Task 4.2.2-A: SEO Intent Primary Search
                    seo_intent = generate_primary_search(profile)
                    profile["seo_intent"] = seo_intent

                    profiles.append(profile)
                    with st.expander(f"{record.sku or '第'+str(i+1)+'个产品'}｜{profile['basic_info']['product_type'] or '未识别产品类型'}", expanded=i == 0):
                        a, b, c = st.columns(3)
                        a.write("**产品类型**")
                        a.write(profile["basic_info"]["product_type"] or "Unknown")
                        b.write("**品牌关系**")
                        b.write(profile["brand_info"]["relationship"])
                        c.write("**风险等级**")
                        c.write(profile["compliance"]["risk_level"])
                        st.write("**兼容品牌：**", "、".join(profile["compatibility"]["brands"]) or "Unknown")
                        st.write("**兼容型号：**", "、".join(profile["compatibility"]["models"]) or "Unknown")
                        st.write("**核心功能：**", profile["basic_info"]["main_function"] or "Unknown")
                        st.write("**主要关键词：**", "、".join(profile["seo"]["main_keywords"]) or "Unknown")
                        st.write("**搜索意图：**", profile["seo"]["search_intent"] or "Unknown")

                        if "seo_intent" in profile:
                            st.write("### SEO Intent")
                            primary_search = profile["seo_intent"].get("primary_search", [])
                            st.write("**Primary Search：**", "、".join(primary_search) or "Unknown")

                        st.write("**事实锁：**", profile["fact_lock"])
                        st.json(profile)
                except UnderstandingError as exc:
                    st.error(f"{record.sku or '第'+str(i+1)+'个产品'} 分析失败：{exc}")
                progress.progress((i + 1) / int(max_products))
            if profiles:
                st.download_button(
                    "下载 Product Profile JSON",
                    data=json.dumps(profiles, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name="product_profiles_v2.2.3.json",
                    mime="application/json",
                )

    st.subheader("原始数据预览")
    st.dataframe(envelope.dataframe.head(10), use_container_width=True)

    exported = export_unchanged(envelope)
    integrity = integrity_report(envelope, exported)
    st.subheader("导出完整性")
    if integrity["byte_identical"]:
        st.success(f"验证通过：导出文件与原文件完全一致，大小 {integrity['export_size']:,} 字节。")
    else:
        st.error("完整性验证失败，已停止导出。")
        st.stop()

    safe_stem = re.sub(r"\.xlsx$", "", uploaded.name, flags=re.I)
    st.download_button(
        "导出完整性测试文件",
        data=exported,
        file_name=f"{safe_stem}_{VERSION}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
