---
name: extracting-data-from-pdf
description: 
  一个用于从科学 PDF 文档中提取结构化数据的技能。
  该技能提供将 PDF 文件转换为 Markdown、为向量嵌入分块文本、 
  在 Qdrant 向量数据库中存储和搜索、以及从研究论文中提取催化剂合成信息的工具。
  当用户需要处理 PDF 文件、从科学论文中提取数据或检索催化剂相关信息时使用此技能。
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
  - search_catalyst_content
  - extract_dual_atom_catalyst
---

# PDF 数据提取技能

本技能提供了一套完整的工具集，用于从科学 PDF 文档中提取结构化数据，并专门支持催化剂合成信息的提取。

## 功能特性

### 1. PDF 处理
- **PDF 转 Markdown**：将 PDF 文件转换为结构化的 Markdown 格式，同时保留化学式（下标/上标）、表格和科学符号
- **文本分块**：将 Markdown 文档智能分割成语义连贯的块，用于向量嵌入

### 2. 向量数据库操作
- **独立分块工具**：仅进行文本分块，不涉及向量数据库操作
- **独立存储工具**：支持两种存储模式
  - **全部存入**：批量处理目录下所有 Markdown 文件
  - **按名称存入单个**：处理指定的单个 Markdown 文件
- **语义搜索**：查询 Qdrant 向量数据库，从已索引的文档中查找相关内容
- **集合管理**：列出和管理向量数据库中的文档集合

### 3. 催化剂信息提取
- **单原子催化剂 (SAC)**：搜索和提取单原子催化剂的合成信息
- **双原子催化剂 (DAC)**：提取双原子催化剂的结构化合成步骤，包括：
  - 反应步骤和条件
  - 前驱体和反应物
  - 活性位点结构
  - 温度和气氛条件
  - 金属-金属距离

## 使用场景

当用户需要以下操作时使用此技能：
- 将 PDF 文档转换为 Markdown 格式
- **仅进行文本分块，不需要立即存入向量数据库**
- **将分块后的文本存入向量数据库**
- **批量处理目录下所有 Markdown 文件**
- **按名称存入单个指定文件**
- 在已索引的科学论文中搜索特定内容
- 从研究文档中提取催化剂合成信息
- 从非结构化 PDF 文本中提取结构化数据
- 处理包含化学式和表格的学术论文

## 可用工具

### PDF 处理工具

| 工具 | 描述 |
|------|------|
| `convert_pdf_to_markdown` | 将 PDF 文件转换为 Markdown 格式，保留原有格式 |

### 文本分块工具（独立）

| 工具 | 描述 |
|------|------|
| `chunk_text_only` | 独立的文本分块工具，将 Markdown 文本分割成块，不存入向量数据库 |
| `chunk_single_markdown_file` | 对单个 Markdown 文件进行分块（不存入向量数据库） |

### 向量数据库存储工具（独立）

| 工具 | 描述 |
|------|------|
| `store_chunks_to_vector_db` | 独立的向量存储工具，将文本块存入 Qdrant |
| `store_single_file_to_vector_db` | **按名称存入单个文件** - 将单个 Markdown 文件分块并存入向量数据库 |
| `store_all_files_to_vector_db` | **全部存入** - 批量处理目录下所有 Markdown 文件并存入向量数据库 |
| `list_vector_db_collections` | 列出 Qdrant 中已存储的所有集合 |

### 一步完成工具

| 工具 | 描述 |
|------|------|
| `chunk_and_store_to_qdrant` | 分块并存入向量数据库（一步完成） |

### 向量数据库查询工具

| 工具 | 描述 |
|------|------|
| `search_qdrant_collection` | 在 Qdrant 向量数据库中搜索内容 |
| `list_qdrant_collections` | 列出数据库中所有可用的集合 |
| `delete_collections_by_pattern` | 按模式删除集合 |

### 催化剂信息提取工具

| 工具 | 描述 |
|------|------|
| `search_catalyst_content` | 在所有集合中搜索单原子催化剂相关内容 |
| `extract_dual_atom_catalyst` | 提取结构化的 DAC 合成信息 |

## 使用示例

### 转换 PDF 文件
```python
result = convert_pdf_to_markdown(
    pdf_path="paper.pdf",
    output_dir="markdown_docs",
    overwrite=False
)
```

### 仅进行文本分块（不存入向量数据库）
```python
# 方式1：分块文本内容
chunks = chunk_text_only(
    text="# Title\n\nContent...",
    chunk_size=1000,
    overlap=200,
    min_chunk_size=500
)

# 方式2：分块单个文件
result = chunk_single_markdown_file(
    md_path="paper.md",
    chunk_size=1000,
    overlap=200
)
print(f"生成了 {result['chunk_count']} 个块")
```

### 将分块后的文本存入向量数据库
```python
# 将 chunk_text_only 的输出存入向量数据库
store_result = store_chunks_to_vector_db(
    chunks=chunks,
    collection_name="my_document",
    source_file="paper.md",
    batch_size=10
)
```

### 按名称存入单个文件
```python
# 将指定的单个 Markdown 文件存入向量数据库
result = store_single_file_to_vector_db(
    md_path="paper.md",
    collection_name="paper_collection",  # 可选，默认根据文件名生成
    chunk_size=1000,
    chunk_overlap=200,
    batch_size=10
)

print(f"状态: {result['status']}")
print(f"集合名: {result['pre_name']}")
print(f"块数: {result['chunks_count']}")
```

### 全部存入（批量处理）
```python
# 将目录下所有 Markdown 文件存入向量数据库
result = store_all_files_to_vector_db(
    md_dir="markdown_docs",
    chunk_size=1000,
    chunk_overlap=200,
    min_chunk_size=500,
    batch_size=10
)

print(f"总文件数: {result['total_files']}")
print(f"成功: {result['success_count']}")
print(f"失败: {result['failed_count']}")
print(f"总块数: {result['total_chunks']}")
```

### 一步完成：分块并存入
```python
# 分块并存入向量数据库（一步完成）
result = chunk_and_store_to_qdrant(
    markdown_text="# Title\n\nContent...",
    collection_name="my_document",
    source_file="paper.md",
    chunk_size=1000
)
```

### 搜索向量数据库
```python
results = search_qdrant_collection(
    collection_name="paper_collection",
    query_text="催化剂合成方法",
    n_results=10,
    score_threshold=0.7
)
```

### 列出已存储的集合
```python
# 方式1
collections = list_qdrant_collections()

# 方式2（返回更详细的信息）
result = list_vector_db_collections()
for col in result['collections']:
    print(f"集合: {col['name']}, 向量数: {col['points_count']}")
```

### 提取催化剂信息
```python
# 搜索催化剂内容
content = search_catalyst_content(
    query="单原子催化剂合成",
    total_top_k=20
)

# 提取结构化的 DAC 合成数据
extraction = extract_dual_atom_catalyst(
    collection_name="paper_collection"
)
```

## 前置条件

- Qdrant 向量数据库必须运行且可访问
- 必须配置 OpenAI API 寘ab用于嵌入生成
- PDF 文件应为具有清晰文本内容的科学论文

## 注意事项

- 该技能使用 OpenAI Embeddings 进行向量生成
- 化学式会保留正确的下标/上标格式
- 提取质量取决于原始 PDF 的质量和格式
- 文本分块工具和向量存储工具可以分开使用，也可以使用一步完成工具
- 可以选择全部存入或按名称存入单个文件

## 工作流程

### 标准流程
1. 使用 `convert_pdf_to_markdown` 将 PDF 转换为 Markdown
2. 使用 `chunk_text_only` 进行文本分块
3. 使用 `store_chunks_to_vector_db` 存入向量数据库
4. 使用 `search_qdrant_collection` 进行语义搜索

### 批量处理流程
1. 将所有 PDF 文件转换为 Markdown
2. 使用 `store_all_files_to_vector_db` 一次性处理所有 Markdown 文件
3. 使用 `search_catalyst_content` 搜索单原子催化剂相关内容

### 单文件处理流程
1. 使用 `convert_pdf_to_markdown` 转换单个 PDF
2. 使用 `store_single_file_to_vector_db` 处理该文件
3. 使用 `search_qdrant_collection` 在指定集合中搜索
