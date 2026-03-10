"""
PDF 数据提取工具注册模块

该模块从 pdf_qdrant_mvp/src/ 目录导入已经添加了 Agent 可识别 docstring 的函数，
并将它们注册为 deepagents 工具。

工具列表：
- convert_pdf_to_markdown: PDF 转 Markdown
- chunk_markdown: Markdown 文本分块
- QdrantManager.search: 向量数据库语义搜索
- CatalystInfoExtractor.search_related_content: 单原子催化剂信息搜索
- query_and_extract: 双原子催化剂合成信息提取
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable

from rich.markup import escape

# 添加 pdf_qdrant_mvp/src 目录到 Python 路径
_pdf_qdrant_src = Path(__file__).parent / "pdf_qdrant_mvp" / "src"
if str(_pdf_qdrant_src) not in sys.path:
    sys.path.insert(0, str(_pdf_qdrant_src))


# ============================================
# 延迟导入工具函数（避免循环导入和模块级初始化问题）
# ============================================

# 使用延迟导入模式，只有在实际调用时才加载模块
# 这样可以避免 ingest_markdown.py 中的全局初始化代码立即执行

def _import_pdf_to_markdown():
    """延迟导入 PDF 转 Markdown 工具"""
    from pdf_to_markdown import convert_pdf_to_markdown
    return convert_pdf_to_markdown


def _import_ingest_markdown():
    """延迟导入 Markdown 分块工具"""
    from ingest_markdown import (
        chunk_markdown,
        get_markdown_files,
        read_markdown_file,
        sanitize_collection_name,
    )
    return {
        "chunk_markdown": chunk_markdown,
        "get_markdown_files": get_markdown_files,
        "read_markdown_file": read_markdown_file,
        "sanitize_collection_name": sanitize_collection_name,
    }


def _import_vector_tools():
    """延迟导入 Qdrant 向量数据库管理器"""
    from vector_tools import QdrantManager
    return QdrantManager


def _import_extract_catalyst_info():
    """延迟导入单原子催化剂信息提取"""
    from extract_catalyst_info import CatalystInfoExtractor
    return CatalystInfoExtractor


def _import_extract_dac_synthesis():
    """延迟导入双原子催化剂合成信息提取"""
    from extract_dac_synthesis import query_and_extract
    return query_and_extract


def _import_delete_collections():
    """延迟导入集合管理工具"""
    from delete_collections import delete_collections_by_pattern
    return delete_collections_by_pattern


# ============================================
# 包装函数（提供稳定的对外接口）
# ============================================

def convert_pdf_to_markdown(pdf_path: str, output_dir: str = None) -> dict:
    """
    将 PDF 文件转换为 Markdown 格式。
    
    该工具使用 marker 库将 PDF 文档转换为结构化的 Markdown 文本，
    保留标题层级、表格结构和基本格式。适用于科学论文的文本提取。
    
    Use this tool when you need to:
    - Convert PDF documents to readable Markdown text
    - Extract text content from scientific papers
    - Prepare PDF content for semantic chunking
    
    Args:
        pdf_path: PDF 文件的完整路径
        output_dir: 输出目录（可选，默认与 PDF 同目录）
        
    Returns:
        dict: 包含转换结果的字典：
            - success (bool): 是否成功
            - markdown_path (str): 生成的 Markdown 文件路径
            - text (str): 提取的文本内容（如果成功）
            - error (str): 错误信息（如果失败）
    """
    func = _import_pdf_to_markdown()
    return func(pdf_path, output_dir)


def chunk_markdown(text: str, chunk_size: int = 1000, overlap: int = 200, min_chunk_size: int = 500) -> list:
    """
    将 Markdown 文本智能分割成适合向量嵌入的文本块。
    
    该工具用于将长文本分割成适当大小的块，以便进行向量嵌入和语义搜索。
    采用智能分块策略：在句号位置分割、合并小段落、保留标题上下文。
    
    Use this tool when you need to:
    - Split long Markdown documents into chunks for vector embedding
    - Prepare text data for semantic search in Qdrant
    
    Args:
        text: 要分割的 Markdown 文本
        chunk_size: 目标块大小（字符数），默认 1000
        overlap: 块之间的重叠字符数，默认 200
        min_chunk_size: 最小块大小，默认 500
        
    Returns:
        list: 文本块列表，每个块是包含以下字段的字典：
            - text (str): 文本内容
            - char_count (int): 字符数
            - chunk_index (int): 块索引
    """
    funcs = _import_ingest_markdown()
    return funcs["chunk_markdown"](text, chunk_size, overlap, min_chunk_size)


def get_markdown_files(md_dir: str) -> list:
    """
    获取目录下所有 Markdown 文件。
    
    Args:
        md_dir: Markdown 文件目录
        
    Returns:
        list: 文件信息列表，每项包含 name, path, collection_name
    """
    funcs = _import_ingest_markdown()
    return funcs["get_markdown_files"](md_dir)


def read_markdown_file(md_path: str) -> dict:
    """
    读取 Markdown 文件内容。
    
    Args:
        md_path: Markdown 文件路径
        
    Returns:
        dict: 包含 text, char_count, success, error 的字典
    """
    funcs = _import_ingest_markdown()
    return funcs["read_markdown_file"](md_path)


def sanitize_collection_name(filename: str) -> str:
    """
    将文件名转换为合法的 Qdrant 集合名称。
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 合法的集合名称
    """
    funcs = _import_ingest_markdown()
    return funcs["sanitize_collection_name"](filename)


def get_qdrant_manager():
    """获取 QdrantManager 实例"""
    cls = _import_vector_tools()
    return cls()


def get_catalyst_extractor():
    """获取 CatalystInfoExtractor 实例"""
    cls = _import_extract_catalyst_info()
    return cls()


def query_and_extract_wrapper(collection_name: str = None) -> dict[str, Any]:
    """
    在指定集合中查询并提取双原子催化剂合成信息。
    
    该函数是 extract_dac_synthesis.query_and_extract 的包装器，
    用于从 Qdrant 集合中查询与双原子催化剂合成相关的文本，
    并使用 LLM 提取结构化数据。
    
    Args:
        collection_name: Qdrant 集合名称，如果为 None 则使用默认值
        
    Returns:
        dict: 包含提取结果的字典，包括反应步数、每步详情、活性位点等
    """
    func = _import_extract_dac_synthesis()
    return func(collection_name)


def delete_collections_by_pattern(pattern: str = None) -> dict:
    """
    删除匹配模式的 Qdrant 集合。
    
    Args:
        pattern: 集合名称匹配模式（可选）
        
    Returns:
        dict: 删除结果
    """
    func = _import_delete_collections()
    return func(pattern)


# ============================================
# 包装类方法为独立工具函数
# ============================================

def search_qdrant_collection(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    score_threshold: float = 0.7
) -> list[dict[str, Any]]:
    """
    在 Qdrant 向量数据库中执行语义搜索，查找与查询文本最相似的内容。
    
    该工具使用 OpenAI Embeddings 将查询文本转换为向量，然后在指定的 Qdrant 集合中
    执行相似度搜索，返回与查询语义最相关的文本块。适用于从已索引的科学论文中
    检索相关信息。
    
    Use this tool when you need to:
    - Search for relevant content in indexed PDF documents
    - Find semantically similar text passages in scientific papers
    - Retrieve context for catalyst synthesis information
    - Query the vector database for specific research topics
    
    Args:
        collection_name: Qdrant 集合名称，通常是 PDF 文件名的小写下划线形式
        query_text: 搜索查询文本，支持自然语言描述和关键词
        n_results: 返回的最大结果数量，默认 5
        score_threshold: 相似度阈值（0-1），低于此值的结果会被过滤，默认 0.7
        
    Returns:
        list: 搜索结果列表，每个元素是包含以下字段的字典：
            - text (str): 匹配的文本内容
            - score (float): 相似度分数（0-1，越高越相似）
            - chunk_index (int): 文本块在原文中的索引
            - source_file (str): 来源文件名
    """
    manager = get_qdrant_manager()
    return manager.search(
        collection_name=collection_name,
        query_text=query_text,
        n_results=n_results,
        score_threshold=score_threshold
    )


def list_qdrant_collections() -> list[dict[str, Any]]:
    """
    列出 Qdrant 向量数据库中所有可用的集合。
    
    Use this tool when you need to:
    - Check which PDF documents have been indexed
    - Get an overview of available data collections
    - Verify that a specific document has been processed
    
    Returns:
        list: 集合信息列表，每个元素包含：
            - name (str): 集合名称
            - points_count (int): 向量点数量
            - status (str): 集合状态
    """
    manager = get_qdrant_manager()
    return manager.list_collections()


def search_catalyst_content(
    query: str = None,
    top_k_per_collection: int = 5,
    total_top_k: int = 20,
    score_threshold: float = 0.35
) -> list[dict[str, Any]]:
    """
    在所有 Qdrant 集合中搜索与催化剂合成相关的内容。
    
    该方法会在所有已索引的文档集合中执行语义搜索，查找与催化剂
    合成、制备方法、实验步骤等相关的内容片段。
    
    Use this tool when you need to:
    - Search for catalyst synthesis information across all documents
    - Find experimental procedures for catalyst preparation
    - Retrieve relevant content for structure extraction
    
    Args:
        query: 自定义查询文本，如果为 None 则使用默认的催化剂合成相关关键词
        top_k_per_collection: 每个集合返回的最大结果数，默认 5
        total_top_k: 最终返回的总结果数（去重后），默认 20
        score_threshold: 相似度阈值，低于此值的结果会被过滤，默认 0.35
        
    Returns:
        list: 搜索结果列表，每个元素包含：
            - text (str): 匹配的文本内容
            - score (float): 相似度分数
            - collection (str): 来源集合名称
            - source_file (str): 来源文件名
    """
    extractor = get_catalyst_extractor()
    return extractor.search_related_content(
        query=query,
        top_k_per_collection=top_k_per_collection,
        total_top_k=total_top_k,
        score_threshold=score_threshold
    )


def _escape_value(value: Any) -> Any:
    """转义值中的 rich markup 特殊字符
    
    Args:
        value: 要转义的值
        
    Returns:
        转义后的值
    """
    if isinstance(value, str):
        return escape(value)
    elif isinstance(value, dict):
        return {k: _escape_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_escape_value(item) for item in value]
    else:
        return value


def extract_dual_atom_catalyst(collection_name: str = None) -> dict[str, Any]:
    """
    从 Qdrant 集合中提取双原子催化剂（DAC）合成的结构化数据。
    
    该工具用于从已索引的科学论文中提取双原子催化剂的合成信息。
    它会先在指定的 Qdrant 集合中搜索与双原子催化剂合成相关的内容，
    然后使用 LLM 将非结构化文本转换为结构化的 JSON 数据。
    
    Use this tool when you need to:
    - Extract dual-atom catalyst synthesis information from scientific papers
    - Structure experimental details for catalyst preparation
    - Retrieve information about active sites, precursors, and reaction conditions
    
    Args:
        collection_name: Qdrant 集合名称，如果为 None 则使用默认值
        
    Returns:
        dict: 包含提取结果的字典，包括反应步数、每步详情、活性位点等
    """
    result = query_and_extract_wrapper(collection_name)
    # 转义结果中的文本以避免 rich markup 解析错误
    return _escape_value(result)


# ============================================
# 工具注册列表
# ============================================

# 导出所有工具函数供 main.py 和 non_interactive.py 使用
PDF_EXTRACTION_TOOLS: list[Callable[..., Any]] = [
    # PDF 处理工具
    convert_pdf_to_markdown,
    
    # 文本处理工具
    chunk_markdown,
    
    # 向量数据库工具
    search_qdrant_collection,
    list_qdrant_collections,
    delete_collections_by_pattern,
    
    # 催化剂信息提取工具
    search_catalyst_content,
    extract_dual_atom_catalyst,
]
