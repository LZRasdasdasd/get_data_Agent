# 基于DeepAgents的论文数据提取Agent详细实现方案 (集成Qdrant)

## 一、项目概述

### 1.1 项目目标
从本地PDF论文中自动提取特定数据并输出为Excel格式，采用"PDF→大模型提取关键段落→分块→向量化→Qdrant向量数据库→提取成Excel"的流程。

### 1.2 核心优势
- 利用LLM的语义理解能力提升数据提取准确性
- 多Agent架构实现专业化分工
- 可扩展的技能系统和工具集
- 基于成熟的DeepAgents框架
- **集成Qdrant向量数据库**: 使用Docker部署的高性能向量存储，支持海量化文档检索

---

## 二、项目目录结构设计

```
paper_data_extraction/
├── .env.example                 # 环境变量模板
├── .gitignore                  # Git忽略文件
├── AGENTS.md                   # 主Agent身份和行为定义
├── README.md                   # 项目说明文档
├── pyproject.toml             # Python项目配置
├── docker-compose.yml           # Docker Compose配置（Qdrant）
├── agent.py                    # 主程序入口
├── subagents.yaml              # 子Agent配置文件
├── requirements.txt            # Python依赖列表
│
├── paper_extractor/            # 主Agent包
│   ├── __init__.py
│   ├── agent.py               # 主Agent创建和配置
│   ├── main.py                # 命令行入口
│   ├── config.py              # 配置管理
│   ├── utils.py               # 工具函数
│   │
│   ├── tools/                 # 工具集
│   │   ├── __init__.py
│   │   ├── pdf_tools.py      # PDF处理工具
│   │   ├── text_tools.py     # 文本处理工具
│   │   ├── table_tools.py    # 表格提取工具
│   │   ├── excel_tools.py    # Excel输出工具
│   │   └── vector_tools.py   # Qdrant向量工具
│   │
│   ├── skills/                # 技能系统
│   │   ├── __init__.py
│   │   ├── paragraph-extraction/   # 段落提取技能
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       └── paragraph_extractor.py
│   │   ├── table-structure/       # 表格结构化技能
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       └── table_structurer.py
│   │   ├── data-validation/       # 数据验证技能
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       └── data_validator.py
│   │   └── excel-export/          # Excel导出技能
│   │       ├── SKILL.md
│   │       └── scripts/
│   │           └── excel_exporter.py
│   │
│   ├── subagents/             # 子Agent系统
│   │   ├── __init__.py
│   │   ├── pdf_parser_agent.py      # PDF解析子Agent
│   │   ├── paragraph_extractor.py    # 段落提取子Agent
│   │   ├── table_structurer.py       # 表格结构化子Agent
│   │   ├── data_validator.py         # 数据验证子Agent
│   │   └── excel_exporter.py        # Excel导出子Agent
│   │
│   └── data/                 # 数据目录
│       ├── input/            # 输入PDF文件
│       ├── output/           # 输出Excel文件
│       └── temp/             # 临时文件
│
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── test_pdf_tools.py
│   ├── test_table_extraction.py
│   ├── test_qdrant_integration.py
│   ├── test_integration.py
│   └── sample_papers/      # 测试用PDF样本
│
└── docs/                    # 文档目录
    ├── architecture.md      # 架构设计文档
    ├── qdrant_setup.md     # Qdrant部署文档
    ├── api_reference.md    # API参考文档
    └── usage_examples.md   # 使用示例
```

---

## 三、核心组件详细实现计划

### 3.1 主Agent实现框架

#### 3.1.1 [`paper_extractor/agent.py`](paper_extractor/agent.py) - 主Agent创建函数

```python
# 核心功能框架
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model

def create_paper_extraction_agent():
    """
    创建论文数据提取主Agent
    
    功能：
    1. 初始化模型 (Claude Sonnet 4.5)
    2. 加载工具集 (PDF、表格、Excel、Qdrant向量工具)
    3. 配置技能系统 (段落提取、表格结构化、数据验证、Excel导出)
    4. 设置子Agent (PDF解析、段落提取、表格结构化、数据验证、Excel导出)
    5. 配置文件系统后端
    6. 返回配置完成的Agent实例
    """
    pass
```

#### 3.1.2 [`paper_extractor/main.py`](paper_extractor/main.py) - 命令行接口

```python
# 命令行接口框架
import argparse
from pathlib import Path

def main():
    """
    主入口函数
    
    功能：
    1. 解析命令行参数 (PDF文件路径、输出路径、配置选项)
    2. 加载环境变量
    3. 创建Agent实例
    4. 执行数据提取任务
    5. 处理错误和异常
    6. 显示结果统计
    """
    pass

if __name__ == "__main__":
    main()
```

### 3.2 工具集实现

#### 3.2.1 [`paper_extractor/tools/pdf_tools.py`](paper_extractor/tools/pdf_tools.py) - PDF处理工具

```python
# PDF工具函数框架
from langchain_core.tools import tool
import pdfplumber
import fitz
from pathlib import Path

@tool
def read_pdf_file(pdf_path: str) -> dict:
    """
    读取PDF文件并返回基本信息和页数
    
    参数：
        pdf_path: PDF文件路径
    
    返回：
        dict: 包含页数、文件大小、创建时间等基本信息
    """
    pass

@tool
def extract_pdf_text(pdf_path: str, pages: list = None) -> str:
    """
    从PDF中提取纯文本内容
    
    参数：
        pdf_path: PDF文件路径
        pages: 要提取的页码列表，None表示全部页面
    
    返回：
        str: 提取的文本内容
    """
    pass

@tool
def detect_pdf_structure(pdf_path: str) -> dict:
    """
    分析PDF结构，识别标题、段落、表格等元素
    
    参数：
        pdf_path: PDF文件路径
    
    返回：
        dict: 包含文档结构信息的字典
    """
    pass

@tool
def extract_pdf_pages_info(pdf_path: str) -> list:
    """
    获取PDF每一页的详细信息
    
    参数：
        pdf_path: PDF文件路径
    
    返回：
        list: 每页的详细信息列表
    """
    pass
```

#### 3.2.2 [`paper_extractor/tools/table_tools.py`](paper_extractor/tools/table_tools.py) - 表格处理工具

```python
# 表格工具函数框架
from langchain_core.tools import tool
import pdfplumber
import pandas as pd

@tool
def extract_tables_from_pdf(pdf_path: str) -> list:
    """
    从PDF中提取所有表格
    
    参数：
        pdf_path: PDF文件路径
    
    返回：
        list: 包含所有表格数据的列表
    """
    pass

@tool
def parse_table_structure(table_data: list) -> dict:
    """
    解析表格结构，识别表头、数据行、合并单元格等
    
    参数：
        table_data: 原始表格数据
    
    返回：
        dict: 结构化的表格信息
    """
    pass

@tool
def extract_table_context(pdf_text: str, table_location: dict) -> str:
    """
    提取表格的上下文信息（标题、说明等）
    
    参数：
        pdf_text: PDF全文
        table_location: 表格位置信息
    
    返回：
        str: 表格的上下文描述
    """
    pass

@tool
def merge_table_data(tables: list) -> dict:
    """
    合并多个表格的数据，处理跨页表格
    
    参数：
        tables: 表格列表
    
    返回：
        dict: 合并后的表格数据
    """
    pass
```

#### 3.2.3 [`paper_extractor/tools/excel_tools.py`](paper_extractor/tools/excel_tools.py) - Excel输出工具

```python
# Excel工具函数框架
from langchain_core.tools import tool
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

@tool
def create_excel_file(data: dict, output_path: str) -> str:
    """
    创建Excel文件并写入数据
    
    参数：
        data: 要写入的数据字典
        output_path: 输出文件路径
    
    返回：
        str: 生成的Excel文件路径
    """
    pass

@tool
def format_excel_sheet(excel_path: str, sheet_name: str, formatting: dict) -> bool:
    """
    格式化Excel工作表
    
    参数：
        excel_path: Excel文件路径
        sheet_name: 工作表名称
        formatting: 格式化配置
    
    返回：
        bool: 是否格式化成功
    """
    pass

@tool
def add_excel_metadata(excel_path: str, metadata: dict) -> bool:
    """
    为Excel文件添加元数据
    
    参数：
        excel_path: Excel文件路径
        metadata: 元数据字典
    
    返回：
        bool: 是否添加成功
    """
    pass

@tool
def export_structured_data(structured_data: dict, output_path: str) -> str:
    """
    导出结构化数据到Excel
    
    参数：
        structured_data: 结构化数据
        output_path: 输出路径
    
    返回：
        str: 导出的文件路径
    """
    pass
```

#### 3.2.4 [`paper_extractor/tools/vector_tools.py`](paper_extractor/tools/vector_tools.py) - Qdrant向量工具

```python
# Qdrant向量工具函数框架
from langchain_core.tools import tool
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant配置
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "paper_chunks")

@tool
def connect_qdrant() -> dict:
    """
    连接到Qdrant向量数据库
    
    参数：
        无
    
    返回：
        dict: 连接状态和集合信息
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        collections = client.get_collections()
        
        return {
            "status": "connected",
            "url": QDRANT_URL,
            "collections": [col.name for col in collections.collections],
            "message": "成功连接到Qdrant"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "连接Qdrant失败"
        }

@tool
def create_qdrant_collection(collection_name: str = COLLECTION_NAME) -> dict:
    """
    创建Qdrant集合（集合相当于数据库中的表）
    
    参数：
        collection_name: 集合名称，默认使用环境变量中的配置
    
    返回：
        dict: 创建结果
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        
        # 检查集合是否已存在
        collections = client.get_collections()
        existing_collections = [col.name for col in collections.collections]
        
        if collection_name in existing_collections:
            return {
                "status": "exists",
                "collection_name": collection_name,
                "message": f"集合 {collection_name} 已存在"
            }
        
        # 创建新集合
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # 1536维度适合OpenAI、Cohere等嵌入模型
        )
        
        return {
            "status": "created",
            "collection_name": collection_name,
            "message": f"成功创建集合 {collection_name}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "创建集合失败"
        }

@tool
def add_text_chunks(chunks: list, doc_id: str, collection_name: str = COLLECTION_NAME) -> bool:
    """
    将文本块添加到Qdrant向量数据库
    
    参数：
        chunks: 文本块列表，每个块包含text、embedding、metadata
        doc_id: 文档ID，用于标识来源文档
        collection_name: 集合名称
    
    返回：
        bool: 是否添加成功
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        
        # 准备点数据
        points = []
        for i, chunk in enumerate(chunks):
            point = PointStruct(
                id=f"{doc_id}_{i}",
                vector=chunk.get("embedding", []),
                payload={
                    "text": chunk.get("text", ""),
                    "doc_id": doc_id,
                    "chunk_id": i,
                    "metadata": chunk.get("metadata", {})
                }
            )
            points.append(point)
        
        # 批量插入
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return True
    except Exception as e:
        print(f"添加文本块到Qdrant失败: {e}")
        return False

@tool
def search_similar_chunks(query_embedding: list, n_results: int = 5, collection_name: str = COLLECTION_NAME) -> list:
    """
    在Qdrant中搜索相似的文本块
    
    参数：
        query_embedding: 查询向量嵌入
        n_results: 返回结果数量
        collection_name: 集合名称
    
    返回：
        list: 相似的文本块列表
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        
        # 执行向量搜索
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=n_results,
            score_threshold=0.7  # 相似度阈值
        )
        
        # 格式化结果
        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "doc_id": result.payload.get("doc_id", ""),
                "chunk_id": result.payload.get("chunk_id", -1),
                "metadata": result.payload.get("metadata", {}),
                "score": result.score
            })
        
        return results
    except Exception as e:
        print(f"搜索相似文本块失败: {e}")
        return []

@tool
def delete_document_from_qdrant(doc_id: str, collection_name: str = COLLECTION_NAME) -> bool:
    """
    从Qdrant中删除指定文档的所有文本块
    
    参数：
        doc_id: 文档ID
        collection_name: 集合名称
    
    返回：
        bool: 是否删除成功
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        
        # 删除所有匹配该doc_id的点
        client.delete(
            collection_name=collection_name,
            points_selector={
                "must": [
                    {
                        "key": "doc_id",
                        "match": {"value": doc_id}
                    }
                ]
            }
        )
        
        return True
    except Exception as e:
        print(f"删除文档从Qdrant失败: {e}")
        return False

@tool
def get_collection_info(collection_name: str = COLLECTION_NAME) -> dict:
    """
    获取Qdrant集合信息
    
    参数：
        collection_name: 集合名称
    
    返回：
        dict: 集合信息，包括点数量、向量配置等
    """
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        
        collection_info = client.get_collection(collection_name=collection_name)
        
        return {
            "status": "success",
            "collection_name": collection_name,
            "points_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "distance_metric": collection_info.config.params.vectors.distance.value,
            "created_at": collection_info.created_at
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "获取集合信息失败"
        }

@tool
def chunk_text_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """
    将文本分割成块，适合向量化处理
    
    参数：
        text: 要分割的文本
        chunk_size: 每个块的字符数
        overlap: 块之间的重叠字符数
    
    返回：
        list: 文本块列表，每个块包含text、start_pos、end_pos
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        chunks.append({
            "text": chunk,
            "start_pos": start,
            "end_pos": end,
            "chunk_index": len(chunks)
        })
        
        start = end - overlap
        
        # 避免无限循环
        if start >= text_length:
            break
    
    return chunks
```

### 3.3 技能系统实现

#### 3.3.1 段落提取技能

**文件结构：**
```
paper_extractor/skills/paragraph-extraction/
├── SKILL.md              # 技能定义文件
└── scripts/
    └── paragraph_extractor.py  # 技能实现
```

**[`SKILL.md`](paper_extractor/skills/paragraph-extraction/SKILL.md) 内容概要：**
```markdown
# 段落提取技能

## 目标
从论文中智能识别和提取包含关键数据的段落。

## 使用时机
当需要从论文中提取特定类型的数据段落时使用此技能。
特别结合Qdrant向量数据库进行智能搜索和检索。

## 工作流程
1. 使用LLM分析论文全文，识别数据密集型段落
2. 提取段落的上下文信息
3. 将段落分块并添加到Qdrant向量数据库
4. 标注段落的数据类型（表格数据、数值数据、文本数据）
5. 使用向量搜索找到相关段落
6. 返回结构化的段落信息

## Qdrant集成
- 将提取的文本分块存储到Qdrant
- 使用向量相似性搜索相关段落
- 支持跨文档的语义检索

## 输出格式
```json
{
  "paragraphs": [
    {
      "id": "para_001",
      "text": "段落内容",
      "page": 15,
      "data_type": "table|numeric|text",
      "context": "上下文描述",
      "relevance_score": 0.95,
      "qdrant_ids": ["chunk_1", "chunk_2"]
    }
  ]
}
```
```

**[`paragraph_extractor.py`](paper_extractor/skills/paragraph-extraction/scripts/paragraph_extractor.py) 实现：**
```python
from langchain_core.tools import tool
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

@tool
def extract_data_paragraphs(pdf_text: str) -> dict:
    """
    使用LLM提取包含数据的段落
    
    参数：
        pdf_text: PDF全文内容
    
    返回：
        dict: 包含数据段落的字典
    """
    # 实现LLM驱动的段落提取
    pass

@tool
def identify_table_paragraphs(pdf_text: str, tables: list) -> list:
    """
    识别包含表格的段落及其上下文
    
    参数：
        pdf_text: PDF全文
        tables: 检测到的表格列表
    
    返回：
        list: 表格相关的段落列表
    """
    pass
```

#### 3.3.2 表格结构化技能

**文件结构：**
```
paper_extractor/skills/table-structure/
├── SKILL.md              # 技能定义文件
└── scripts/
    └── table_structurer.py  # 技能实现
```

**[`SKILL.md`](paper_extractor/skills/table-structure/SKILL.md) 内容概要：**
```markdown
# 表格结构化技能

## 目标
将原始表格数据转换为结构化的数据格式。

## 使用时机
当需要处理提取的原始表格数据时使用此技能。

## 工作流程
1. 分析表格的结构和格式
2. 识别表头、数据行、合并单元格
3. 规范化列名和数据类型
4. 验证数据的完整性

## 输出格式
```json
{
  "tables": [
    {
      "id": "table_001",
      "title": "表格标题",
      "page": 10,
      "headers": ["列1", "列2", "列3"],
      "data": [
        ["值1", "值2", "值3"],
        ["值4", "值5", "值6"]
      ],
      "metadata": {
        "data_types": {
          "列1": "string",
          "列2": "number",
          "列3": "percentage"
        }
      }
    }
  ]
}
```
```

#### 3.3.3 数据验证技能

**文件结构：**
```
paper_extractor/skills/data-validation/
├── SKILL.md              # 技能定义文件
└── scripts/
    └── data_validator.py  # 技能实现
```

**[`SKILL.md`](paper_extractor/skills/data-validation/SKILL.md) 内容概要：**
```markdown
# 数据验证技能

## 目标
验证提取的数据的准确性和完整性。

## 使用时机
在数据提取完成后进行质量检查时使用此技能。

## 验证规则
1. 数据类型验证
2. 数值范围验证
3. 格式一致性验证
4. 重复数据检查
5. 数据完整性检查

## Qdrant一致性检查
- 验证Qdrant中的向量与提取数据的对应关系
- 检查索引完整性

## 输出格式
```json
{
  "validation_results": {
    "total_items": 100,
    "valid_items": 98,
    "invalid_items": 2,
    "issues": [
      {
        "item_id": "table_001_row_5",
        "issue_type": "invalid_format",
        "severity": "medium",
        "description": "百分比格式不正确"
      }
    ],
    "qdrant_consistency": {
      "indexed_chunks": 50,
      "missing_chunks": 0
    }
  }
}
```
```

#### 3.3.4 Excel导出技能

**文件结构：**
```
paper_extractor/skills/excel-export/
├── SKILL.md              # 技能定义文件
└── scripts/
    └── excel_exporter.py  # 技能实现
```

**[`SKILL.md`](paper_extractor/skills/excel-export/SKILL.md) 内容概要：**
```markdown
# Excel导出技能

## 目标
将结构化数据导出为格式化的Excel文件。

## 使用时机
当需要输出最终结果时使用此技能。

## 导出特点
1. 多工作表支持
2. 自动格式化
3. 数据类型保留
4. 元数据添加
5. 智能列宽调整

## 输出格式
- Excel文件 (.xlsx)
- 包含多个工作表
- 自动应用样式和格式
- 包含文档来源和处理信息
```

### 3.4 子Agent系统实现

#### 3.4.1 PDF解析子Agent

**[`paper_extractor/subagents/pdf_parser_agent.py`](paper_extractor/subagents/pdf_parser_agent.py)：**

```python
"""
PDF解析子Agent

职责：
1. 读取PDF文件
2. 提取文本内容
3. 识别文档结构
4. 检测表格位置
"""

PDF_PARSER_INSTRUCTIONS = """
你是PDF解析专家。你的任务是：
1. 精确读取PDF文件的所有内容
2. 识别文档结构（标题、段落、表格）
3. 提取表格的准确位置和内容
4. 保存页码和位置信息
5. 处理特殊字符和格式

可使用工具：
- read_pdf_file: 读取PDF基本信息
- extract_pdf_text: 提取文本内容
- detect_pdf_structure: 分析文档结构
- extract_tables_from_pdf: 提取表格
- extract_pdf_pages_info: 获取页面信息

注意事项：
- 保持原文档的结构
- 准确记录页码信息
- 特别注意表格的完整性
- 处理复杂的布局
"""

def create_pdf_parser_subagent():
    """
    创建PDF解析子Agent
    
    返回：
        dict: 子Agent配置
    """
    return {
        "name": "pdf-parser",
        "description": "专门负责PDF文件的解析和内容提取",
        "system_prompt": PDF_PARSER_INSTRUCTIONS,
        "tools": [
            "read_pdf_file",
            "extract_pdf_text", 
            "detect_pdf_structure",
            "extract_tables_from_pdf",
            "extract_pdf_pages_info"
        ]
    }
```

#### 3.4.2 段落提取子Agent

**[`paper_extractor/subagents/paragraph_extractor.py`](paper_extractor/subagents/paragraph_extractor.py)：**

```python
"""
段落提取子Agent

职责：
1. 分析PDF文本内容
2. 识别包含关键数据的段落
3. 提取表格的上下文信息
4. 使用Qdrant进行向量搜索
5. 评估段落相关性
"""

PARAGRAPH_EXTRACTOR_INSTRUCTIONS = """
你是段落提取专家。你的任务是：
1. 使用LLM的语义理解能力分析论文内容
2. 识别包含实验数据、结果、图表说明的段落
3. 提取表格的标题、说明文字等上下文
4. 将文本分块并存储到Qdrant向量数据库
5. 使用向量搜索找到相关的段落和数据
6. 评估每个段落的数据价值
7. 过滤无关信息

可使用工具：
- extract_data_paragraphs: 使用LLM提取数据段落
- identify_table_paragraphs: 识别表格相关段落
- chunk_text_text: 文本分块
- add_text_chunks: 添加到Qdrant向量数据库
- connect_qdrant: 连接Qdrant
- search_similar_chunks: 在Qdrant中搜索相似段落
- get_collection_info: 获取集合信息

注意事项：
- 优先包含实验结果部分
- 保留表格的完整上下文
- 提取图表的标题和说明
- 过滤理论性过强的内容
- 充分利用Qdrant的向量搜索能力
- 确保所有相关内容都被索引
"""

def create_paragraph_extractor_subagent():
    """
    创建段落提取子Agent
    
    返回：
        dict: 子Agent配置
    """
    return {
        "name": "paragraph-extractor",
        "description": "智能识别和提取包含数据的段落，集成Qdrant向量搜索",
        "system_prompt": PARAGRAPH_EXTRACTOR_INSTRUCTIONS,
        "tools": [
            "extract_data_paragraphs",
            "identify_table_paragraphs",
            "chunk_text_text",
            "add_text_chunks",
            "connect_qdrant",
            "search_similar_chunks",
            "get_collection_info"
        ]
    }
```

#### 3.4.3 表格结构化子Agent

**[`paper_extractor/subagents/table_structurer.py`](paper_extractor/subagents/table_structurer.py)：**

```python
"""
表格结构化子Agent

职责：
1. 解析原始表格数据
2. 识别表格结构
3. 标准化数据格式
4. 处理合并单元格
5. 添加数据元数据
"""

TABLE_STRUCTURER_INSTRUCTIONS = """
你是表格结构化专家。你的任务是：
1. 分析表格的复杂结构
2. 识别表头、数据行、合并单元格
3. 规范化列名和数据类型
4. 处理跨页表格的合并
5. 添加数据类型和单位信息

可使用工具：
- parse_table_structure: 解析表格结构
- extract_table_context: 提取表格上下文
- merge_table_data: 合并表格数据
- validate_data_type: 验证数据类型
- search_similar_chunks: 在Qdrant中搜索相关表格上下文

注意事项：
- 保持表格的语义完整性
- 正确处理科学计数法
- 保留单位和百分号
- 处理缺失值
- 标准化日期格式
- 利用Qdrant搜索表格的相关上下文
"""

def create_table_structurer_subagent():
    """
    创建表格结构化子Agent
    
    返回：
        dict: 子Agent配置
    """
    return {
        "name": "table-structurer",
        "description": "将原始表格数据转换为结构化格式，结合Qdrant上下文搜索",
        "system_prompt": TABLE_STRUCTURER_INSTRUCTIONS,
        "tools": [
            "parse_table_structure",
            "extract_table_context",
            "merge_table_data",
            "validate_data_type",
            "search_similar_chunks"
        ]
    }
```

#### 3.4.4 数据验证子Agent

**[`paper_extractor/subagents/data_validator.py`](paper_extractor/subagents/data_validator.py)：**

```python
"""
数据验证子Agent

职责：
1. 验证数据完整性
2. 检查数据一致性
3. 发现异常值
4. 验证Qdrant索引的完整性
5. 生成验证报告
"""

DATA_VALIDATOR_INSTRUCTIONS = """
你是数据验证专家。你的任务是：
1. 检查数据的类型和格式
2. 验证数值的合理范围
3. 检查数据的一致性
4. 识别重复或缺失的数据
5. 验证Qdrant向量数据库的索引完整性
6. 生成详细的验证报告

可使用工具：
- validate_data_type: 验证数据类型
- check_data_ranges: 检查数值范围
- find_duplicates: 查找重复数据
- check_completeness: 检查完整性
- get_collection_info: 获取Qdrant集合信息进行验证

注意事项：
- 遵循学术数据的验证标准
- 区分必要数据和可选数据
- 提供详细的错误描述
- 给出修复建议
- 确保Qdrant索引与提取数据的一致性
"""

def create_data_validator_subagent():
    """
    创建数据验证子Agent
    
    返回：
        dict: 子Agent配置
    """
    return {
        "name": "data-validator",
        "description": "验证提取数据的准确性和完整性，包括Qdrant索引一致性",
        "system_prompt": DATA_VALIDATOR_INSTRUCTIONS,
        "tools": [
            "validate_data_type",
            "check_data_ranges",
            "find_duplicates",
            "check_completeness",
            "get_collection_info"
        ]
    }
```

#### 3.4.5 Excel导出子Agent

**[`paper_extractor/subagents/excel_exporter.py`](paper_extractor/subagents/excel_exporter.py)：**

```python
"""
Excel导出子Agent

职责：
1. 创建Excel文件
2. 组织数据结构
3. 应用格式化
4. 添加元数据
5. 生成输出文件
"""

EXCEL_EXPORTER_INSTRUCTIONS = """
你是Excel导出专家。你的任务是：
1. 创建结构化的Excel工作簿
2. 将数据组织到合适的工作表中
3. 应用适当的格式和样式
4. 添加数据和文档的元信息
5. 确保文件的可读性

可使用工具：
- create_excel_file: 创建Excel文件
- format_excel_sheet: 格式化工作表
- add_excel_metadata: 添加元数据
- export_structured_data: 导出结构化数据
- get_collection_info: 获取Qdrant统计信息用于元数据

注意事项：
- 使用清晰的工作表命名
- 添加适当的标题和说明
- 保持数据类型的一致性
- 添加文档来源信息
- 格式化数值和日期
- 包含Qdrant索引统计信息
"""

def create_excel_exporter_subagent():
    """
    创建Excel导出子Agent
    
    返回：
        dict: 子Agent配置
    """
    return {
        "name": "excel-exporter",
        "description": "将结构化数据导出为Excel文件，包含Qdrant统计信息",
        "system_prompt": EXCEL_EXPORTER_INSTRUCTIONS,
        "tools": [
            "create_excel_file",
            "format_excel_sheet",
            "add_excel_metadata",
            "export_structured_data",
            "get_collection_info"
        ]
    }
```

### 3.5 配置和主程序实现

#### 3.5.1 [`paper_extractor/config.py`](paper_extractor/config.py) - 配置管理

```python
"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """配置类"""
    
    def __init__(self):
        """初始化配置"""
        load_dotenv()
        
        # 基础路径
        self.base_dir = Path(__file__).parent.absolute()
        self.data_dir = self.base_dir / "data"
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.temp_dir = self.data_dir / "temp"
        
        # 创建必要的目录
        self._create_directories()
        
        # 模型配置
        self.model_name = os.getenv("MODEL_NAME", "anthropic:claude-sonnet-4-5-20250929")
        self.temperature = float(os.getenv("TEMPERATURE", "0.0"))
        
        # Qdrant配置
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "paper_chunks")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        # Excel导出配置
        self.default_excel_format = os.getenv("EXCEL_FORMAT", "xlsx")
        
    def _create_directories(self):
        """创建必要的目录"""
        for directory in [self.input_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def api_key(self) -> str:
        """获取API密钥"""
        return os.getenv("ANTHROPIC_API_KEY", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "qdrant_url": self.qdrant_url,
            "qdrant_collection": self.qdrant_collection,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "base_dir": str(self.base_dir),
            "data_dir": str(self.data_dir),
        }

# 全局配置实例
config = Config()
```

#### 3.5.2 [`paper_extractor/utils.py`](paper_extractor/utils.py) - 工具函数

```python
"""
工具函数模块
"""
import logging
from typing import List, Dict, Any
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    设置日志
    
    参数：
        log_level: 日志级别
    
    返回：
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger("paper_extract")
    logger.setLevel(getattr(logging, log_level))
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def validate_pdf_path(pdf_path: str) -> Path:
    """
    验证PDF文件路径
    
    参数：
        pdf_path: PDF文件路径
    
    返回：
        Path: 验证后的路径对象
    
    抛出：
        FileNotFoundError: 文件不存在
        ValueError: 文件不是PDF
    """
    path = Path(pdf_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"文件不是PDF格式: {pdf_path}")
    
    return path

def clean_text(text: str) -> str:
    """
    清理文本
    
    参数：
        text: 原始文本
    
    返回：
        str: 清理后的文本
    """
    # 移除多余的空格
    text = " ".join(text.split())
    
    # 移除特殊字符
    text = text.replace("\x00", "")
    
    return text.strip()

def generate_summary(results: Dict[str, Any]) -> str:
    """
    生成结果摘要
    
    参数：
        results: 处理结果
    
    返回：
        str: 摘要文本
    """
    summary_parts = []
    
    if "tables" in results:
        table_count = len(results["tables"])
        summary_parts.append(f"提取了 {table_count} 个表格")
    
    if "validation" in results:
        validation = results["validation"]
        summary_parts.append(f"验证通过率: {validation.get('success_rate', 0):.1%}")
    
    if "qdrant_stats" in results:
        stats = results["qdrant_stats"]
        summary_parts.append(f"Qdrant索引: {stats.get('points_count', 0)} 个向量")
    
    if "output" in results:
        output_path = results["output"]
        summary_parts.append(f"输出文件: {output_path}")
    
    return " | ".join(summary_parts) if summary_parts else "处理完成"
```

#### 3.5.3 [`paper_extractor/agent.py`](paper_extractor/agent.py) - 主Agent创建

```python
"""
主Agent创建模块
"""
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model

from .config import config
from .tools import *
from .subagents import *
from .utils import setup_logging

logger = setup_logging()

def create_paper_extraction_agent():
    """
    创建论文数据提取主Agent
    
    返回：
        Agent: 配置完成的Agent实例
    """
    logger.info("开始创建论文数据提取Agent...")
    
    # 初始化模型
    logger.info(f"初始化模型: {config.model_name}")
    model = init_chat_model(
        model=config.model_name,
        temperature=config.temperature
    )
    
    # 收集所有工具
    logger.info("加载工具集...")
    tools = get_all_tools()
    
    # 加载技能
    logger.info("加载技能系统...")
    skills_dir = Path(__file__).parent / "skills"
    memory_files = [
        Path(__file__).parent / "AGENTS.md"
    ]
    
    # 创建子Agent
    logger.info("创建子Agent系统...")
    subagents = [
        create_pdf_parser_subagent(),
        create_paragraph_extractor_subagent(),
        create_table_structurer_subagent(),
        create_data_validator_subagent(),
        create_excel_exporter_subagent()
    ]
    
    # 配置文件系统后端
    logger.info("配置文件系统后端...")
    backend = FilesystemBackend(root_dir=str(config.base_dir))
    
    # 创建Agent
    logger.info("创建主Agent...")
    agent = create_deep_agent(
        model=model,
        tools=tools,
        skills=[str(skills_dir)],
        memory=memory_files,
        subagents=subagents,
        backend=backend
    )
    
    logger.info("Agent创建完成！")
    return agent

def get_all_tools():
    """
    获取所有工具
    
    返回：
        list: 所有工具的列表
    """
    from .tools.pdf_tools import (
        read_pdf_file,
        extract_pdf_text,
        detect_pdf_structure,
        extract_pdf_pages_info
    )
    from .tools.table_tools import (
        extract_tables_from_pdf,
        parse_table_structure,
        extract_table_context,
        merge_table_data
    )
    from .tools.excel_tools import (
        create_excel_file,
        format_excel_sheet,
        add_excel_metadata,
        export_structured_data
    )
    from .tools.vector_tools import (
        connect_qdrant,
        create_qdrant_collection,
        add_text_chunks,
        search_similar_chunks,
        delete_document_from_qdrant,
        get_collection_info,
        chunk_text_text
    )
    
    return [
        read_pdf_file,
        extract_pdf_text,
        detect_pdf_structure,
        extract_pdf_pages_info,
        extract_tables_from_pdf,
        parse_table_structure,
        extract_table_context,
        merge_table_data,
        create_excel_file,
        format_excel_sheet,
        add_excel_metadata,
        export_structured_data,
        connect_qdrant,
        create_qdrant_collection,
        add_text_chunks,
        search_similar_chunks,
        delete_document_from_qdrant,
        get_collection_info,
        chunk_text_text
    ]
```

#### 3.5.4 [`paper_extractor/main.py`](paper_extractor/main.py) - 命令行入口

```python
"""
主程序入口
"""
import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from .agent import create_paper_extraction_agent
from .config import config
from .utils import validate_pdf_path, generate_summary, setup_logging

console = Console()
logger = setup_logging()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="论文数据提取Agent - 从PDF论文中提取数据并导出为Excel (集成Qdrant)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py papers/sample.pdf                    # 使用默认输出路径
  python main.py papers/sample.pdf --output results/    # 指定输出目录
  python main.py papers/sample.pdf --verbose            # 显示详细日志
  python main.py papers/sample.pdf --validate           # 仅验证不提取
        """
    )
    
    parser.add_argument(
        "pdf_path",
        type=str,
        help="PDF论文文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径（默认：data/output/<filename>.xlsx）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅验证PDF文件，不进行提取"
    )
    
    parser.add_argument(
        "--check-qdrant",
        action="store_true",
        help="检查Qdrant连接和集合状态"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel("DEBUG")
    
    try:
        # 检查Qdrant连接（如果指定）
        if args.check_qdrant:
            from .tools.vector_tools import connect_qdrant, get_collection_info
            console.print(Panel(f"[bold cyan]检查Qdrant连接...[/bold cyan]"))
            
            conn_result = connect_qdrant()
            console.print(f"✓ Qdrant连接状态: {conn_result['status']}")
            console.print(f"✓ 服务地址: {conn_result['url']}")
            
            if conn_result['status'] == 'connected':
                collection_info = get_collection_info()
                console.print(f"✓ 集合信息: {collection_info['collection_name']}")
                console.print(f"✓ 向量数量: {collection_info.get('points_count', 0)}")
            else:
                console.print(f"✗ 连接失败: {conn_result.get('error', 'Unknown error')}")
            
            return
        
        # 验证PDF路径
        console.print(Panel(f"[bold cyan]开始处理PDF文件[/bold cyan]"))
        pdf_path = validate_pdf_path(args.pdf_path)
        console.print(f"✓ PDF文件验证通过: {pdf_path.name}")
        
        # 创建Agent
        console.print("\n[dim]初始化Agent...[/dim]")
        agent = create_paper_extraction_agent()
        console.print("✓ Agent初始化完成")
        
        # 如果只验证，则结束
        if args.validate_only:
            console.print("\n[bold green]验证完成！文件可以正常处理。[/bold green]")
            return
        
        # 确定输出路径
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = config.output_dir / f"{pdf_path.stem}_extracted.xlsx"
        
        # 显示处理进度
        with Progress() as progress:
            task1 = progress.add_task("[cyan]提取PDF内容...", total=100)
            progress.update(task1, advance=20)
            
            # 执行数据提取
            console.print("\n[dim]执行数据提取...[/dim]")
            result = agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"""
请从PDF文件 '{pdf_path}' 中提取所有数据表格和信息。

任务步骤：
1. 解析PDF文件结构和内容
2. 识别包含数据的段落并分块
3. 将文本块添加到Qdrant向量数据库
4. 使用向量搜索找到相关段落和表格上下文
5. 提取表格数据并结构化
6. 验证数据的准确性和Qdrant索引一致性
7. 将结果导出为Excel文件到 '{output_path}'

Qdrant配置：
- 服务地址: {config.qdrant_url}
- 集合名称: {config.qdrant_collection}
- 块大小: {config.chunk_size}
- 重叠度: {config.chunk_overlap}

请按照以下要求：
- 准确提取所有表格数据
- 保留表格的上下文信息
- 充分利用Qdrant的向量搜索能力
- 验证数据的完整性
- 生成格式化的Excel文件
- 提供详细的处理报告
                    """
                }]
            })
            
            progress.update(task1, advance=50)
            console.print("✓ 数据提取完成")
            
            task2 = progress.add_task("[cyan]生成Excel文件...", total=100)
            progress.update(task2, advance=100)
            console.print("✓ Excel文件生成完成")
        
        # 显示结果摘要
        try:
            final_message = result["messages"][-1]
            result_text = (
                final_message.content if hasattr(final_message, 'content') 
                else str(final_message)
            )
            
            console.print(Panel(
                f"[bold green]处理完成！[/bold green]\n\n{result_text}",
                border_style="green"
            ))
            
            if output_path.exists():
                console.print(f"\n✓ 输出文件: [blue]{output_path.absolute()}[/blue]")
                console.print(f"✓ 文件大小: [blue]{output_path.stat().st_size / 1024:.1f} KB[/blue]")
        
        except Exception as e:
            console.print(f"\n[yellow]警告: {e}[/yellow]")
            console.print(f"\n✓ 处理完成，请检查输出目录: {config.output_dir}")
    
    except FileNotFoundError as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]")
        sys.exit(1)
    
    except ValueError as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"\n[bold red]意外错误: {e}[/bold red]")
        logger.exception("处理过程中发生错误")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 四、文件级别的改造步骤

### 阶段一：基础框架搭建（第1周）

#### 步骤1.1：创建项目目录结构
```bash
# 执行命令
cd e:/get_data_Agent
mkdir -p paper_data_extraction/paper_extractor/{tools,skills,subagents,data/{input,output,temp}}
mkdir -p paper_data_extraction/{tests/sample_papers,docs}
cd paper_data_extraction
```

#### 步骤1.2：创建基础配置文件
1. 创建[`pyproject.toml`](pyproject.toml)
2. 创建[`.env.example`](.env.example)
3. 创建[`requirements.txt`](requirements.txt)
4. 创建[`docker-compose.yml`](docker-compose.yml)
5. 创建[`README.md`](README.md)

**关键文件内容：**

[`pyproject.toml`](pyproject.toml)：
```toml
[project]
name = "paper-data-extraction"
version = "0.1.0"
description = "基于DeepAgents的论文数据提取系统 (集成Qdrant向量数据库)"
requires-python = ">=3.10"
dependencies = [
    "deepagents>=0.1.0",
    "langchain>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "langchain-core>=0.3.0",
    "langchain-qdrant>=0.1.0",
    "pdfplumber>=0.11.0",
    "PyMuPDF>=1.24.0",
    "pandas>=2.2.0",
    "openpyxl>=3.1.0",
    "qdrant-client>=1.7.0",
    "python-dotenv>=1.0.0",
    "rich>=13.7.0",
    "tabula-py>=2.9.0",
    "camelot-py[cv]>=0.11.0",
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q"
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

[`.env.example`](.env.example)：
```bash
# API配置
ANTHROPIC_API_KEY=your-api-key-here
MODEL_NAME=anthropic:claude-sonnet-4-5-20250929
TEMPERATURE=0.0

# Qdrant配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=paper_chunks

# 向量化配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 输出配置
EXCEL_FORMAT=xlsx

# 日志配置
LOG_LEVEL=INFO
```

[`docker-compose.yml`](docker-compose.yml)：
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: pdf-paper-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333
    restart: unless-stopped

volumes:
  qdrant_storage:
    driver: local
```

#### 步骤1.3：创建核心配置模块
1. 创建[`paper_extractor/__init__.py`](paper_extractor/__init__.py)
2. 创建[`paper_extractor/config.py`](paper_extractor/config.py)
3. 创建[`paper_extractor/utils.py`](paper_extractor/utils.py)

### 阶段二：工具系统开发（第2周）

#### 步骤2.1：PDF处理工具
1. 创建[`paper_extractor/tools/__init__.py`](paper_extractor/tools/__init__.py)
2. 实现[`paper_extractor/tools/pdf_tools.py`](paper_extractor/tools/pdf_tools.py)
   - [`read_pdf_file()`](paper_extractor/tools/pdf_tools.py:read_pdf_file) 函数
   - [`extract_pdf_text()`](paper_extractor/tools/pdf_tools.py:extract_pdf_text) 函数
   - [`detect_pdf_structure()`](paper_extractor/tools/pdf_tools.py:detect_pdf_structure) 函数
   - [`extract_pdf_pages_info()`](paper_extractor/tools/pdf_tools.py:extract_pdf_pages_info) 函数

#### 步骤2.2：表格处理工具
1. 实现[`paper_extractor/tools/table_tools.py`](paper_extractor/tools/table_tools.py)
   - [`extract_tables_from_pdf()`](paper_extractor/tools/table_tools.py:extract_tables_from_pdf) 函数
   - [`parse_table_structure()`](paper_extractor/tools/table_tools.py:parse_table_structure) 函数
   - [`extract_table_context()`](paper_extractor/tools/table_tools.py:extract_table_context) 函数
   - [`merge_table_data()`](paper_extractor/tools/table_tools.py:merge_table_data) 函数

#### 步骤2.3：Excel输出工具
1. 实现[`paper_extractor/tools/excel_tools.py`](paper_extractor/tools/excel_tools.py)
   - [`create_excel_file()`](paper_extractor/tools/excel_tools.py:create_excel_file) 函数
   - [`format_excel_sheet()`](paper_extractor/tools/excel_tools.py:format_excel_sheet) 函数
   - [`add_excel_metadata()`](paper_extractor/tools/excel_tools.py:add_excel_metadata) 函数
   - [`export_structured_data()`](paper_extractor/tools/excel_tools.py:export_structured_data) 函数

#### 步骤2.4：Qdrant向量工具
1. 实现[`paper_extractor/tools/vector_tools.py`](paper_extractor/tools/vector_tools.py)
   - [`connect_qdrant()`](paper_extractor/tools/vector_tools.py:connect_qdrant) 函数
   - [`create_qdrant_collection()`](paper_extractor/tools/vector_tools.py:create_qdrant_collection) 函数
   - [`add_text_chunks()`](paper_extractor/tools/vector_tools.py:add_text_chunks) 函数
   - [`search_similar_chunks()`](paper_extractor/tools/vector_tools.py:search_similar_chunks) 函数
   - [`delete_document_from_qdrant()`](paper_extractor/tools/vector_tools.py:delete_document_from_qdrant) 函数
   - [`get_collection_info()`](paper_extractor/tools/vector_tools.py:get_collection_info) 函数
   - [`chunk_text_text()`](paper_extractor/tools/vector_tools.py:chunk_text_text) 函数

### 阶段三：技能系统开发（第3周）

#### 步骤3.1：段落提取技能
1. 创建目录：`paper_extractor/skills/paragraph-extraction/scripts/`
2. 创建[`paper_extractor/skills/paragraph-extraction/SKILL.md`](paper_extractor/skills/paragraph-extraction/SKILL.md)
3. 实现[`paper_extractor/skills/paragraph-extraction/scripts/paragraph_extractor.py`](paper_extractor/skills/paragraph-extraction/scripts/paragraph_extractor.py)

#### 步骤3.2：表格结构化技能
1. 创建目录：`paper_extractor/skills/table-structure/scripts/`
2. 创建[`paper_extractor/skills/table-structure/SKILL.md`](paper_extractor/skills/table-structure/SKILL.md)
3. 实现相关的表格结构化工具函数

#### 步骤3.3：数据验证技能
1. 创建目录：`paper_extractor/skills/data-validation/scripts/`
2. 创建[`paper_extractor/skills/data-validation/SKILL.md`](paper_extractor/skills/data-validation/SKILL.md)
3. 实现数据验证工具函数

#### 步骤3.4：Excel导出技能
1. 创建目录：`paper_extractor/skills/excel-export/scripts/`
2. 创建[`paper_extractor/skills/excel-export/SKILL.md`](paper_extractor/skills/excel-export/SKILL.md)
3. 实现Excel导出相关函数

### 阶段四：子Agent系统开发（第4周）

#### 步骤4.1：PDF解析子Agent
1. 创建[`paper_extractor/subagents/__init__.py`](paper_extractor/subagents/__init__.py)
2. 实现[`paper_extractor/subagents/pdf_parser_agent.py`](paper_extractor/subagents/pdf_parser_agent.py)
3. 定义PDF_PARSER_INSTRUCTIONS常量
4. 创建create_pdf_parser_subagent()函数

#### 步骤4.2：段落提取子Agent
1. 实现[`paper_extractor/subagents/paragraph_extractor.py`](paper_extractor/subagents/paragraph_extractor.py)
2. 定义PARAGRAPH_EXTRACTOR_INSTRUCTIONS常量（包含Qdrant集成说明）
3. 创建create_paragraph_extractor_subagent()函数

#### 步骤4.3：表格结构化子Agent
1. 实现[`paper_extractor/subagents/table_structurer.py`](paper_extractor/subagents/table_structurer.py)
2. 定义TABLE_STRUCTURER_INSTRUCTIONS常量
3. 创建create_table_structurer_subagent()函数

#### 步骤4.4：数据验证子Agent
1. 实现[`paper_extractor/subagents/data_validator.py`](paper_extractor/subagents/data_validator.py)
2. 定义DATA_VALIDATOR_INSTRUCTIONS常量
3. 创建create_data_validator_subagent()函数

#### 步骤4.5：Excel导出子Agent
1. 实现[`paper_extractor/subagents/excel_exporter.py`](paper_extractor/subagents/excel_exporter.py)
2. 定义EXCEL_EXPORTER_INSTRUCTIONS常量
3. 创建create_excel_exporter_subagent()函数

### 阶段五：主Agent和接口实现（第5周）

#### 步骤5.1：创建主Agent
1. 创建[`paper_extractor/agent.py`](paper_extractor/agent.py)
2. 实现create_paper_extraction_agent()函数
3. 实现get_all_tools()函数进行工具整合

#### 步骤5.2：实现主程序
1. 创建[`paper_extractor/main.py`](paper_extractor/main.py)
2. 实现命令行参数解析
3. 实现主处理流程
4. 添加错误处理和日志

#### 步骤5.3：创建Agent身份文件
1. 创建[`AGENTS.md`](AGENTS.md)
2. 定义Agent的行为和目标

### 阶段六：测试和优化（第6周）

#### 步骤6.1：创建测试文件
1. 创建[`tests/__init__.py`](tests/__init__.py)
2. 创建[`tests/test_pdf_tools.py`](tests/test_pdf_tools.py)
3. 创建[`tests/test_table_extraction.py`](tests/test_table_extraction.py)
4. 创建[`tests/test_qdrant_integration.py`](tests/test_qdrant_integration.py)
5. 创建[`tests/test_integration.py`](tests/test_integration.py)

#### 步骤6.2：准备测试数据
1. 在[`tests/sample_papers/`](tests/sample_papers/)中添加各种类型的PDF样本
2. 准备简单表格的PDF
3. 准备复杂表格的PDF
4. 准备跨页表格的PDF
5. 准备混合格式的PDF

#### 步骤6.3：执行测试
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Qdrant
docker-compose up -d

# 配置环境变量
cp .env.example .env
# 编辑.env添加API密钥

# 运行测试
pytest tests/

# 测试特定文件
pytest tests/test_qdrant_integration.py -v

# 运行集成测试
pytest tests/test_integration.py -v
```

#### 步骤6.4：性能优化
1. 分析性能瓶颈
2. 优化LLM调用频次
3. 实现Qdrant缓存机制
4. 优化向量搜索参数

### 阶段七：文档和发布（第7周）

#### 步骤7.1：创建文档
1. 创建[`docs/architecture.md`](docs/architecture.md) - 架构设计文档
2. 创建[`docs/qdrant_setup.md`](docs/qdrant_setup.md) - Qdrant部署文档
3. 创建[`docs/api_reference.md`](docs/api_reference.md) - API参考文档
4. 创建[`docs/usage_examples.md`](docs/usage_examples.md) - 使用示例

#### 步骤7.2：完善README
1. 添加功能介绍
2. 添加Qdrant部署说明
3. 添加安装说明
4. 添加使用示例
5. 添加配置说明
6. 添加故障排除

---

## 五、Docker部署配置

### 5.1 Qdrant Docker部署

#### 完整的Docker Compose配置
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: pdf-paper-qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readyz"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # 可选：添加Qdrant Web仪表板
  qdrant-dashboard:
    image: qdrant/qdrant-dashboard
    container_name: qdrant-dashboard
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - qdrant
    restart: unless-stopped

volumes:
  qdrant_storage:
    driver: local
```

#### 部署命令
```bash
# 启动Qdrant
docker-compose up -d

# 查看日志
docker-compose logs -f qdrant

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart qdrant

# 停止服务
docker-compose down

# 完全清理（包括数据卷）
docker-compose down -v
```

### 5.2 Qdrant Web仪表板

如果启用了Qdrant Dashboard，可以通过以下方式访问：

1. **默认访问地址**: http://localhost:8000
2. **配置连接**:
   - Qdrant URL: `http://localhost:6333`
   - API Key: 留空（如果没有配置认证）

3. **主要功能**:
   - 查看所有集合
   - 浏览向量数据
   - 执行向量搜索
   - 监控性能指标
   - 管理索引

---

## 六、使用示例

### 6.1 基本使用
```bash
# 进入项目目录
cd e:/get_data_Agent/paper_data_extraction

# 启动Qdrant
docker-compose up -d

# 基本使用
python paper_extractor/main.py data/input/sample_paper.pdf

# 指定输出路径
python paper_extractor/main.py data/input/sample_paper.pdf --output data/output/results.xlsx

# 显示详细日志
python paper_extractor/main.py data/input/sample_paper.pdf --verbose

# 检查Qdrant连接
python paper_extractor/main.py --check-qdrant
```

### 6.2 批量处理
```bash
# 批量处理多个PDF文件
for file in data/input/*.pdf; do
    python paper_extractor/main.py "$file" --output data/output/$(basename "$file" .pdf)_extracted.xlsx
done
```

### 6.3 开发模式
```bash
# 设置环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 运行开发服务器
python -m paper_extractor.main
```

### 6.4 Qdrant管理
```bash
# 连接到Qdrant容器
docker exec -it pdf-paper-qdrant bash

# 查看集合
curl http://localhost:6333/collections

# 查看集合信息
curl http://localhost:6333/collections/paper_chunks

# 删除集合
curl -X DELETE http://localhost:6333/collections/paper_chunks
```

---

## 七、技术要点总结

### 7.1 核心优势
1. **智能化**: 利用LLM的语义理解能力
2. **模块化**: 清晰的工具、技能、子Agent分工
3. **可扩展**: 易于添加新功能和工具
4. **可靠性**: 完善的错误处理和验证机制
5. **高性能**: 集成Qdrant实现高效向量搜索

### 7.2 关键技术
1. **PDF解析**: pdfplumber + PyMuPDF双重保障
2. **表格提取**: 专门优化的表格识别算法
3. **语义理解**: LLM驱动的段落提取
4. **Qdrant向量存储**: 基于Docker的高性能向量数据库，支持海量化文档检索
5. **数据验证**: 多层面的质量检查
6. **Docker部署**: 便于扩展和维护的容器化部署

### 7.3 性能优化
1. **结果缓存**: 避免重复处理
2. **并发处理**: 充分利用系统资源
3. **智能分块**: 优化Qdrant向量数据库性能
4. **延迟加载**: 按需加载大型资源
5. **向量索引优化**: 利用Qdrant的HNSW索引

---

## 八、后续扩展方向

### 8.1 功能扩展
1. 支持更多文档格式（Word、PPT）
2. 添加图片表格识别（OCR）
3. 支持数据可视化和分析
4. 添加数据标准化和转换功能
5. 集成更多嵌入模型

### 8.2 性能优化
1. 实现GPU加速（包括向量搜索）
2. 添加分布式处理支持
3. 优化内存使用
4. 实现增量处理
5. Qdrant集群部署

### 8.3 用户界面
1. 添加Web界面
2. 开发桌面应用
3. 集成到现有系统中
4. 提供API接口
5. 实时处理状态监控

---

这个方案提供了一个完整的、可实施的论文数据提取Agent系统实现计划，基于DeepAgents框架，集成了Qdrant向量数据库进行高效检索。方案充分利用了Docker的优势，便于部署和扩展，同时针对PDF数据提取的需求进行了专门优化。涵盖了从基础架构到具体实现的各个层面，包含Qdrant的完整部署和管理说明，可以作为详细的开发指南使用。