# PDF Qdrant MVP 项目详细分析

> 生成时间: 2026-03-07
> 分析范围: 项目所有文件

---

## 📁 项目概览

这是一个 **PDF 数据提取最小可执行方案 (MVP)**，核心功能是将 PDF 文件内容向量化后存入 Qdrant 向量数据库，并支持语义搜索查询。

---

## 📂 项目结构与文件详解

### 1️⃣ 配置文件

#### [`.env`](.env)
**用途**: 实际使用的环境变量配置（包含敏感信息）

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `OPENAI_API_KEY` | `sk-fc3984...` | 千问模型 API 密钥 |
| `OPENAI_BASE_URL` | `https://dashscope.aliyuncs.com/...` | 阿里云 DashScope API 端点 |
| `QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant 服务地址 |
| `PDF_DIR` | `E:\...\paper` | PDF 文件存放目录（10 篇学术论文） |
| `CHUNK_SIZE` | `1000` | 文本分块大小 |
| `EMBEDDING_MODEL` | `text-embedding-v3` | 千问 embedding 模型 |
| `EMBEDDING_DIMENSION` | `1024` | 向量维度 |

---

#### [`.env.example`](.env.example)
**用途**: 环境变量模板文件（不含敏感信息，用于复制参考）

额外包含的配置：
- `CHUNK_OVERLAP=200` - 块重叠字符数
- `LOG_LEVEL=INFO` - 日志级别

---

#### [`docker-compose.yml`](docker-compose.yml)
**用途**: Docker Compose 配置，用于部署 Qdrant 向量数据库

```yaml
关键配置:
- 镜像: qdrant/qdrant:latest
- 容器名: pdf-qdrant-mvp
- 端口映射:
  - 6333: HTTP API 端口
  - 6334: gRPC API 端口
- 数据卷: ./qdrant_storage 持久化存储
- 健康检查: 每 30s 检查 /readyz 端点
```

---

#### [`requirements.txt`](requirements.txt)
**用途**: Python 依赖包列表

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| `qdrant-client` | ≥1.7.0 | Qdrant 客户端 |
| `openai` | ≥1.0.0 | 向量嵌入生成 |
| `pdfplumber` | ≥0.11.0 | PDF 文本提取 |
| `python-dotenv` | ≥1.0.0 | 环境变量管理 |
| `rich` | ≥13.7.0 | 终端美化输出 |
| `requests` | ≥2.31.0 | HTTP 请求 |
| `typing-extensions` | ≥4.9.0 | 类型提示 |

---

### 2️⃣ 文档文件

#### [`README.md`](README.md)
**用途**: 项目使用说明和快速入门指南

内容包含：
- 功能特性说明
- 目录结构
- 快速开始（5 步骤）
- 集合命名规则
- 配置说明
- 常用命令

---

#### [`MVP_PLAN.md`](MVP_PLAN.md)
**用途**: 详细技术方案文档

核心内容：
- **设计原则**: 一个 PDF 对应一个数据库表
- **技术架构图**: PDF → Python 脚本 → Qdrant → 查询
- **存入流程**: 扫描 → 提取 → 分块 → 向量化 → 存储
- **查询流程**: 列表 → 选择 → 输入 → 搜索 → 返回
- **命名规则**: 小写 + 下划线 + 截断 50 字符
- **预期输出示例**

---

### 3️⃣ 源代码文件 (`src/`)

#### [`__init__.py`](src/__init__.py)
**用途**: 包初始化文件
```python
__version__ = "0.1.0"
```

---

#### [`config.py`](src/config.py)
**用途**: 配置管理模块

**核心类**: `Config`

**主要功能**:
1. **加载环境变量**: 支持从多个路径加载 `.env` 文件
2. **配置项管理**:
   - OpenAI API 配置（支持两种变量名）
   - Qdrant 连接配置
   - PDF 目录配置
   - 向量化参数
3. **`validate()` 方法**: 验证配置完整性
4. **`to_dict()` 方法**: 转换为字典（隐藏敏感信息）

---

#### [`pdf_tools.py`](src/pdf_tools.py)
**用途**: PDF 处理工具模块

**核心函数**:

| 函数 | 功能 | 参数 |
|------|------|------|
| `sanitize_collection_name()` | 将文件名转换为合法集合名 | filename |
| `extract_text_from_pdf()` | 提取 PDF 文本内容 | pdf_path |
| `chunk_text()` | 将文本分割成块 | text, chunk_size, overlap |
| `get_pdf_files()` | 获取目录下所有 PDF 文件 | pdf_dir |

**集合命名规则**:
1. 移除 `.pdf` 扩展名
2. 转小写
3. 特殊字符替换为下划线
4. 合并连续下划线
5. 截断到 50 字符

**文本分块策略**:
- 按字符数分割
- 智能识别句子边界（。. ! ? ！？\n）
- 支持块重叠

---

#### [`vector_tools.py`](src/vector_tools.py)
**用途**: Qdrant 向量数据库操作模块

**核心类**: `QdrantManager`

**主要方法**:

| 方法 | 功能 |
|------|------|
| `__init__()` | 初始化 Qdrant 客户端并测试连接 |
| `create_collection()` | 创建集合（表） |
| `delete_collection()` | 删除集合 |
| `list_collections()` | 列出所有集合 |
| `get_collection_info()` | 获取集合详情 |
| `generate_embedding()` | 生成文本向量嵌入 |
| `upsert_points()` | 批量插入/更新向量点 |
| `search()` | 向量相似性搜索 |

**向量配置**:
- 距离度量: COSINE（余弦相似度）
- 向量维度: 1024（千问 embedding）

---

#### [`ingest_pdfs.py`](src/ingest_pdfs.py)
**用途**: PDF 数据存入脚本（主入口之一）

**命令行参数**:
```bash
--pdf-dir, -d    PDF 目录路径
--chunk-size, -s 文本块大小（默认 1000）
--chunk-overlap, -o 块重叠（默认 200）
--dry-run, -n    模拟运行，不实际存入
```

**执行流程**:
1. 加载配置并验证
2. 连接 Qdrant 数据库
3. 扫描 PDF 目录
4. 遍历每个 PDF 文件:
   - 生成集合名
   - 创建集合（如不存在）
   - 提取文本内容
   - 分块处理
   - 生成向量嵌入
   - 存入 Qdrant
5. 输出统计结果

---

#### [`query_pdfs.py`](src/query_pdfs.py)
**用途**: PDF 数据查询脚本（主入口之二）

**命令行参数**:
```bash
--list, -l           列出所有集合
--collection, -c     指定集合名称
--query, -q          查询文本
--top, -t            返回结果数量（默认 5）
--threshold          相似度阈值（默认 0.7）
```

**核心函数**:

| 函数 | 功能 |
|------|------|
| `list_collections()` | 列出所有集合并显示为表格 |
| `search_collection()` | 在指定集合中执行语义搜索 |
| `interactive_mode()` | 交互式查询模式（REPL） |

**查询输出**:
- 相似度得分
- 来源文件
- 文本预览（截断显示）

---

#### [`pdf_to_markdown.py`](src/pdf_to_markdown.py)
**用途**: PDF 转 Markdown 工具（额外功能）

**命令行参数**:
```bash
--pdf-dir, -d     PDF 目录
--output-dir, -o  输出目录（默认 markdown_docs）
--overwrite, -w   覆盖已存在文件
```

**转换功能**:
- 提取 PDF 完整文本
- 添加元信息头（源路径、页数、字符数、转换时间）
- 输出为 `.md` 文件

**用途**: 转换后的 Markdown 可用于 MCP RAG 工具添加完整文档

---

### 4️⃣ 测试文件

#### [`test_setup.py`](test_setup.py)
**用途**: 系统配置和连接验证测试脚本

**测试项**:

| 测试函数 | 验证内容 |
|----------|----------|
| `test_config()` | 配置加载是否正确 |
| `test_qdrant_connection()` | Qdrant 数据库连接 |
| `test_pdf_files()` | PDF 文件检测 |
| `test_embedding()` | Embedding 生成功能 |
| `test_single_pdf_ingest()` | 单个 PDF 导入流程 |

**运行方式**: `python test_setup.py`

---

### 5️⃣ 数据目录

#### `qdrant_storage/`
**用途**: Qdrant 数据持久化存储目录（Docker 挂载）

**内容**:
- `.qdrant_fs_check` - 文件系统检查标记
- `raft_state.json` - 集群状态
- `aliases/data.json` - 别名数据
- `collections/` - 集合数据

#### `markdown_docs/`
**用途**: PDF 转换后的 Markdown 文件存储目录

**已转换文件**（10 个学术论文）:
1. Acid gas-induced fabrication of hydrophilic carbon nitride.md
2. Activation of peroxymonosulfate by single-atom Fe-g-C3N4 catalysts...
3. CO electroreduction on single-atom copper.md
4. ... 等 10 篇论文

---

## 🔄 数据流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户操作                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌──────────────────┐                         ┌──────────────────┐
│  ingest_pdfs.py  │                         │  query_pdfs.py   │
│   (数据存入)      │                         │   (数据查询)      │
└────────┬─────────┘                         └────────┬─────────┘
         │                                            │
         ▼                                            ▼
┌──────────────────┐                         ┌──────────────────┐
│   pdf_tools.py   │                         │  vector_tools.py │
│  - extract_text  │                         │  - search()      │
│  - chunk_text    │                         │  - generate_emb  │
└────────┬─────────┘                         └────────┬─────────┘
         │                                            │
         ▼                                            ▼
┌──────────────────┐                         ┌──────────────────┐
│  vector_tools.py │                         │     Qdrant       │
│  - generate_emb  │◄────────────────────────│   向量数据库      │
│  - upsert_points │                         │  (localhost:6333)│
└────────┬─────────┘                         └──────────────────┘
         │
         ▼
┌──────────────────┐
│     Qdrant       │
│   向量数据库      │
│  (Docker 容器)   │
└──────────────────┘
```

---

## 🚀 快速使用指南

```bash
# 1. 启动 Qdrant
docker-compose up -d

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env 填入 API Key

# 4. 存入 PDF
python src/ingest_pdfs.py

# 5. 查询数据
python src/query_pdfs.py --list
python src/query_pdfs.py -c co_electroreduction_on_single_atom_copper -q "copper catalyst"

# 6. 转换为 Markdown
python src/pdf_to_markdown.py --overwrite
```

---

## 📊 技术栈总结

| 层级 | 技术 |
|------|------|
| **前端交互** | Rich (终端 UI) |
| **PDF 处理** | pdfplumber |
| **向量生成** | OpenAI API (千问 text-embedding-v3) |
| **向量存储** | Qdrant (Docker) |
| **配置管理** | python-dotenv |
| **语言** | Python 3.x |

---

## 📋 核心模块依赖关系

```
ingest_pdfs.py
    ├── config.py (配置)
    ├── pdf_tools.py (PDF处理)
    │   └── pdfplumber
    └── vector_tools.py (向量操作)
        ├── qdrant-client
        └── openai (embedding)

query_pdfs.py
    ├── config.py (配置)
    └── vector_tools.py (向量操作)
        ├── qdrant-client
        └── openai (embedding)

pdf_to_markdown.py
    ├── config.py (配置)
    └── pdf_tools.py (PDF处理)
```

---

## 🔧 扩展方向

此 MVP 可扩展为完整 Agent 系统：
1. 添加 LLM 进行智能数据提取
2. 添加表格识别和结构化
3. 添加数据验证模块
4. 添加 Excel 导出功能
5. 添加多语言支持
6. 添加增量更新机制
