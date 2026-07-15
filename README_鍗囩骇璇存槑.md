# V2.0 Core P1.3 失败池收敛 + Item Highlights

## 必须替换
- `app.py`
- `core/ai_pipeline.py`
- `core/validator.py`
- `core/short_title.py`
- `core/language_profiles.py`

## 不需要替换
- `requirements.txt`
- `prompts/`
- 其他 `core/` 文件

## 本次更新
1. 主标题继续硬限制 75 个字符（包含空格和标点）。
2. “短标题”改为 Amazon Item Highlights 逻辑，最大 125 字符。
3. Item Highlights 从整条产品信息提取：数量、材质、尺寸、使用场景、功能、事实卖点和搜索词。
4. 失败池逐轮收敛：每次只处理当前失败项，成功项立即移出失败池。
5. 手动重试时每项只调用一次 AI，速度明显提升。
6. 每轮使用不同策略：本地修复 → 失败字段修复 → 严格压缩 → 安全兜底。
7. 第 2 轮以后仍失败时，使用已验证产品事实生成安全兜底结果，避免反复卡住。
8. 新增“重试轮次”列，便于查看每条记录处理进度。

## 部署
把上述文件上传到 `v2.0-core-test` 分支并提交。Streamlit 自动更新后，必要时执行 `Manage app → Reboot app`。
