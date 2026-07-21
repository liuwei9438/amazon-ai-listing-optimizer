from __future__ import annotations

import re

import streamlit as st

from core import export_unchanged, integrity_report, read_workbook

VERSION = "V2.2.1-Data-Pipeline-Stable"

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")
st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)

st.info(
    "本版本只验证 Excel 数据底座，不运行 AI、不优化图片。"
    "导出文件与上传文件保持字节级一致，确保字段、格式和嵌入图片不会丢失。"
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("原始列数", diagnostics["column_count"])
    c2.metric("原始行数", diagnostics["row_count"])
    c3.metric("嵌入图片", diagnostics["embedded_image_count"])
    c4.metric("工作表数量", diagnostics["sheet_count"])

    st.subheader("字段识别诊断")
    detected = {
        "SKU": fields.sku or "未识别",
        "标题": fields.title or "未识别",
        "短标题": fields.short_title or "未识别",
        "五点": "、".join(fields.bullets) if fields.bullets else "未识别",
        "详情": fields.description or "未识别",
        "图片": fields.images or "未识别（可能是嵌入图片对象）",
        "语言": fields.language or "未识别",
    }
    st.json(detected)

    if fields.images:
        st.success(f"识别到图片链接列：{fields.images}")
    elif diagnostics["embedded_image_count"]:
        st.success(
            f"未发现图片链接列，但工作表包含 {diagnostics['embedded_image_count']} 个嵌入图片对象；"
            "本版本原样导出，因此这些图片会保留。"
        )
    else:
        st.warning("没有识别到图片链接列或嵌入图片。请确认原文件是否实际包含图片信息。")

    st.subheader("原始数据预览")
    st.dataframe(envelope.dataframe.head(10), use_container_width=True)

    exported = export_unchanged(envelope)
    report = integrity_report(envelope, exported)

    st.subheader("导出完整性")
    if report["byte_identical"]:
        st.success(
            f"验证通过：导出文件与原文件完全一致，大小 {report['export_size']:,} 字节。"
        )
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
