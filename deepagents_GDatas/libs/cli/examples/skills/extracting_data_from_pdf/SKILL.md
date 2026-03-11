---
name: extracting-data-from-pdf
description:
  一个用于从科学 PDF 文档中提取结构化数据的技能。
  该技能提供完整的 PDF 数据提取流水线：
  1. PDF 转 Markdown (convert_pdf_to_markdown)
  2. Markdown 文件分块 (chunk_single_markdown_file)
  3. 存入向量数据库 (store_single_file_to_vector_db)
  4. 提取双原子催化剂信息 (extract_dual_atom_catalyst)
  当用户需要从科学论文 PDF 中提取催化剂合成信息时使用此技能。
tools:
  - convert_pdf_to_markdown
  - chunk_single_markdown_file
  - store_single_file_to_vector_db
  - list_vector_db_collections
  - delete_collections_by_pattern
  - delete_all_vector_db_collections
  - extract_dual_atom_catalyst
---

# PDF 数据提取技能

本技能提供了一套完整的流水线工具，用于从科学 PDF 文档中提取双原子催化剂的结构化合成数据。

## 核心工作流程

```
┌─────────────────────────────┐
│  1. convert_pdf_to_markdown │
│     PDF → Markdown          │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  2. chunk_single_markdown   │
│     Markdown → 文本块        │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  3. store_single_file_to    │
│     _vector_db              │
│     文本块 → 向量数据库       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  4. extract_dual_atom       │
│     _catalyst               │
│     向量搜索 → 结构化数据     │
└─────────────────────────────┘
```

## 功能特性

### 1. PDF 转 Markdown (`convert_pdf_to_markdown`)
- 使用 pdfplumber 提取 PDF 文本
- 精确保留化学式下标/上标（如 H₂O、Fe²⁺、cm²）
- 保留科学计数法（如 10⁻⁵）
- 保留表格结构（Markdown 表格格式）
- 自动识别标题并添加层级

### 2. 文本分块 (`chunk_single_markdown_file`)
- 智能分割：在句号位置分割，避免截断句子
- 合并小段落：将过小的段落与相邻段落合并
- 保留标题上下文：标题会与下一段落合并
- 可配置块大小（默认 1000 字符）

### 3. 向量存储 (`store_single_file_to_vector_db`)
- 自动创建 Qdrant 集合
- 使用 OpenAI Embeddings 生成向量
- 支持批量存储
- 自动根据文件名生成集合名称

### 4. 催化剂提取 (`extract_dual_atom_catalyst`)
- 语义搜索：在向量数据库中搜索相关内容
- LLM 结构化：使用大语言模型提取结构化数据
- 提取字段：
  - 反应步数
  - 反应物及用量
  - 温度、时间、气氛
  - 中间产物和最终产物
  - 活性位点结构
  - 金属-金属距离（键长）

## 使用场景

当用户需要以下操作时使用此技能：
- 从 PDF 论文中提取双原子催化剂的合成方法
- 将 PDF 文档转换为可搜索的向量数据
- 获取催化剂的详细实验条件
- 提取反应步骤、温度、时间等结构化信息

## 可用工具

### 核心工具（按顺序使用）

| 序号 | 工具 | 描述 |
|------|------|------|
| 1 | `convert_pdf_to_markdown` | 将 PDF 文件转换为 Markdown 格式 |
| 2 | `chunk_single_markdown_file` | 对单个 Markdown 文件进行智能分块 |
| 3 | `store_single_file_to_vector_db` | 将单个文件分块并存入 Qdrant 向量数据库 |
| 4 | `extract_dual_atom_catalyst` | 从向量数据库中提取结构化的 DAC 合成信息 |

### 辅助工具

| 工具 | 描述 |
|------|------|
| `list_vector_db_collections` | 列出 Qdrant 中已存储的所有集合 |
| `delete_collections_by_pattern` | 按模式删除集合 |
| `delete_all_vector_db_collections` | 删除所有集合（⚠️ 危险操作） |

## 使用示例

### 完整流程示例

```python
# 步骤 1: 将 PDF 转换为 Markdown
result = convert_pdf_to_markdown(
    pdf_path="paper.pdf",
    output_dir="markdown_docs",
    overwrite=False
)
print(f"输出文件: {result['output_file']}")

# 步骤 2: 对 Markdown 文件进行分块
chunk_result = chunk_single_markdown_file(
    md_path="markdown_docs/paper.md",
    chunk_size=1000,
    overlap=200,
    min_chunk_size=500
)
print(f"生成了 {chunk_result['chunk_count']} 个块")

# 步骤 3: 将分块后的文本存入向量数据库
store_result = store_single_file_to_vector_db(
    md_path="markdown_docs/paper.md",
    collection_name="paper_collection",  # 可选，默认根据文件名生成
    chunk_size=1000,
    chunk_overlap=200,
    batch_size=10
)
print(f"集合名: {store_result['collection_name']}")
print(f"存入向量数: {store_result['points_added']}")

# 步骤 4: 提取双原子催化剂的合成信息
extraction = extract_dual_atom_catalyst(
    collection_name="paper_collection"
)
print(extraction["extraction"]["data"])
```

### 查看已存储的集合

```python
result = list_vector_db_collections()
for col in result['collections']:
    print(f"集合: {col['name']}, 向量数: {col['points_count']}")
```

## 返回值结构

### convert_pdf_to_markdown
```python
{
    "success": True,
    "input_file": "paper.pdf",
    "output_file": "markdown_docs/paper.md",
    "char_count": 15000,
    "pages": 10,
    "error": None
}
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

### store_single_file_to_vector_db
```python
{
    "status": "success",
    "collection_name": "paper",
    "file_name": "paper.md",
    "char_count": 15000,
    "chunks_count": 15,
    "points_added": 15,
    "message": "成功将 15 个文本块存入集合 paper",
    "error": None
}
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
            "reaction_steps": 4,
            "step_1": {
                "reactants": [
                    {"reactant": "Zn(NO3)2·6H2O", "amount": "8000 mg"}
                ],
                "temperature": "room temperature",
                "reaction_time": "dissolved",
                "atmosphere": "air",
                "product": "solution A"
            },
            "double_atom_catalyst_active_site": {
                "active_site": "Fe2N6",
                "loading": "0.1 mg/cm²",
                "metal_metal_distance": "2.88 Å"
            }
        }
    }
}
```

## 前置条件

1. **Qdrant 向量数据库**：必须运行且可访问（默认 localhost:6333）
2. **OpenAI API**：必须配置有效的 API Key（用于向量嵌入和 LLM 提取）
3. **PDF 文件**：应具有清晰的文本内容（非扫描件）

## 配置说明

在 `.env` 文件中配置以下环境变量：

```env
# Qdrant 配置
QDRANT_URL=http://localhost:6333

# OpenAI 配置
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
```

## 注意事项

1. **PDF 质量**：提取质量取决于原始 PDF 的质量，扫描件效果较差
2. **化学式保留**：化学式会自动保留下标/上标格式（如 H₂O → H₂O）
3. **集合命名**：集合名称会自动从文件名生成，只保留小写字母、数字和下划线
4. **存储覆盖**：如果集合已存在，新数据会追加到现有集合中
5. **LLM 调用**：`extract_dual_atom_catalyst` 会调用 LLM 进行结构化提取，请确保 API 可用

## 工作流程详解

### 标准流程（推荐）

1. **转换 PDF** → 使用 `convert_pdf_to_markdown` 将 PDF 转为 Markdown
2. **分块处理** → 使用 `chunk_single_markdown_file` 对文本进行智能分块
3. **向量存储** → 使用 `store_single_file_to_vector_db` 存入 Qdrant
4. **数据提取** → 使用 `extract_dual_atom_catalyst` 提取结构化信息

### 快速流程（推荐）

如果不需要单独查看分块结果，可以直接从步骤 1 跳到步骤 3，因为 `store_single_file_to_vector_db` 会自动执行分块操作：

```python
# 快速流程：步骤 1 + 步骤 3（自动包含步骤 2）
convert_pdf_to_markdown(pdf_path="paper.pdf", output_dir="markdown_docs")
store_single_file_to_vector_db(md_path="markdown_docs/paper.md")
extract_dual_atom_catalyst(collection_name="paper")
```

## 错误处理

所有工具都返回包含 `error` 或 `status` 字段的结果：

```python
result = convert_pdf_to_markdown("nonexistent.pdf", "output")
if result.get("error"):
    print(f"错误: {result['error']}")
```

```python
result = store_single_file_to_vector_db("doc.md")
if result.get("status") == "error":
    print(f"存入失败: {result.get('error')}")
```
