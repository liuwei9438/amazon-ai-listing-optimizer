# Amazon AI Listing Optimizer V2.0 Core Test

## 本阶段目标
只重构文案核心，保留 V1.3.2 已验证的图片、Cloudinary、多语言、失败重试和 Excel 导出流程。

## 新增模块
- `core/product_analyzer.py`：每个原产品只分析一次，提取产品类型、类目、品牌、型号、材质、场景、功能、卖点和事实字段。
- `core/language_profiles.py`：九种语言的固定兼容表达和字符限制。
- `core/keyword_library.py`：本地搜索关键词种子库。
- `core/ai_pipeline.py`：产品理解 → 本地关键词 → 文案生成 → 自动质检 → 重试。
- `core/validator.py`：75字符、兼容表达、禁止词、五点、详情和SEO评分检查。
- `core/short_title.py`：短标题兜底生成。
- `core/retry_engine.py`：最多4次自动修复。

## GitHub 更新方法
只在 `v2.0-core-test` 分支上传并覆盖整个部署包内容：

```text
app.py
requirements.txt
core/
prompts/
```

不要修改：
- `main`
- `v1.1-test`
- `v1.2-test`
- `v1.3-test`

## Secrets
继续使用原来的 Streamlit Secrets：

```toml
OPENAI_API_KEY = "..."
CLOUDINARY_CLOUD_NAME = "..."
CLOUDINARY_API_KEY = "..."
CLOUDINARY_API_SECRET = "..."
```

## 第一轮测试建议
先上传 10–20 个产品，并选择 2–3 种语言。重点检查：
1. 产品类型是否正确。
2. 材质、功能、场景是否只提取原文事实。
3. 法语、德语、西班牙语等标题是否更像当地搜索表达。
4. 所有标题是否不超过75字符。
5. 所有品牌是否带对应语言兼容表达。
6. 型号、数量、颜色是否没有改变。
7. 原有图片和导出流程是否正常。

页面导出会新增辅助列：`产品类型`、`本地关键词`，方便测试阶段判断产品理解是否正确。稳定后可以隐藏这两列。
