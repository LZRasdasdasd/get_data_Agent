"""
向量数据库存储工具模块

核心功能：Vector Database Storage / 向量存储
- 将文本块存入 Qdrant 向量数据库
- 支持两种存储模式：全部存入 和 按名称存入单个文件
- 为每个文本块生成向量嵌入 (Embedding)

这是向量数据库存储流程中的独立工具，只负责向量存储操作
需要先通过 chunk_text_tool.py 进行文本分块

Use this tool when you need to:
- Store text chunks into Qdrant vector database
- Batch ingest multiple documents into vector store
- Single document ingestion by name
- Prepare document corpus for semantic search and retrieval
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from qdrant_config import config
from vector_tools import QdrantManager


# 初始化控制台
console = Console()

# 全局 Qdrant 管理器实例（延迟初始化）
_qdrant_manager: Optional[QdrantManager] = None


def get_qdrant_manager() -> QdrantManager:
    """
    获取 Qdrant 管理器实例（单例模式）
    
    Returns:
        QdrantManager: Qdrant 管理器实例
    """
    global _qdrant_manager
    if _qdrant_manager is None:
        _qdrant_manager = QdrantManager()
    return _qdrant_manager


def sanitize_collection_name(filename: str) -> str:
    """
    将文件名转换为合法的 Qdrant 集合名称
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 合法的集合名称
    """
    import re
    # 移除扩展名
    name = Path(filename).stem
    
    # 转小写
    name = name.lower()
    
    # 替换特殊字符为下划线
    name = re.sub(r'[^a-z0-9_]', '_', name)
    
    # 合并连续下划线
    name = re.sub(r'_+', '_', name)
    
    # 移除首尾下划线
    name = name.strip('_')
    
    # 截断到 50 个字符
    if len(name) > 50:
        name = name[:50]
    
    # 确保不为空
    if not name:
        name = "unnamed_collection"
    
    return name


def store_chunks_to_qdrant(
    chunks: List[Dict[str, Any]],
    collection_name: str,
    source_file: str = "",
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    【向量存储工具】将文本块存入 Qdrant 向量数据库。
    
    核心功能：Vector Database Storage / 向量存储
    - 为每个文本块生成向量嵌入 (Embedding)
    - 将向量数据存入 Qdrant 向量数据库
    - 支持后续的语义搜索和检索
    
    这是向量数据库存储流程中的第二步：向量存储 (Vector Storage)
    需要先通过 chunk_text_tool 进行文本分块
    
    Use this tool when you need to:
    - Store text chunks into Qdrant vector database
    - Ingest chunked content into vector store
    - Prepare document corpus for semantic search
    
    Args:
        chunks: 文本块列表，每个块是包含以下字段的字典：
            - text (str): 文本内容
            - chunk_index (int): 块索引
            - char_count (int): 字符数
        collection_name: Qdrant 集合名称（用于存储向量）
        source_file: 源文件名（可选，用于元数据）
        batch_size: 批量存储大小，默认 10
        
    Returns:
        dict: 包含操作结果的字典：
            - status (str): 操作状态 ("success" 或 "error")
            - collection_name (str): 集合名称
            - chunks_count (int): 输入的文本块数量
            - points_added (int): 成功存入的向量点数量
            - message (str): 结果描述
            - error (str): 错误信息（如果失败）
    
    Example:
        >>> chunks = [{"text": "content...", "chunk_index": 0, "char_count": 500}]
        >>> result = store_chunks_to_qdrant(chunks, "my_collection", "doc.md")
        >>> print(result["status"])  # "success" 或 "error"
    """
    if not chunks:
        return {
            "status": "error",
            "collection_name": collection_name,
            "chunks_count": 0,
            "points_added": 0,
            "message": "没有提供文本块",
            "error": "No chunks provided"
        }
    
    try:
        # 为每个块添加源文件信息
        for chunk in chunks:
            if "source_file" not in chunk:
                chunk["source_file"] = source_file
        
        # 获取 Qdrant 管理器
        qdrant = get_qdrant_manager()
        
        # 创建集合
        create_result = qdrant.create_collection(collection_name)
        if create_result["status"] == "error":
            return {
                "status": "error",
                "collection_name": collection_name,
                "chunks_count": len(chunks),
                "points_added": 0,
                "message": f"创建集合失败: {create_result.get('error')}",
                "error": create_result.get("error")
            }
        
        # 存入向量
        store_result = qdrant.add_points(
            collection_name=collection_name,
            points=chunks,
            batch_size=batch_size
        )
        
        if store_result["status"] == "success":
            return {
                "status": "success",
                "collection_name": collection_name,
                "chunks_count": len(chunks),
                "points_added": store_result.get("points_added", len(chunks)),
                "message": f"成功将 {len(chunks)} 个文本块存入集合 {collection_name}",
                "error": None
            }
        else:
            return {
                "status": "error",
                "collection_name": collection_name,
                "chunks_count": len(chunks),
                "points_added": 0,
                "message": f"存入向量失败: {store_result.get('error')}",
                "error": store_result.get("error")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "collection_name": collection_name,
            "chunks_count": len(chunks),
            "points_added": 0,
            "message": f"存入向量时发生异常: {str(e)}",
            "error": str(e)
        }


def store_single_file(
    md_path: str,
    collection_name: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 500,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    【按名称存入单个文件】将单个 Markdown 文件分块并存入 Qdrant 向量数据库。
    
    核心功能：Single File Storage / 单文件存储
    - 读取单个 Markdown 文件
    - 自动进行文本分块
    - 存入指定的 Qdrant 集合
    
    Use this tool when you need to:
    - Store a single document into vector database
    - Ingest one specific file by name
    - Create or update a collection with single document
    
    Args:
        md_path: Markdown 文件路径
        collection_name: Qdrant 集合名称（可选，默认根据文件名生成）
        chunk_size: 目标块大小（字符数），默认 1000
        chunk_overlap: 块之间的重叠字符数，默认 200
        min_chunk_size: 最小块大小，默认 500
        batch_size: 批量存储大小，默认 10
        
    Returns:
        dict: 包含操作结果的字典：
            - status (str): 操作状态
            - collection_name (str): 集合名称
            - file_name (str): 文件名
            - char_count (int): 总字符数
            - chunks_count (int): 生成的文本块数量
            - points_added (int): 成功存入的向量点数量
            - message (str): 结果描述
    
    Example:
        >>> result = store_single_file("/path/to/doc.md", "my_collection")
        >>> print(result["status"])
    """
    from chunk_text_tool import chunk_text, read_markdown_file
    
    md_path = Path(md_path)
    if not md_path.exists():
        return {
            "status": "error",
            "collection_name": collection_name or "",
            "file_name": md_path.name,
            "char_count": 0,
            "chunks_count": 0,
            "points_added": 0,
            "message": f"文件不存在: {md_path}",
            "error": f"File not found: {md_path}"
        }
    
    # 如果没有指定集合名称，根据文件名生成
    if not collection_name:
        collection_name = sanitize_collection_name(md_path.name)
    
    # 读取文件
    read_result = read_markdown_file(str(md_path))
    if not read_result["success"]:
        return {
            "status": "error",
            "collection_name": collection_name,
            "file_name": md_path.name,
            "char_count": 0,
            "chunks_count": 0,
            "points_added": 0,
            "message": f"读取文件失败: {read_result.get('error')}",
            "error": read_result.get("error")
        }
    
    text = read_result["text"]
    char_count = read_result["char_count"]
    
    # 分块
    chunks = chunk_text(text, chunk_size, chunk_overlap, min_chunk_size)
    
    if not chunks:
        return {
            "status": "error",
            "collection_name": collection_name,
            "file_name": md_path.name,
            "char_count": char_count,
            "chunks_count": 0,
            "points_added": 0,
            "message": "文本分块失败：没有生成任何文本块",
            "error": "No chunks generated"
        }
    
    # 存入向量
    store_result = store_chunks_to_qdrant(
        chunks=chunks,
        collection_name=collection_name,
        source_file=md_path.name,
        batch_size=batch_size
    )
    
    return {
        "status": store_result["status"],
        "collection_name": collection_name,
        "file_name": md_path.name,
        "char_count": char_count,
        "chunks_count": len(chunks),
        "points_added": store_result.get("points_added", 0),
        "message": store_result["message"],
        "error": store_result.get("error")
    }


def store_all_files(
    md_dir: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 500,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    【全部存入】将目录下所有 Markdown 文件分块并存入 Qdrant 向量数据库。
    
    核心功能：Batch Storage / 批量存储
    - 扫描目录下所有 .md 文件
    - 自动进行文本分块
    - 每个文件创建独立的 Qdrant 集合
    
    Use this tool when you need to:
    - Store all documents in a directory into vector database
    - Batch ingest multiple files at once
    - Build complete document corpus for semantic search
    
    Args:
        md_dir: Markdown 文件目录
        chunk_size: 目标块大小（字符数），默认 1000
        chunk_overlap: 块之间的重叠字符数，默认 200
        min_chunk_size: 最小块大小，默认 500
        batch_size: 批量存储大小，默认 10
        
    Returns:
        dict: 包含批量操作结果的字典：
            - status (str): 整体操作状态
            - md_dir (str): 处理的目录
            - total_files (int): 总文件数
            - success_count (int): 成功数量
            - failed_count (int): 失败数量
            - total_chunks (int): 总块数
            - total_points (int): 总向量点数
            - collections (list): 创建的集合列表
            - errors (list): 错误列表
    
    Example:
        >>> result = store_all_files("/path/to/markdown_docs")
        >>> print(f"成功: {result['success_count']}, 失败: {result['failed_count']}")
    """
    from chunk_text_tool import get_markdown_files
    
    md_path = Path(md_dir)
    if not md_path.exists():
        return {
            "status": "error",
            "md_dir": md_dir,
            "total_files": 0,
            "success_count": 0,
            "failed_count": 0,
            "total_chunks": 0,
            "total_points": 0,
            "collections": [],
            "errors": [{"error": f"目录不存在: {md_dir}"}],
            "message": f"目录不存在: {md_dir}"
        }
    
    # 获取所有 Markdown 文件
    md_files = get_markdown_files(md_dir)
    
    if not md_files:
        return {
            "status": "error",
            "md_dir": md_dir,
            "total_files": 0,
            "success_count": 0,
            "failed_count": 0,
            "total_chunks": 0,
            "total_points": 0,
            "collections": [],
            "errors": [{"error": f"未找到 Markdown 文件: {md_dir}"}],
            "message": f"未找到 Markdown 文件: {md_dir}"
        }
    
    result = {
        "status": "success",
        "md_dir": md_dir,
        "total_files": len(md_files),
        "success_count": 0,
        "failed_count": 0,
        "total_chunks": 0,
        "total_points": 0,
        "collections": [],
        "errors": []
    }
    
    console.print(f"\n[bold]找到 {len(md_files)} 个 Markdown 文件[/bold]")
    console.print(f"Qdrant 地址: {config.qdrant_url}")
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]处理 Markdown 文件...", 
            total=len(md_files)
        )
        
        for i, md_file in enumerate(md_files):
            progress.update(overall_task, advance=1)
            
            collection_name = md_file["collection_name"]
            
            console.print(f"\n[{i+1}/{len(md_files)}] 处理: {md_file['name']}")
            console.print(f"  集合名: {collection_name}")
            
            # 存入单个文件
            file_result = store_single_file(
                md_path=md_file["path"],
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                min_chunk_size=min_chunk_size,
                batch_size=batch_size
            )
            
            if file_result["status"] == "success":
                result["success_count"] += 1
                result["total_chunks"] += file_result["chunks_count"]
                result["total_points"] += file_result["points_added"]
                result["collections"].append({
                    "name": collection_name,
                    "file": md_file["name"],
                    "chunks": file_result["chunks_count"],
                    "points": file_result["points_added"]
                })
                console.print(f"  [green]成功: {file_result['chunks_count']} 个块[/green]")
            else:
                result["failed_count"] += 1
                result["errors"].append({
                    "file": md_file["name"],
                    "error": file_result.get("error", "未知错误")
                })
                console.print(f"  [red]失败: {file_result.get('error')}[/red]")
    
    # 更新整体状态
    if result["failed_count"] > 0 and result["success_count"] == 0:
        result["status"] = "error"
        result["message"] = "所有文件存入失败"
    elif result["failed_count"] > 0:
        result["status"] = "partial_success"
        result["message"] = f"部分成功: {result['success_count']} 个文件成功, {result['failed_count']} 个失败"
    else:
        result["status"] = "success"
        result["message"] = f"全部成功: {result['success_count']} 个文件"
    
    return result


def list_stored_collections() -> Dict[str, Any]:
    """
    列出 Qdrant 中已存储的所有集合
    
    Returns:
        dict: 包含集合列表的字典
    """
    try:
        qdrant = get_qdrant_manager()
        collections = qdrant.list_collections()
        
        return {
            "status": "success",
            "total": len(collections),
            "collections": collections,
            "message": f"找到 {len(collections)} 个集合"
        }
    except Exception as e:
        return {
            "status": "error",
            "total": 0,
            "collections": [],
            "error": str(e),
            "message": f"获取集合列表失败: {str(e)}"
        }


def main():
    """
    命令行入口：向量数据库存储工具
    
    支持两种模式：
    1. 全部存入：将目录下所有 Markdown 文件存入向量数据库
    2. 按名称存入单个：将指定的单个 Markdown 文件存入向量数据库
    """
    parser = argparse.ArgumentParser(
        description="向量数据库存储工具 - 将文本块存入 Qdrant 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 全部存入：处理目录下所有 Markdown 文件
  python vector_store_tool.py --all --md-dir markdown_docs
  
  # 按名称存入单个：处理指定文件
  python vector_store_tool.py --single --file path/to/document.md
  
  # 指定集合名称
  python vector_store_tool.py --single --file doc.md --collection my_collection
  
  # 列出所有集合
  python vector_store_tool.py --list
        """
    )
    
    # 存储模式
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--all", "-a",
        action="store_true",
        help="全部存入：处理目录下所有 Markdown 文件"
    )
    mode_group.add_argument(
        "--single", "-s",
        action="store_true",
        help="按名称存入单个：处理指定的单个 Markdown 文件"
    )
    mode_group.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有已存储的集合"
    )
    
    # 全部存入模式的参数
    parser.add_argument(
        "--md-dir", "-d",
        type=str,
        default="markdown_docs",
        help="Markdown 文件目录路径 (默认: markdown_docs)"
    )
    
    # 单个存入模式的参数
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="单个 Markdown 文件路径（配合 --single 使用）"
    )
    
    parser.add_argument(
        "--collection", "-c",
        type=str,
        default=None,
        help="Qdrant 集合名称（可选，默认根据文件名生成）"
    )
    
    # 分块参数
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="文本块大小 (默认: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="文本块之间的重叠 (默认: 200)"
    )
    
    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=500,
        help="最小文本块大小 (默认: 500)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="批量存储大小 (默认: 10)"
    )
    
    args = parser.parse_args()
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]向量数据库存储工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"Qdrant 地址: {config.qdrant_url}")
    
    # 列出集合模式
    if args.list:
        console.print("\n[bold]列出所有集合[/bold]")
        result = list_stored_collections()
        
        if result["status"] == "success":
            console.print(f"找到 {result['total']} 个集合:")
            for col in result["collections"]:
                console.print(f"  - {col['name']}: {col['points_count']} 个向量点")
        else:
            console.print(f"[red]错误: {result.get('error')}[/red]")
        return result
    
    # 全部存入模式
    if args.all:
        console.print(f"\n[bold]模式: 全部存入[/bold]")
        console.print(f"Markdown 目录: {args.md_dir}")
        console.print(f"块大小: {args.chunk_size}")
        
        result = store_all_files(
            md_dir=args.md_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            min_chunk_size=args.min_chunk_size,
            batch_size=args.batch_size
        )
        
        # 显示统计
        console.print("\n")
        console.print("=" * 60)
        console.print(Panel.fit(
            "[bold green]存入完成统计[/bold green]",
            border_style="green"
        ))
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("统计项", style="cyan")
        table.add_column("值", style="green")
        table.add_row("总文件数", str(result["total_files"]))
        table.add_row("成功", str(result["success_count"]))
        table.add_row("失败", str(result["failed_count"]))
        table.add_row("总块数", str(result["total_chunks"]))
        table.add_row("总向量数", str(result["total_points"]))
        
        console.print(table)
        
        # 显示集合列表
        if result["collections"]:
            console.print("\n[bold]创建的集合:[/bold]")
            for col in result["collections"]:
                console.print(f"  - {col['name']}: {col['chunks']} 个块, {col['points']} 个向量")
        
        return result
    
    # 单个存入模式
    if args.single:
        if not args.file:
            console.print("[red]错误: 必须指定 --file 参数[/red]")
            return {"status": "error", "message": "必须指定 --file 参数"}
        
        console.print(f"\n[bold]模式: 按名称存入单个[/bold]")
        console.print(f"文件: {args.file}")
        console.print(f"集合名称: {args.collection or '(自动生成)'}")
        console.print(f"块大小: {args.chunk_size}")
        
        result = store_single_file(
            md_path=args.file,
            collection_name=args.collection,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            min_chunk_size=args.min_chunk_size,
            batch_size=args.batch_size
        )
        
        if result["status"] == "success":
            console.print(f"\n[green]成功存入![/green]")
            console.print(f"  集合: {result['collection_name']}")
            console.print(f"  字符数: {result['char_count']}")
            console.print(f"  块数: {result['chunks_count']}")
            console.print(f"  向量数: {result['points_added']}")
        else:
            console.print(f"\n[red]存入失败: {result.get('error')}[/red]")
        
        return result
    
    return {"status": "error", "message": "未指定操作模式"}


if __name__ == "__main__":
    main()
