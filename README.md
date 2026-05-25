# Deep Agents 项目环境配置指南

本项目是基于 [Deep Agents](https://github.com/langchain-ai/deepagents) 的本地部署版本，包含交互式 AI Agent CLI 以及 PDF/Markdown 数据处理工具链。

---

## 环境要求

| 项目 | 版本要求 |
|------|---------|
| Python | >= 3.11, < 4.0 |
| 操作系统 | Windows 10/11 |

> 本项目已自带隔离的 Python 环境（`.conda` 目录），**无需额外安装 Python 或配置系统 PATH**。

---

## 快速开始

### 1. 环境配置（已自动完成）

项目已配置独立的 Python 3.11 环境，并安装以下核心组件：

- **deepagents SDK** (v0.4.4) — Agent 核心框架
- **deepagents-cli** (v0.0.25) — 终端交互式 CLI
- **PDF Qdrant MVP 依赖** — 包含 `qdrant-client`, `pdfplumber`, `python-docx`, `numpy` 等

如果你需要重新安装或迁移项目，请按以下步骤操作：

```cmd
:: 进入项目根目录
cd /d e:\get_data_Agent

:: 1. 安装 deepagents 核心库（本地可编辑模式）
.conda\Scripts\pip.exe install -e deepagents_GDatas\libs\deepagents

:: 2. 安装 deepagents-cli（本地可编辑模式）
.conda\Scripts\pip.exe install -e deepagents_GDatas\libs\cli

:: 3. 安装 PDF 处理相关依赖
.conda\Scripts\pip.exe install -r deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\requirements.txt
```

### 2. 验证安装

```cmd
:: 查看 deepagents 版本
.conda\Scripts\deepagents.exe --version

:: 或直接使用项目根目录的包装脚本
deepagents --version
```

正常应输出：
```
deepagents-cli 0.0.25
deepagents (SDK) 0.4.4
```

---

## 主要功能与使用方式

### 一、Deep Agents CLI（交互式 AI 终端）

```cmd
:: 启动交互式会话（项目根目录下）
deepagents

:: 恢复上次会话
deepagents -r

:: 非交互模式执行单次任务
deepagents -n "读取 README.md 并总结内容"

:: 查看帮助
deepagents --help
```

> **提示**：由于 `.conda\Scripts` 未加入系统 PATH，项目根目录已提供 `deepagents.bat` 包装脚本，可直接在根目录下运行 `deepagents` 命令。若在其他目录使用，请调用完整路径 `.conda\Scripts\deepagents.exe`。

### 二、PDF 批量转 Markdown（双击运行）

| 批处理文件 | 功能说明 |
|-----------|---------|
| [`batch_convert_to_pdf.bat`](batch_convert_to_pdf.bat) | 将 `E:\数据集\512` 目录下的 PDF/DOCX/DOC 批量转换为 Markdown，输出到 `markdown_output` |
| [`convert_pdf_to_markdown_batch.bat`](convert_pdf_to_markdown_batch.bat) | 通用批量转换工具，支持自定义输入/输出目录，自动检查并安装依赖 |
| [`convert_pdf_to_markdown.py`](convert_pdf_to_markdown.py) | Python 入口脚本，将 `D:\数据集\论文分段存储0\pdf4001-5000` 下的 PDF 转为 Markdown |

**使用方法**：
1. 双击对应的 `.bat` 文件即可运行。
2. 批处理文件已配置为使用项目自带的 `.conda` 环境，无需系统 Python。
3. 如需修改输入/输出路径，请用文本编辑器打开 `.bat` 文件，修改其中的 `DOC_DIR` 和 `OUTPUT_DIR` 变量。

### 三、Markdown 入库 Qdrant（向量化存储）

```cmd
:: 将 markdown_output_3001-4000 目录下的文件存入 Qdrant 向量数据库
ingest_markdown_3001_4000.bat
```

### 四、数据提取脚本

位于 `deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\` 目录下：

```cmd
:: 批量提取所有集合数据
cd deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
.conda\python.exe extract_all_collections_dac.py

:: 单个集合提取
.conda\python.exe extract_dac_synthesis.py

:: JSON 转 Excel
.conda\python.exe extract_json_to_excel.py
```

详细操作请参考 [`TERMINAL_RUN_GUIDE.md`](deepagents_GDatas/libs/cli/deepagents_cli/pdf_qdrant_mvp/TERMINAL_RUN_GUIDE.md)。

---

## 环境变量配置

PDF Qdrant MVP 模块已配置好 `.env` 文件，位于：

```
deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\.env
```

主要配置项：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | `sk-fc3984cf3d8a4214a0ea781b417a25b7` | DashScope（通义千问）API Key |
| `OPENAI_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 千问兼容接口地址 |
| `QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant 向量数据库地址 |
| `PDF_DIR` | `E:\get_data_Agent\...` | PDF 文件存放目录 |
| `EMBEDDING_MODEL` | `text-embedding-v3` | 嵌入模型名称 |
| `EMBEDDING_DIMENSION` | `1024` | 向量维度 |

> **注意**：如需更换 API Key 或其他配置，请直接编辑上述 `.env` 文件。

---

## 项目目录结构

```
e:\get_data_Agent
├── .conda/                          # 项目自带的 Python 3.11 环境（已预装依赖）
├── deepagents_GDatas/
│   ├── libs/
│   │   ├── cli/                     # deepagents-cli 源码
│   │   │   ├── deepagents_cli/      # CLI 主代码
│   │   │   │   ├── pdf_qdrant_mvp/  # PDF 处理 & Qdrant 工具链
│   │   │   │   │   ├── src/         # 核心脚本（转换、提取、入库）
│   │   │   │   │   ├── .env         # 环境变量配置
│   │   │   │   │   └── requirements.txt
│   │   │   │   └── ...
│   │   └── deepagents/              # deepagents SDK 源码
│   └── examples/                    # 示例 Agent
├── batch_convert_to_pdf.bat         # PDF→Markdown 批量转换（目录3001-4000）
├── convert_pdf_to_markdown_batch.bat # 通用批量转换工具
├── convert_pdf_to_markdown.py       # Python 转换入口
├── ingest_markdown_3001_4000.bat    # Markdown 入库 Qdrant
├── markdown_output/                 # 默认 Markdown 输出目录
└── README.md                        # 本文件
```

---

## 常见问题

### Q1: 输入 `deepagents` 提示 "无法识别为 cmdlet"

**原因**：`.conda\Scripts` 未加入系统 PATH。  
**解决**：在项目根目录下使用 `deepagents.bat` 包装脚本，或调用完整路径：

```cmd
.conda\Scripts\deepagents.exe --version
```

### Q2: 批处理运行时提示缺少 `pdfplumber` 等模块

**原因**：系统 Python 与项目 `.conda` 环境不一致。  
**解决**：批处理文件已修改为强制使用 `.conda\python.exe`，请确认 `.conda` 目录存在且未被删除。如需要，可重新执行依赖安装：

```cmd
.conda\Scripts\pip.exe install -r deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\requirements.txt
```

### Q3: 如何修改默认模型？

启动 `deepagents` 后，使用 `--default-model` 参数或在交互界面中切换模型。支持的模型提供商包括 OpenAI、Anthropic、Google、DashScope（千问）等。

---

## 参考文档

- [Deep Agents 官方文档](https://docs.langchain.com/oss/python/deepagents/overview)
- [CLI 文档](https://docs.langchain.com/oss/python/deepagents/cli/overview)
- [TERMINAL_RUN_GUIDE.md](deepagents_GDatas/libs/cli/deepagents_cli/pdf_qdrant_mvp/TERMINAL_RUN_GUIDE.md) — 数据提取脚本终端运行指南
