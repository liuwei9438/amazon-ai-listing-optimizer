# Amazon AI Listing Optimizer V2.0 Clean Stable

这是重新整理的完整部署版，不需要在旧代码上继续修改。

## 完整上传内容

将本压缩包解压后，把以下全部内容上传到一个新分支：

- app.py
- requirements.txt
- core/
- storage/
- prompts/
- .gitignore

不要上传 `__pycache__`。

## Streamlit 新部署设置

- Repository：你的 GitHub 仓库
- Branch：建议新建 `v2.0-clean-stable`
- Main file path：`app.py`
- Python version：在 Advanced settings 中选择 **3.12**

## Secrets

```toml
OPENAI_API_KEY = "你的 OpenAI API Key"

CLOUDINARY_CLOUD_NAME = "你的 Cloudinary Cloud Name"
CLOUDINARY_API_KEY = "你的 Cloudinary API Key"
CLOUDINARY_API_SECRET = "你的 Cloudinary API Secret"
```

未使用首图优化时，Cloudinary 三项可以暂时不填。

## 本版重点修复

1. 恢复并保留完整 validator 接口。
2. 自动把各语言混用或拼错的兼容表达修正为目标语言固定表达。
3. 标题、短标题、五点和详情中的裸品牌会在本地自动补兼容词，不调用 AI。
4. 失败原因会指出具体字段。
5. 删除重复的 `shorten_at_word_boundary`，避免启动错误。
6. 主标题不超过 75 字符，短标题不超过 125 字符。
7. 保留多语言、失败池、图片优化、Cloudinary、检查点恢复和导出功能。

## 部署建议

不要覆盖当前不能启动的分支。新建分支并重新创建一个 Streamlit 测试应用。
测试正常后，再决定是否替换正式版本。
