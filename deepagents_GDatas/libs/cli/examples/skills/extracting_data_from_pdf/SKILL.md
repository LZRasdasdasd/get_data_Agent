---
name: extracting-data-from-pdf
description:
  一个用于从科学 PDF/DOCX/DOC 文档中提取结构化数据的技能。
  该技能提供完整的文档数据提取流水线：
  1. 文档转 Markdown (convert_pdf_to_markdown)
  2. 文本智能分块 (chunk_text_only / chunk_single_markdown_file)
  3. 向量数据库存储 (store_chunks_to_vector_db / store_single_file_to_vector_db / store_all_files_to_vector_db)
  4. 一步分块+存储 (chunk_and_store_to_qdrant)
  5. 语义搜索 (search_qdrant_collection / search_catalyst_content)
  6. 提取双原子催化剂信息 (extract_dual_atom_catalyst)
  7. 导出 JSON 到 Excel/CSV (extract_single_json_to_excel / process_json_directory_to_excel)
  当用户需要从科学论文中提取催化剂合成信息或进行文档向量化检索时使用此技能。
tools:
  - convert_pdf_to_markdown
  - chunk_text_only
  - chunk_single_markdown_file
  - store_chunks_to_vector_db
  - store_single_file_to_vector_db
  - store_all_files_to_vector_db
  - chunk_and_store_to_qdrant
  - search_qdrant_collection
  - list_qdrant_collections
  - list_vector_db_collections
  - delete_collections_by_pattern
  - delete_all_vector_db_collections
  - search_catalyst_content
  - extract_dual_atom_catalyst
  - extract_single_json_to_excel
  - process_json_directory_to_excel
---

# PDF 数据提取技能

本技能提供了一套完整的流水线工具，用于从科学 PDF/DOCX/DOC 文档中提取双原子催化剂的结构化合成数据，并支持向量数据库存储与语义搜索。

## 核心工作流程

```
┌──────────────────────────────────┐
│  1. convert_pdf_to_markdown      │
│     PDF/DOCX/DOC → Markdown      │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  2. chunk_text_only /            │
│     chunk_single_markdown_file   │
│     Markdown → 文本块             │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  3. store_chunks_to_vector_db /  │
│     store_single_file_to         │
│     _vector_db /                 │
│     store_all_files_to_vector_db │
│     文本块 → Qdrant 向量数据库     │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  4. search_qdrant_collection /   │
│     search_catalyst_content      │
│     语义搜索相关内容               │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  5. extract_dual_atom_catalyst   │
│     向量搜索 → LLM 结构化数据      │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  6. extract_single_json_to       │
│     _excel /                     │
│     process_json_directory       │
│     _to_excel                    │
│     JSON → Excel/CSV             │
└──────────────────────────────────┘
```

## 功能特性

### 1. 文档转 Markdown (`convert_pdf_to_markdown`)
- 支持 PDF、DOCX、DOC 三种文档格式
- PDF：使用 pdfplumber 字符级提取，精确保留下标/上标格式（如 H₂O、Fe²⁺、cm²）
- DOCX：使用 python-docx 提取段落、表格、标题、列表等结构化内容
- DOC：先转换为 DOCX（依赖 LibreOffice 或 MS Word），再按 DOCX 流程处理
- 保留科学计数法（如 10⁻⁵）
- 保留表格结构（Markdown 表格格式）
- 自动识别标题并添加层级

### 2. 文本分块工具

#### `chunk_text_only`
- 独立文本分块工具，不涉及向量数据库操作
- 直接对 Markdown 文本字符串进行分块
- 分块后可通过 `store_chunks_to_vector_db` 存入向量数据库

#### `chunk_single_markdown_file`
- 对单个 Markdown 文件进行分块（不存入向量数据库）
- 适合预览分块结果后再决定是否入库

**分块策略：**
- 智能分割：在句号位置分割，避免截断句子
- 合并小段落：将过小的段落与相邻段落合并
- 保留标题上下文：标题会与下一段落合并
- 可配置块大小（默认 1000 字符）、重叠（默认 200）、最小块大小（默认 500）

### 3. 向量存储工具

#### `store_chunks_to_vector_db`
- 独立向量存储工具，将已分块的文本存入 Qdrant
- 需要先通过 `chunk_text_only` 或 `chunk_single_markdown_file` 进行文本分块

#### `store_single_file_to_vector_db`
- 将单个 Markdown 文件自动分块并存入 Qdrant（一步完成）
- 自动根据文件名生成集合名称

#### `store_all_files_to_vector_db`
- 批量将目录下所有 Markdown 文件分块并存入 Qdrant
- 适合一次性构建完整文档库

**存储特性：**
- 自动创建 Qdrant 集合
- 使用 OpenAI Embeddings 生成向量
- 支持批量存储（可配置 batch_size）
- 支持标题提取模式（使用 LLM 从内容中提取论文标题作为集合名）

### 4. 一步完成分块+存储 (`chunk_and_store_to_qdrant`)
- 将文本分块和向量存储合并为一步操作
- 传入 Markdown 文本和集合名称即可完成入库
- 内部自动执行：分块 → 创建集合 → 生成嵌入 → 存入向量

### 5. 语义搜索工具

#### `search_qdrant_collection`
- 在指定 Qdrant 集合中执行语义搜索
- 使用 OpenAI Embeddings 将查询文本转换为向量
- 支持配置相似度阈值（score_threshold）和返回数量（n_results）

#### `search_catalyst_content`
- 在所有 Qdrant 集合中搜索与催化剂合成相关的内容
- 使用专门的催化剂合成相关关键词进行语义搜索
- 自动按相似度排序并去重

### 6. 催化剂提取 (`extract_dual_atom_catalyst`)
- 语义搜索：在向量数据库中搜索与双原子催化剂合成相关的内容
- LLM 结构化：使用大语言模型（支持 qwen-plus 等模型）提取结构化数据
- 提取字段：
  - 论文标题（paper_title）
  - 反应步数（reaction_steps）
  - 每步反应物及用量（含催化剂标记）
  - 温度、时间、气氛
  - 中间产物和最终产物
  - 活性位点结构（active_site）
  - 金属-金属距离（metal_metal_distance）
  - 金属配位环境（metal_coordination）
  - 催化性能（catalytic_performance）

### 7. 数据导出工具

#### `extract_single_json_to_excel`
- 将单个 JSON 提取结果转换为 Excel/CSV 格式的结构化数据
- 支持温度单位转换（开尔文→摄氏度）
- 支持时间单位转换（分钟/天→小时）
- 自动提取气氛信息

#### `process_json_directory_to_excel`
- 批量处理目录中所有 JSON 文件并导出为合并的 CSV 文件
- 自动跳过 batch_summary 文件

## 使用场景

当用户需要以下操作时使用此技能：
- 从 PDF/DOCX/DOC 论文中提取双原子催化剂的合成方法
- 将文档转换为可搜索的向量数据
- 获取催化剂的详细实验条件
- 提取反应步骤、温度、时间等结构化信息
- 在已索引的文档集合中进行语义搜索
- 将提取结果导出为 Excel/CSV 格式进行数据分析

## 可用工具

### 文档处理工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 1 | `convert_pdf_to_markdown` | 将 PDF/DOCX/DOC 文件转换为 Markdown 格式 |

### 文本分块工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 2 | `chunk_text_only` | 对 Markdown 文本字符串进行智能分块（独立工具） |
| 3 | `chunk_single_markdown_file` | 对单个 Markdown 文件进行分块（不存入数据库） |

### 向量存储工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 4 | `store_chunks_to_vector_db` | 将已分块的文本存入 Qdrant（独立工具） |
| 5 | `store_single_file_to_vector_db` | 将单个文件分块并存入 Qdrant（一步完成） |
| 6 | `store_all_files_to_vector_db` | 将目录下所有文件批量存入 Qdrant |
| 7 | `chunk_and_store_to_qdrant` | 一步完成文本分块和向量存储（传入文本） |

### 搜索工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 8 | `search_qdrant_collection` | 在指定集合中执行语义搜索 |
| 9 | `search_catalyst_content` | 在所有集合中搜索催化剂合成相关内容 |

### 数据库管理工具

| 工具 | 描述 |
|------|------|
| `list_qdrant_collections` | 列出 Qdrant 中所有集合（来自 vector_tools） |
| `list_vector_db_collections` | 列出已存储的集合（来自 vector_store_tool） |
| `delete_collections_by_pattern` | 按模式删除集合 |
| `delete_all_vector_db_collections` | 删除所有集合（⚠️ 危险操作，不可逆） |

### 催化剂提取工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 10 | `extract_dual_atom_catalyst` | 从向量数据库中提取结构化的 DAC 合成信息 |

### 数据导出工具

| 序号 | 工具 | 描述 |
|------|------|------|
| 11 | `extract_single_json_to_excel` | 将单个 JSON 提取结果转换为 Excel/CSV 格式 |
| 12 | `process_json_directory_to_excel` | 批量处理目录中所有 JSON 文件并导出为 CSV |

## 使用示例

### 完整流程示例

```python
# 步骤 1: 将 PDF 转换为 Markdown
result = convert_pdf_to_markdown(
    pdf_path="paper.pdf",
    output_dir="markdown_docs"
)
print(f"输出文件: {result.get('markdown_path', 'N/A')}")

# 步骤 2: 对 Markdown 文本进行分块
chunks = chunk_text_only(
    text=open("markdown_docs/paper.md").read(),
    chunk_size=1000,
    overlap=200,
    min_chunk_size=500
)
print(f"生成了 {len(chunks)} 个块")

# 步骤 3: 将分块后的文本存入向量数据库
store_result = store_chunks_to_vector_db(
    chunks=chunks,
    collection_name="paper_collection",
    source_file="paper.md",
    batch_size=10
)
print(f"存入向量数: {store_result.get('points_added', 0)}")

# 步骤 4: 提取双原子催化剂的合成信息
extraction = extract_dual_atom_catalyst(
    collection_name="paper_collection"
)
print(extraction.get("extraction", {}).get("data", {}))
```

### 快速流程：单文件一步入库

```python
# 步骤 1: 转换 PDF
convert_pdf_to_markdown(pdf_path="paper.pdf", output_dir="markdown_docs")

# 步骤 2+3: 单文件一步分块+入库
result = store_single_file_to_vector_db(
    md_path="markdown_docs/paper.md",
    collection_name="paper"  # 可选，默认根据文件名生成
)
print(f"集合名: {result['collection_name']}")

# 步骤 4: 提取数据
extract_dual_atom_catalyst(collection_name="paper")
```

### 一步完成分块+存储

```python
# 直接传入文本，一步完成分块和入库
result = chunk_and_store_to_qdrant(
    markdown_text="# Title\n\nContent...",
    collection_name="my_document",
    source_file="my_document.md"
)
print(f"状态: {result['status']}, 存入向量数: {result['points_added']}")
```

### 批量处理目录

```python
# 将目录下所有 Markdown 文件存入向量数据库
result = store_all_files_to_vector_db(
    md_dir="markdown_docs",
    chunk_size=1000,
    chunk_overlap=200,
    batch_size=10
)
print(f"处理了 {result.get('total_files', 0)} 个文件")
```

### 语义搜索

```python
# 在指定集合中搜索
results = search_qdrant_collection(
    collection_name="paper_collection",
    query_text="catalyst synthesis temperature",
    n_results=5,
    score_threshold=0.7
)
for r in results:
    print(f"分数: {r['score']}, 内容: {r['text'][:100]}...")

# 在所有集合中搜索催化剂相关内容
results = search_catalyst_content(
    query="dual atom catalyst synthesis procedure",
    top_k_per_collection=5,
    total_top_k=20
)
```

### 查看和管理集合

```python
# 列出所有集合
collections = list_qdrant_collections()
for col in collections:
    print(f"集合: {col['name']}, 向量数: {col.get('points_count', 'N/A')}")

# 按模式删除集合
result = delete_collections_by_pattern(pattern="test_")
print(f"删除了 {result.get('deleted_count', 0)} 个集合")
```

### 导出 JSON 到 Excel/CSV

```python
# 单个 JSON 文件转换
result = extract_single_json_to_excel(
    json_file_path="queried_datas/paper_result.json"
)
print(f"提取了 {result['row_count']} 行数据")

# 批量处理目录
result = process_json_directory_to_excel(
    json_dir="queried_datas",
    output_dir="queried_datas/excel_datas"  # 可选
)
print(f"输出文件: {result['output_file']}")
```

## 返回值结构

### convert_pdf_to_markdown
```python
{
    "success": True,
    "markdown_path": "markdown_docs/paper.md",
    "text": "提取的完整文本内容...",
    "error": None  # 或错误信息
}
```

### chunk_text_only
```python
[
    {"text": "第一个文本块...", "chunk_index": 0, "char_count": 800},
    {"text": "第二个文本块...", "chunk_index": 1, "char_count": 900}
]
```

### chunk_single_markdown_file
```python
{
    "success": True,
    "file_path": "markdown_docs/paper.md",
    "file_name": "paper.md",
    "collection_name": "paper",
    "chunks": [
        {"text": "...", "chunk_index": 0, "char_count": 800},
        {"text": "...", "chunk_index": 1, "char_count": 900}
    ],
    "char_count": 15000,
    "chunk_count": 15,
    "error": None
}
```

### store_chunks_to_vector_db / store_single_file_to_vector_db
```python
{
    "status": "success",
    "collection_name": "paper",
    "chunks_count": 15,
    "points_added": 15,
    "message": "成功将 15 个文本块存入集合 paper",
    "error": None
}
```

### chunk_and_store_to_qdrant
```python
{
    "status": "success",
    "collection_name": "my_document",
    "chunks_count": 10,
    "points_added": 10,
    "message": "成功将 10 个文本块存入集合 my_document",
    "error": None
}
```

### search_qdrant_collection
```python
[
    {
        "text": "匹配的文本内容...",
        "score": 0.85,
        "chunk_index": 3,
        "source_file": "paper.md"
    }
]
```

### search_catalyst_content
```python
[
    {
        "text": "催化剂合成相关内容...",
        "score": 0.82,
        "collection": "paper_collection",
        "source_file": "paper.md",
        "chunk_index": 5
    }
]
```

### extract_dual_atom_catalyst
```python
{
    "metadata": {
        "collection_name": "paper",
        "query": "双原子催化剂合成实验...",
        "timestamp": "20260311_134747",
        "total_results": 10
    },
    "query_results": [...],
    "extraction": {
        "success": True,
        "data": {
            "paper_title": "Dual-Metal Hetero-Single-Atoms...",
            "reaction_steps": 3,
            "step_1": {
                "reactants": [
                    {"reactant": "Zn(NO3)2·6H2O", "amount": "8000 mg", "catalyst": false}
                ],
                "temperature": "25 °C",
                "reaction_time": "1 h",
                "atmosphere": "air",
                "product": "solution A"
            },
            "double_atom_catalyst_active_site": {
                "active_site": "Fe2N6",
                "loading": {"Fe": "0.1 mg/cm2"},
                "metal_metal_distance": "2.88 Å",
                "metal_coordination": {
                    "Fe": {"coordinating_elements": ["N"], "coordination_numbers": {"N": 4.0}},
                    "Co": {"coordinating_elements": ["N"], "coordination_numbers": {"N": 4.0}}
                }
            },
            "catalytic_performance": {}
        }
    }
}
```

### extract_single_json_to_excel
```python
{
    "status": "success",
    "file_name": "extraction_result.json",
    "rows": [
        {
            "step_i": 1,
            "ReactantA": "Zn(NO3)2·6H2O",
            "amountA": "8000 mg",
            "temperature": "25.00",
            "time": "1.00",
            "atmosphere": "N2",
            "active_site": "Fe2N6",
            "metal_metal_distance": "2.88",
            "coordinationtypeA": "N",
            "numbersA": "4.0",
            "coordinationtypeB": "N",
            "numbersB": "4.0",
            "FileName": "extraction_result.json"
        }
    ],
    "row_count": 1
}
```

### process_json_directory_to_excel
```python
{
    "status": "success",
    "total_files": 10,
    "processed_files": 8,
    "total_rows": 25,
    "output_file": "queried_datas/excel_datas/synthesis_data_updated.csv"
}
```

## 前置条件

1. **Qdrant 向量数据库**：必须运行且可访问（默认 `http://localhost:6333`）
   - 可通过 `docker-compose up -d` 启动本地 Qdrant 实例
2. **OpenAI 兼容 API**：必须配置有效的 API Key 和 Base URL
   - 支持 OpenAI 官方 API 或兼容接口（如 DashScope/阿里云）
   - 用于向量嵌入和 LLM 结构化提取
3. **文档文件**：PDF 应具有清晰的文本内容（非扫描件），也支持 DOCX/DOC 格式
4. **可选依赖**：处理 DOC 文件需要 LibreOffice 或 MS Word

## 配置说明

在 `pdf_qdrant_mvp/.env` 文件中配置以下环境变量：

```env
# OpenAI API 配置（支持兼容接口）
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
# 或使用 OPENAI_BASE_URL 环境变量名

# Qdrant 配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# 向量化配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 嵌入模型配置
EMBEDDING_MODEL=text-embedding-v2
EMBEDDING_DIMENSION=1024

# 日志级别
LOG_LEVEL=INFO
```

## 项目结构

```
pdf_qdrant_mvp/
├── .env.example                  # 环境变量模板
├── docker-compose.yml            # Qdrant Docker 配置
├── requirements.txt              # Python 依赖
├── markdown_docs/                # 转换后的 Markdown 文件
├── queried_datas/                # 提取结果 JSON 文件
│   └── excel_datas/              # CSV 导出文件
├── src/
│   ├── qdrant_config.py          # 配置管理（Config 类）
│   ├── pdf_to_markdown.py        # 文档转 Markdown（PDF/DOCX/DOC）
│   ├── chunk_text_tool.py        # 文本分块工具（独立）
│   ├── vector_store_tool.py      # 向量存储工具（独立）
│   ├── ingest_markdown.py        # Markdown 分块+向量化（含 LLM 标题提取）
│   ├── vector_tools.py           # Qdrant 向量操作（QdrantManager）
│   ├── extract_catalyst_info.py  # 单原子催化剂信息搜索（CatalystInfoExtractor）
│   ├── extract_dac_synthesis.py  # 双原子催化剂合成数据提取
│   ├── extract_all_collections_dac.py  # 批量提取所有集合
│   ├── extract_json_to_excel.py  # JSON → Excel/CSV 转换
│   ├── delete_collections.py     # 集合管理（删除操作）
│   └── query_pdfs.py             # PDF 查询脚本
└── qdrant_storage/               # Qdrant 数据持久化目录
```

## 注意事项

1. **文档质量**：提取质量取决于原始文档的质量，扫描件 PDF 效果较差
2. **化学式保留**：化学式会自动保留下标/上标格式（如 H₂O → H₂O）
3. **集合命名**：集合名称会自动从文件名生成，只保留小写字母、数字和下划线；也支持通过 LLM 提取论文标题作为集合名
4. **存储覆盖**：如果集合已存在，新数据会追加到现有集合中
5. **LLM 调用**：`extract_dual_atom_catalyst` 和标题提取会调用 LLM，请确保 API 可用
6. **API 兼容性**：支持 OpenAI 兼容接口，可在 `.env` 中配置 `OPENAI_API_BASE` 或 `OPENAI_BASE_URL`
7. **嵌入模型**：默认使用 `text-embedding-v2`（DashScope），也可配置为 OpenAI 的 `text-embedding-3-small`

## 工作流程详解

### 标准流程（分步操作，推荐用于调试）

1. **转换文档** → 使用 `convert_pdf_to_markdown` 将 PDF/DOCX/DOC 转为 Markdown
2. **分块处理** → 使用 `chunk_text_only` 或 `chunk_single_markdown_file` 对文本进行智能分块
3. **向量存储** → 使用 `store_chunks_to_vector_db` 存入 Qdrant
4. **数据提取** → 使用 `extract_dual_atom_catalyst` 提取结构化信息
5. **导出数据** → 使用 `extract_single_json_to_excel` 或 `process_json_directory_to_excel` 导出

### 快速流程（推荐生产使用）

使用组合工具减少步骤：

```python
# 快速流程：步骤 1 + 步骤 2+3（自动分块+入库） + 步骤 4
convert_pdf_to_markdown(pdf_path="paper.pdf", output_dir="markdown_docs")
store_single_file_to_vector_db(md_path="markdown_docs/paper.md")
extract_dual_atom_catalyst(collection_name="paper")
```

### 一步流程（适合直接处理文本）

```python
# 一步完成分块和存储
result = chunk_and_store_to_qdrant(
    markdown_text="# Title\n\nContent...",
    collection_name="my_document"
)
extract_dual_atom_catalyst(collection_name="my_document")
```

## 错误处理

所有工具都返回包含 `error` 或 `status` 字段的结果：

```python
result = convert_pdf_to_markdown("nonexistent.pdf", "output")
if not result.get("success") or result.get("error"):
    print(f"错误: {result.get('error')}")

result = store_chunks_to_vector_db([], "my_collection")
if result.get("status") == "error":
    print(f"存入失败: {result.get('error')}")

result = extract_dual_atom_catalyst("nonexistent_collection")
if result.get("status") == "error":
    print(f"提取失败: {result.get('error')}")
```

## 依赖项

| 包名 | 用途 |
|------|------|
| `qdrant-client>=1.7.0` | Qdrant 向量数据库客户端 |
| `openai>=1.0.0` | OpenAI API（向量嵌入 + LLM 调用） |
| `pdfplumber>=0.11.0` | PDF 文本提取 |
| `python-docx>=1.1.0` | DOCX 文件处理 |
| `python-dotenv>=1.0.0` | 环境变量管理 |
| `rich>=13.7.0` | 终端美化输出 |
| `requests>=2.31.0` | HTTP 请求 |

## 数据字段说明（CSV 导出）

导出的 CSV 文件包含以下字段：

| 字段 | 描述 |
|------|------|
| `step_i` | 反应步骤编号 |
| `ReactantA-F` | 反应物名称（最多6个） |
| `amountA-F` | 反应物用量 |
| `Intermediate` | 中间产物 |
| `temperature` | 最终温度（摄氏度，已自动转换） |
| `time` | 反应时间（小时，已自动转换） |
| `atmosphere` | 反应气氛 |
| `active_site` | 活性位点结构 |
| `metal_metal_distance` | 金属-金属距离 |
| `coordinationtypeA-B` | 配位类型（按金属分组） |
| `numbersA-B` | 配位数量（按金属分组） |
| `stir` | 是否搅拌 |
| `stir_time` | 搅拌时间 |
| `stir_temperature` | 搅拌温度 |
| `FileName` | 源文件名 |
