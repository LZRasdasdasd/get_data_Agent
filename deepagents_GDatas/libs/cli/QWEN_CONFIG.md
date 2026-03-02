# 千问模型配置指南

本指南说明如何在 DeepAgents CLI 中配置千问模型（Qwen）。

## 快速配置

### 方法一：使用 OpenAI 兼容接口（推荐）

千问模型提供 OpenAI 兼容接口，可以直接通过配置 `OPENAI_API_KEY` 使用。

#### 1. 配置环境变量

编辑 `libs/cli/.env` 文件：

```bash
# 设置千问模型的 API Key（从阿里云 DashScope 获取）
OPENAI_API_KEY=sk-你的千问API密钥

# 可选：配置 LangSmith 用于追踪
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_langsmith_api_key
```

#### 2. 运行 CLI 并指定模型

```bash
# 使用千问模型运行
cd libs/cli
uv run deepagents --model openai:qwen-turbo

# 或者使用其他千问模型
uv run deepagents --model openai:qwen-plus
uv run deepagents --model openai:qwen-max
```

#### 3. 通过配置文件自定义 Base URL

如果需要指定千问的 API 端点，可以创建或编辑 `~/.deepagents/config.toml` 文件：

```toml
[providers.openai]
api_key_env = "OPENAI_API_KEY"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
models = ["qwen-turbo", "qwen-plus", "qwen-max"]

[params.openai.qwen-turbo]
api_key = "sk-你的千问API密钥"

[models]
default = "openai:qwen-turbo"
```

### 方法二：使用 LangChain OpenAI 提供商

#### 1. 安装必要的依赖

```bash
cd libs/cli
uv add langchain-openai
```

#### 2. 配置环境变量

编辑 `libs/cli/.env` 文件：

```bash
# 千问 API Key
OPENAI_API_KEY=sk-你的千问API密钥

# 千问 API 端点（可选）
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 3. 使用千问模型

```bash
uv run deepagents --model openai:qwen-turbo
```

## 获取千问 API Key

1. 访问阿里云控制台：https://dashscope.console.aliyun.com/
2. 创建 API Key
3. 将生成的 Key 格式为 `sk-xxxx` 复制到 `OPENAI_API_KEY`

## 可用的千问模型

- `qwen-turbo` - 快速响应，适合日常对话
- `qwen-plus` - 平衡性能和速度
- `qwen-max` - 最强性能，适合复杂任务
- `qwen-long` - 长文本支持
- `qwen-vl-max` - 多模态模型（支持图像）

## 验证配置

运行以下命令验证配置是否成功：

```bash
cd libs/cli
uv run deepagents --model openai:qwen-turbo
```

如果配置成功，CLI 应该能够正常启动并使用千问模型进行对话。

## 常见问题

### Q: 如何切换不同的千问模型？

A: 在启动时使用 `--model` 参数指定：
```bash
uv run deepagents --model openai:qwen-plus
```

### Q: 为什么使用 `openai:` 前缀？

A: 千问提供 OpenAI 兼容接口，因此可以使用 LangChain 的 `openai` 提供商，只需配置正确的 base_url 和 API Key。

### Q: 如何在没有 OpenAI 前缀的情况下使用？

A: 可以在配置文件中创建自定义提供商。参见下面的方法三。

## 方法三：创建自定义千问提供商

如果想要使用 `qwen:` 作为提供商前缀，可以在 `~/.deepagents/config.toml` 文件中创建自定义提供商：

```toml
[providers.qwen]
api_key_env = "OPENAI_API_KEY"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long", "qwen-vl-max"]

[models]
default = "qwen:qwen-turbo"
```

然后使用：
```bash
uv run deepagents --model qwen:qwen-turbo
```

## 参考资源

- 阿里云 DashScope 文档：https://help.aliyun.com/zh/dashscope/
- LangChain 文档：https://docs.langchain.com/oss/python/deepagents/cli
- DeepAgents CLI 文档：https://docs.langchain.com/oss/python/deepagents/cli/overview
