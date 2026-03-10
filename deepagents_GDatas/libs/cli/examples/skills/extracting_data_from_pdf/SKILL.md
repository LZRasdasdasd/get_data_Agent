---
name: extracting-data-from-pdf
description: 
  一个用于从科学 PDF 文档中提取结构化数据的技能。
  该技能提供将 PDF 文件转换为 Markdown、为向量嵌入分块文本、
  在 Qdrant 向量数据库中搜索、以及从研究论文中提取催化剂合成信息的工具。
  当用户需要处理 PDF 文件、从科学论文中提取数据或检索催化剂相关信息时使用此技能。
tools:
  - convert_pdf_to_markdown
  - chunk_markdown
  - search_qdrant_collection
  - list_qdrant_collections
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
- 在已索引的科学论文中搜索特定内容
- 从研究文档中提取催化剂合成信息
- 从非结构化 PDF 文本中提取结构化数据
- 处理包含化学式和表格的学术论文

## 可用工具

| 工具 | 描述 |
|------|------|
| `convert_pdf_to_markdown` | 将 PDF 文件转换为 Markdown 格式，保留原有格式 |
| `chunk_markdown` | 将 Markdown 文本分割成块，用于向量嵌入 |
| `search_qdrant_collection` | 在 Qdrant 向量数据库中搜索内容 |
| `list_qdrant_collections` | 列出数据库中所有可用的集合 |
| `delete_collections_by_pattern` | 按模式删除集合 |
| `search_catalyst_content` | 在所有集合中搜索催化剂相关内容 |
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

### 搜索向量数据库
```python
results = search_qdrant_collection(
    collection_name="paper_collection",
    query_text="催化剂合成方法",
    n_results=10,
    score_threshold=0.7
)
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
- 必须配置 OpenAI API 密钥用于嵌入
- PDF 文件应为具有清晰文本内容的科学论文

## 注意事项

- 该技能使用 OpenAI Embeddings 进行向量生成
- 化学式会保留正确的下标/上标格式
- 提取质量取决于原始 PDF 的质量和格式
