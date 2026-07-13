# Amazon AI Listing Optimizer 线上部署包

## 文件

- `app.py`：网页程序
- `requirements.txt`：依赖
- `.streamlit/config.toml`：页面配置
- `.gitignore`：防止 API Key 被上传

## 部署步骤

### 1. 创建 GitHub 私有仓库

仓库名称建议：`amazon-ai-listing-optimizer`

将本文件夹中的全部文件上传到仓库根目录。请保持 `.streamlit/config.toml` 的目录结构。

### 2. 登录 Streamlit Community Cloud

使用 GitHub 账号登录 Streamlit Community Cloud，创建新 App。

填写：

- Repository：刚创建的仓库
- Branch：`main`
- Main file path：`app.py`

### 3. 设置 API Key

进入 App settings → Secrets，填写：

```toml
OPENAI_API_KEY = "你的新OpenAI API Key"
```

不要把 API Key 写进 `app.py`，也不要上传 `secrets.toml`。

### 4. 部署

点击 Deploy。部署成功后会生成一个 `streamlit.app` 网址。

### 5. 使用

打开网址：

1. 选择国家
2. 上传采集插件导出的 `.xlsx`
3. 点击“开始优化”
4. 优化完成后点击“下载优化后的 Excel”

## 固定规则

页面不显示规则，但程序会固定执行：

- 标题不超过 75 个字符
- 所有产品默认是非原装兼容产品
- 第三方品牌每次出现都必须使用目标语言的固定兼容词
- 删除 Original、Genuine、Official、OEM、Best Seller、Promotion 等词
- 删除 Manufacturer、ASIN、Item model number、Best Sellers Rank、店铺和物流信息
- 综合标题、五点、详情和颜色理解产品后重新编写
- 最多自动重试 3 次
- 失败行标记“需人工检查”和失败原因
