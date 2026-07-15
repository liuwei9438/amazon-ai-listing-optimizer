# V2.0 Core P1.2 完整替换说明

本版修复 Streamlit 首次打开、刷新或重启后出现：

`AttributeError: st.session_state has no attribute product_analysis_cache`

## 替换方式

在 `v2.0-core-test` 分支中，用本包完整覆盖：

- `app.py`
- `requirements.txt`
- `core/`
- `prompts/`

不要上传 `__pycache__`。

## 修复内容

- 补充 `product_analysis_cache` 初始化
- 所有字典缓存改为防御式读取
- 页面刷新、应用重启或 Session 清空后自动重建缓存
- 同时保护 `text_cache` 和 `image_cache`
- 版本号更新为 `V2.0-core-P1.2-test`

上传提交后，等待 Streamlit 自动重新部署；必要时在 Manage app 中执行 Reboot app。
