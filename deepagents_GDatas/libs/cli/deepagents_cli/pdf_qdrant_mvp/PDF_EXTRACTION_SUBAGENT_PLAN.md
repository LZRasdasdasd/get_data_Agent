# PDF 数据提取 SubAgent 实施规划

## 1. 项目概述

### 1.1 目标
将 `pdf_qdrant_mvp/src/` 目录下的 PDF 处理脚本转换为可被 Agent 识别的工具，并创建一个专门的 SubAgent 来管理这些工具，实现 PDF 文件数据提取的自动化工作流。

### 1.2 现有脚本分析

| 脚本文件 | 功能 | 作为工具的优先级 |
|---------|------|----------------|
| `pdf_to_markdown.py` | PDF 转 Markdown | 核心工具 |
| `ingest_markdown.py` | Markdown 分块与向量化 | 核心工具 |
| `extract_catalyst_info.py` | 单原子催化剂信息提取 | 核心工具 |
| `extract_dac_synthesis.py` | 双原子催化剂合成数据提取 | 核心工具 |
| `vector_tools.py` | Qdrant 向量数据库操作 | 辅助工具 |
| `pdf_tools.py` | PDF 基础处理功能 | 辅助工具 |
| `config.py` | 配置管理 | 基础模块 |
| `query_pdfs.py` | 查询 PDF 数据 | 辅助工具 |
| `delete_collections.py` | 删除集合 | 管理工具 |
| `continue_ingest.py` | 继续导入数据 | 管理工具 |
| `reset_and_ingest.py` | 重置并导入 | 管理工具 |

---

## 2. 架构设计

### 2.1 SubAgent 架构

```
deepagents_cli/
├── pdf_qdrant_mvp/
│   ├── src/                          # 现有脚本（保持不变）
│   │   ├── pdf_to_markdown.py
│   │   ├── ingest_markdown.py
│   │   ├── extract_catalyst_info.py
│   │   ├── extract_dac_synthesis.py
│   │   └── ...
│   └── ...
├── pdf_extraction_tools.py           # 新建：工具函数封装
└── built_in_skills/
    └── pdf-extraction/               # 新建：内置技能/子代理
        └── AGENTS.md                 # SubAgent 定义
```

### 2.2 工具层次结构

```
PDF 数据提取 SubAgent (pdf-extractor)
│
├── 核心工具 (Core Tools)
│   ├── pdf_to_markdown()      # PDF 转 Markdown
│   ├── chunk_markdown()       # Markdown 分块
│   ├── ingest_to_qdrant()     # 数据存入向量数据库
│   ├── extract_single_atom_info()  # 单原子催化剂提取
│   └── extract_dual_atom_info()    # 双原子催化剂提取
│
├── 查询工具 (Query Tools)
│   ├── search_vector_db()     # 向量搜索
│   ├── list_collections()     # 列出集合
│   └── get_collection_info()  # 获取集合信息
│
└── 管理工具 (Management Tools)
    ├── delete_collection()    # 删除集合
    ├── reset_collection()     # 重置集合
    └── get_config()           # 获取配置
```

---

## 3. 实施步骤

### 阶段一：工具函数封装 (Day 1)

#### 3.1.1 创建 `pdf_extraction_tools.py`

**文件位置**: `deepagents_cli/pdf_extraction_tools.py`

**工具函数设计**:

```python
# 1. PDF 转 Markdown 工具
def pdf_to_markdown(
    pdf_path: str,
    output_dir: str | None = None
) -> dict[str, Any]:
    """
    将 PDF 文件转换为 Markdown 格式。
    
    Args:
        pdf_path: PDF 文件的完整路径，或包含 PDF 文件的目录路径
        output_dir: 输出 Markdown 文件的目录，默认为 pdf_qdrant_mvp/markdown_docs
        
    Returns:
        dict: 包含转换结果的字典
            - success: 是否成功
            - files: 转换后的文件列表
            - total_chars: 总字符数
            - error: 错误信息（如果有）
    """

# 2. Markdown 分块工具
def chunk_markdown(
    markdown_dir: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> dict[str, Any]:
    """
    将 Markdown 文件分块，准备向量化。
    
    Args:
        markdown_dir: Markdown 文件目录
        chunk_size: 每个块的最大字符数
        overlap: 块之间的重叠字符数
        
    Returns:
        dict: 包含分块结果的字典
            - success: 是否成功
            - chunks: 分块信息列表
            - total_chunks: 总块数
    """

# 3. 向量化存储工具
def ingest_to_qdrant(
    markdown_dir: str,
    collection_name: str | None = None,
    chunk_size: int = 1000
) -> dict[str, Any]:
    """
    将 Markdown 文件向量化并存入 Qdrant 数据库。
    
    Args:
        markdown_dir: Markdown 文件目录
        collection_name: 集合名称（不指定则为每个文件创建单独集合）
        chunk_size: 分块大小
        
    Returns:
        dict: 包含存储结果的字典
            - success: 是否成功
            - collections: 创建的集合列表
            - total_points: 总向量点数
    """

# 4. 单原子催化剂信息提取工具
def extract_single_atom_catalyst(
    collection_name: str,
    top_k: int = 10,
    output_file: str | None = None
) -> dict[str, Any]:
    """
    从向量数据库中搜索并提取单原子催化剂合成信息。
    
    Args:
        collection_name: 要搜索的集合名称
        top_k: 返回的结果数量
        output_file: 输出 JSON 文件路径（可选）
        
    Returns:
        dict: 包含提取结果的字典
            - success: 是否成功
            - results: 提取的结构化数据列表
            - related_count: 相关结果数
    """

# 5. 双原子催化剂信息提取工具
def extract_dual_atom_catalyst(
    collection_name: str,
    top_k: int = 10,
    output_file: str | None = None
) -> dict[str, Any]:
    """
    从向量数据库中搜索并提取双原子催化剂合成信息。
    
    Args:
        collection_name: 要搜索的集合名称
        top_k: 返回的结果数量
        output_file: 输出 JSON 文件路径（可选）
        
    Returns:
        dict: 包含提取结果的字典
            - success: 是否成功
            - results: 提取的结构化数据
            - has_active_site: 是否包含活性位点信息
    """

# 6. 向量搜索工具
def search_vector_db(
    query: str,
    collection_name: str | None = None,
    top_k: int = 5,
    threshold: float = 0.7
) -> dict[str, Any]:
    """
    在向量数据库中搜索相关内容。
    
    Args:
        query: 查询文本
        collection_name: 集合名称（不指定则搜索所有集合）
        top_k: 返回结果数量
        threshold: 相似度阈值
        
    Returns:
        dict: 包含搜索结果的字典
            - success: 是否成功
            - results: 搜索结果列表
            - query: 原始查询
    """

# 7. 列出集合工具
def list_qdrant_collections() -> dict[str, Any]:
    """
    列出 Qdrant 数据库中所有的集合。
    
    Returns:
        dict: 包含集合列表的字典
            - success: 是否成功
            - collections: 集合信息列表
            - total_count: 总集合数
    """

# 8. 删除集合工具
def delete_qdrant_collection(
    collection_name: str,
    pattern: bool = False
) -> dict[str, Any]:
    """
    删除 Qdrant 数据库中的集合。
    
    Args:
        collection_name: 集合名称或模式
        pattern: 是否按模式匹配删除
        
    Returns:
        dict: 包含删除结果的字典
            - success: 是否成功
            - deleted: 已删除的集合列表
    """

# 9. 获取配置工具
def get_pdf_extraction_config() -> dict[str, Any]:
    """
    获取 PDF 提取工具的当前配置。
    
    Returns:
        dict: 配置信息字典
            - qdrant_url: Qdrant 服务地址
            - embedding_model: 嵌入模型名称
            - chunk_size: 分块大小
            - pdf_dir: PDF 目录
    """
```

---

### 阶段二：SubAgent 定义 (Day 1)

#### 3.2.1 创建 SubAgent 目录结构

```
deepagents_cli/built_in_skills/
└── pdf-extractor/
    ├── AGENTS.md              # SubAgent 定义（必需）
    └── scripts/               # 可选：辅助脚本
        └── validate_env.py    # 环境验证脚本
```

#### 3.2.2 AGENTS.md 内容

```markdown
---
name: pdf-extractor
description: 专门用于处理 PDF 文件数据提取的子代理。可以执行 PDF 转 Markdown、文本分块、向量化存储、以及从科学论文中提取单原子/双原子催化剂合成信息等任务。当用户需要进行 PDF 文档处理、化学文献数据提取、或向量数据库操作时，应调用此子代理。
model: null
---

# PDF 数据提取专家

你是一位专门处理 PDF 文件数据提取的专家助手。你的核心能力包括：

## 核心能力

1. **PDF 转换**: 将 PDF 文件转换为 Markdown 格式，保留化学式和科学符号
2. **文本分块**: 智能分块 Markdown 文本，优化向量检索效果
3. **向量化存储**: 将文本向量化并存入 Qdrant 数据库
4. **信息提取**: 从科学论文中提取单原子/双原子催化剂的合成信息

## 可用工具

### PDF 处理工具
- `pdf_to_markdown`: PDF 转 Markdown
- `chunk_markdown`: Markdown 分块

### 向量数据库工具
- `ingest_to_qdrant`: 数据存入向量数据库
- `search_vector_db`: 搜索向量数据库
- `list_qdrant_collections`: 列出所有集合
- `delete_qdrant_collection`: 删除集合

### 信息提取工具
- `extract_single_atom_catalyst`: 提取单原子催化剂信息
- `extract_dual_atom_catalyst`: 提取双原子催化剂信息

### 配置工具
- `get_pdf_extraction_config`: 获取当前配置

## 工作流程

### 完整处理流程
1. 使用 `pdf_to_markdown` 转换 PDF
2. 使用 `ingest_to_qdrant` 存入向量数据库
3. 使用提取工具获取结构化信息

### 仅查询流程
1. 使用 `list_qdrant_collections` 查看可用数据
2. 使用 `search_vector_db` 或提取工具获取信息

## 注意事项

- 确保 Qdrant 服务正在运行
- 确保 OpenAI API 密钥已配置
- 化学式会保留上下标格式
- 支持 PDF 文件或目录批量处理
```

---

### 阶段三：系统集成 (Day 2)

#### 3.3.1 修改 `agent.py`

在 `agent.py` 中添加 PDF 提取工具的加载逻辑：

```python
# 在 agent.py 中添加
from deepagents_cli.pdf_extraction_tools import (
    pdf_to_markdown,
    chunk_markdown,
    ingest_to_qdrant,
    extract_single_atom_catalyst,
    extract_dual_atom_catalyst,
    search_vector_db,
    list_qdrant_collections,
    delete_qdrant_collection,
    get_pdf_extraction_config,
)

# 在 create_agent 函数中添加工具
PDF_EXTRACTION_TOOLS = [
    pdf_to_markdown,
    chunk_markdown,
    ingest_to_qdrant,
    extract_single_atom_catalyst,
    extract_dual_atom_catalyst,
    search_vector_db,
    list_qdrant_collections,
    delete_qdrant_collection,
    get_pdf_extraction_config,
]
```

#### 3.3.2 修改 `subagents.py`

确保 SubAgent 加载器能识别内置的 `pdf-extractor`：

```python
# 在 list_subagents 函数中添加内置子代理的加载
def list_subagents(...) -> list[SubagentMetadata]:
    # ... 现有代码 ...
    
    # 添加内置 pdf-extractor
    built_in_skills_dir = settings.get_built_in_skills_dir()
    pdf_extractor_dir = built_in_skills_dir / "pdf-extractor"
    if pdf_extractor_dir.exists():
        subagent = _parse_subagent_file(pdf_extractor_dir / "AGENTS.md")
        if subagent:
            subagent["source"] = "built-in"
            subagents["pdf-extractor"] = subagent
    
    return list(subagents.values())
```

---

### 阶段四：测试与验证 (Day 2)

#### 3.4.1 单元测试

创建 `tests/unit_tests/test_pdf_extraction_tools.py`:

```python
def test_pdf_to_markdown():
    """测试 PDF 转 Markdown"""
    pass

def test_chunk_markdown():
    """测试 Markdown 分块"""
    pass

def test_search_vector_db():
    """测试向量搜索"""
    pass

# ... 更多测试 ...
```

#### 3.4.2 集成测试

创建 `tests/integration_tests/test_pdf_extraction_subagent.py`:

```python
def test_subagent_registration():
    """测试 SubAgent 是否正确注册"""
    pass

def test_full_extraction_workflow():
    """测试完整提取流程"""
    pass
```

---

## 4. 文件清单

### 4.1 新建文件

| 文件路径 | 描述 |
|---------|------|
| `deepagents_cli/pdf_extraction_tools.py` | PDF 提取工具函数封装 |
| `deepagents_cli/built_in_skills/pdf-extractor/AGENTS.md` | SubAgent 定义 |
| `deepagents_cli/built_in_skills/pdf-extractor/scripts/validate_env.py` | 环境验证脚本 |
| `tests/unit_tests/test_pdf_extraction_tools.py` | 单元测试 |
| `tests/integration_tests/test_pdf_extraction_subagent.py` | 集成测试 |

### 4.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `deepagents_cli/agent.py` | 添加工具导入和注册 |
| `deepagents_cli/subagents.py` | 添加内置 SubAgent 加载逻辑 |

---

## 5. 工具详细描述

### 5.1 pdf_to_markdown

**名称**: `pdf_to_markdown`

**描述**: 将 PDF 文件转换为 Markdown 格式。支持单文件转换或批量目录转换。自动识别并保留化学式中的上标和下标。

**参数**:
- `pdf_path` (string, required): PDF 文件的完整路径，或包含 PDF 文件的目录路径
- `output_dir` (string, optional): 输出 Markdown 文件的目录，默认为 `pdf_qdrant_mvp/markdown_docs`

**返回值**: 包含 `success`, `files`, `total_chars`, `error` 的字典

**使用示例**:
```
用户：将 paper.pdf 转换为 Markdown
调用：pdf_to_markdown(pdf_path="/path/to/paper.pdf")
```

---

### 5.2 chunk_markdown

**名称**: `chunk_markdown`

**描述**: 将 Markdown 文本分块，用于后续向量化处理。分块算法会保留段落完整性，在句号位置分割，合并过小的段落。

**参数**:
- `markdown_dir` (string, required): Markdown 文件目录
- `chunk_size` (integer, optional): 每个块的最大字符数，默认 1000
- `overlap` (integer, optional): 块之间的重叠字符数，默认 200

**返回值**: 包含 `success`, `chunks`, `total_chunks` 的字典

---

### 5.3 ingest_to_qdrant

**名称**: `ingest_to_qdrant`

**描述**: 将 Markdown 文件向量化并存入 Qdrant 向量数据库。每个文件会创建独立的集合，或可选合并到单一集合。

**参数**:
- `markdown_dir` (string, required): Markdown 文件目录
- `collection_name` (string, optional): 集合名称，不指定则为每个文件创建单独集合
- `chunk_size` (integer, optional): 分块大小，默认 1000

**返回值**: 包含 `success`, `collections`, `total_points` 的字典

**依赖**: 需要 Qdrant 服务运行，需要 OpenAI API 密钥

---

### 5.4 extract_single_atom_catalyst

**名称**: `extract_single_atom_catalyst`

**描述**: 从向量数据库中搜索相关内容，使用 LLM 提取单原子催化剂合成的结构化信息。提取内容包括反应步数、反应单体、活性位点、温度、时间、气氛、产物等。

**参数**:
- `collection_name` (string, required): 要搜索的集合名称
- `top_k` (integer, optional): 返回的结果数量，默认 10
- `output_file` (string, optional): 输出 JSON 文件路径

**返回值**: 包含 `success`, `results`, `related_count` 的字典

**输出格式**: JSON 结构包含:
- `is_related_to_synthesis`: 是否与合成相关
- `reaction_steps`: 反应步数
- `step_N`: 各步骤详情
- `single_atom_catalyst_active_site`: 活性位点

---

### 5.5 extract_dual_atom_catalyst

**名称**: `extract_dual_atom_catalyst`

**描述**: 从向量数据库中搜索相关内容，使用 LLM 提取双原子催化剂合成的结构化信息。额外提取双原子间的距离（键长）信息。

**参数**:
- `collection_name` (string, required): 要搜索的集合名称
- `top_k` (integer, optional): 返回的结果数量，默认 10
- `output_file` (string, optional): 输出 JSON 文件路径

**返回值**: 包含 `success`, `results`, `has_active_site` 的字典

**输出格式**: JSON 结构包含:
- `reaction_steps`: 反应步数
- `step_N`: 各步骤详情
- `double_atom_catalyst_active_site`: 活性位点（含金属-金属距离）

---

### 5.6 search_vector_db

**名称**: `search_vector_db`

**描述**: 在向量数据库中搜索与查询文本相关的内容。支持单一集合搜索或全局搜索。

**参数**:
- `query` (string, required): 查询文本
- `collection_name` (string, optional): 集合名称，不指定则搜索所有集合
- `top_k` (integer, optional): 返回结果数量，默认 5
- `threshold` (number, optional): 相似度阈值，默认 0.7

**返回值**: 包含 `success`, `results`, `query` 的字典

---

### 5.7 list_qdrant_collections

**名称**: `list_qdrant_collections`

**描述**: 列出 Qdrant 数据库中所有的集合及其基本信息。

**参数**: 无

**返回值**: 包含 `success`, `collections`, `total_count` 的字典

---

### 5.8 delete_qdrant_collection

**名称**: `delete_qdrant_collection`

**描述**: 删除 Qdrant 数据库中的集合。支持按名称精确删除或按模式批量删除。

**参数**:
- `collection_name` (string, required): 集合名称或模式
- `pattern` (boolean, optional): 是否按模式匹配删除，默认 false

**返回值**: 包含 `success`, `deleted` 的字典

**警告**: 删除操作不可恢复

---

### 5.9 get_pdf_extraction_config

**名称**: `get_pdf_extraction_config`

**描述**: 获取 PDF 提取工具的当前配置信息。

**参数**: 无

**返回值**: 包含配置信息的字典:
- `qdrant_url`: Qdrant 服务地址
- `embedding_model`: 嵌入模型名称
- `chunk_size`: 分块大小
- `pdf_dir`: PDF 默认目录

---

## 6. 使用场景

### 6.1 场景一：完整 PDF 处理流程

用户输入:
```
请处理 /path/to/paper.pdf，提取其中的单原子催化剂合成信息
```

系统行为:
1. 识别为 PDF 数据提取任务
2. 调用 `pdf-extractor` SubAgent
3. SubAgent 执行:
   - `pdf_to_markdown(pdf_path="/path/to/paper.pdf")`
   - `ingest_to_qdrant(markdown_dir="...")`
   - `extract_single_atom_catalyst(collection_name="...")`
4. 返回结构化提取结果

### 6.2 场景二：查询已有数据

用户输入:
```
在已有的数据中搜索关于铜基催化剂的内容
```

系统行为:
1. 调用 `search_vector_db(query="铜基催化剂")`
2. 返回相关结果

### 6.3 场景三：批量处理

用户输入:
```
批量处理 paper/ 目录下的所有 PDF 文件
```

系统行为:
1. 调用 `pdf_to_markdown(pdf_path="paper/")`
2. 调用 `ingest_to_qdrant(markdown_dir="...")`
3. 返回处理统计

---

## 7. 风险与注意事项

1. **API 依赖**: 需要 OpenAI API 密钥进行嵌入和 LLM 提取
2. **服务依赖**: 需要 Qdrant 服务运行
3. **资源消耗**: 大量 PDF 处理可能消耗较多 API 配额
4. **数据安全**: 建议在生产环境使用本地部署的模型

---

## 8. 后续扩展

1. **支持更多文件格式**: Word, Excel, PPT
2. **离线模型支持**: 支持本地运行的嵌入模型
3. **增量更新**: 支持增量添加新文档
4. **多语言支持**: 扩展到其他语言的化学文献

---

## 9. 时间估算

| 阶段 | 预计时间 |
|-----|---------|
| 阶段一：工具函数封装 | 4-6 小时 |
| 阶段二：SubAgent 定义 | 2-3 小时 |
| 阶段三：系统集成 | 3-4 小时 |
| 阶段四：测试与验证 | 2-3 小时 |
| **总计** | **11-16 小时** |

---

## 10. 执行检查清单

- [ ] 创建 `pdf_extraction_tools.py`
- [ ] 实现所有工具函数
- [ ] 创建 `built_in_skills/pdf-extractor/` 目录
- [ ] 编写 `AGENTS.md`
- [ ] 修改 `agent.py` 集成工具
- [ ] 修改 `subagents.py` 加载内置 SubAgent
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 手动测试完整流程
- [ ] 更新文档
