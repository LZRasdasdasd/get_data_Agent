#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从中断点继续导入markdown文件到Qdrant向量数据库
跳过已经存在于Qdrant中的集合,避免重复导入
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Set

import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from dotenv import load_dotenv

# 导入 ingest_markdown 中的函数
from ingest_markdown import (
    chunk_markdown,
    get_markdown_files,
    get_qdrant_client,
    read_markdown_file,
    sanitize_collection_name,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
console = Console()

# 加载环境变量
load_dotenv()

# Qdrant 配置
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")

def get_existing_collections() -> Set[str]:
    """获取Qdrant中已存在的所有集合名称"""
    try:
        response = requests.get(f"{QDRANT_URL}/collections")
        if response.status_code == 200:
            collections = response.json()["result"]["collections"]
            return {col["name"] for col in collections}
        else:
            logger.error(f"获取集合列表失败: {response.status_code}")
            return set()
    except Exception as e:
        logger.error(f"获取集合列表时出错: {e}")
        return set()

def process_markdown_file(md_path: Path, qdrant_client) -> Dict:
    """
    处理单个markdown文件,将其分块并存储到Qdrant

    参数:
        md_path: markdown文件路径
        qdrant_client: Qdrant客户端

    返回:
        包含处理结果的字典
    """
    try:
        # 读取文件内容
        file_data = read_markdown_file(md_path)

        # 创建集合名称
        collection_name = sanitize_collection_name(md_path.name)

        # 检查集合是否已存在
        try:
            qdrant_client.get_collection(collection_name)
            logger.warning(f"集合 {collection_name} 已存在,跳过导入")
            return {
                "file": md_path.name,
                "status": "skipped",
                "chunks": 0,
                "error": None,
            }
        except Exception:
            # 集合不存在,继续导入
            pass

        # 分割文本为chunks
        chunks = chunk_markdown(file_data["content"])

        if not chunks:
            logger.warning(f"文件 {md_path.name} 没有生成任何chunks")
            return {
                "file": md_path.name,
                "status": "no_chunks",
                "chunks": 0,
                "error": None,
            }

        # 创建集合并插入向量
        # 从chunks中提取文本内容
        texts = [chunk["text"] for chunk in chunks]

        # 生成嵌入向量
        try:
            from ingest_markdown import EMBEDDING_MODEL

            embeddings = EMBEDDING_MODEL.encode(texts, show_progress_bar=False)
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return {"file": md_path.name, "status": "embedding_error", "chunks": 0, "error": str(e)}

        # 准备payload数据
        payloads = []
        for i, chunk in enumerate(chunks):
            payload = {
                "text": chunk["text"],
                "source_file": md_path.name,
                "chunk_id": i,
                "heading": chunk.get("heading", ""),
                "metadata": {
                    "authors": file_data.get("authors", ""),
                    "year": file_data.get("year", ""),
                    "title": file_data.get("title", ""),
                },
            }
            payloads.append(payload)

        # 向量化维度
        vector_dim = len(embeddings[0])

        # 创建集合
        try:
            from qdrant_client.models import Distance, VectorParams, PointStruct

            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
            )
        except Exception as e:
            logger.error(f"创建集合 {collection_name} 失败: {e}")
            return {"file": md_path.name, "status": "collection_error", "chunks": 0, "error": str(e)}

        # 插入向量点
        points = [
            PointStruct(id=i, vector=embeddings[i].tolist(), payload=payloads[i])
            for i in range(len(embeddings))
        ]

        try:
            qdrant_client.upsert(collection_name=collection_name, points=points)
        except Exception as e:
            logger.error(f"插入点到 {collection_name} 失败: {e}")
            return {"file": md_path.name, "status": "insert_error", "chunks": len(chunks), "error": str(e)}

        return {
            "file": md_path.name,
            "status": "success",
            "chunks": len(chunks),
            "error": None,
        }

    except Exception as e:
        logger.error(f"处理文件 {md_path} 时出错: {e}")
        return {"file": md_path.name, "status": "error", "chunks": 0, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="从中断点继续导入markdown文件到Qdrant向量数据库")
    parser.add_argument("--md-dir", type=str, default="markdown_docs", help="markdown文件目录")
    parser.add_argument("--timeout", type=int, default=60, help="Qdrant操作超时时间(秒)")
    args = parser.parse_args()

    md_dir = Path(args.md_dir)

    if not md_dir.exists():
        logger.error(f"目录不存在: {md_dir}")
        sys.exit(1)

    # 获取Qdrant客户端
    qdrant_client = get_qdrant_client(timeout=args.timeout)

    # 获取已存在的集合
    console.print("[cyan]正在检查已存在的集合...[/cyan]")
    existing_collections = get_existing_collections()
    console.print(f"[green]已找到 {len(existing_collections)} 个已导入的集合[/green]")

    # 获取所有markdown文件
    md_files = get_markdown_files(str(md_dir))
    total_files = len(md_files)

    if total_files == 0:
        logger.error("没有找到markdown文件")
        sys.exit(1)

    # 过滤出需要导入的文件(未在existing_collections中的)
    files_to_import = []
    skipped_count = 0
    for md_file in md_files:
        collection_name = sanitize_collection_name(md_file.name)
        if collection_name in existing_collections:
            skipped_count += 1
        else:
            files_to_import.append(md_file)

    console.print("\n[cyan]导入统计:[/cyan]")
    console.print(f"  总文件数: {total_files}")
    console.print(f"  已导入(跳过): {skipped_count}")
    console.print(f"  待导入: {len(files_to_import)}")

    if len(files_to_import) == 0:
        console.print("[green]所有文件已导入完成![/green]")
        return

    # 处理markdown文件
    console.print("\n[cyan]开始导入待处理的文件...[/cyan]")

    results = []
    success_count = 0
    failed_count = 0
    skipped_import_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]导入markdown文件...", total=len(files_to_import))

        for md_file in files_to_import:
            progress.update(task, description=f"[cyan]导入: {md_file.name[:50]}...")

            result = process_markdown_file(md_file, qdrant_client)
            results.append(result)

            if result["status"] == "success":
                success_count += 1
                console.print(
                    f"[green]✓[/green] {md_file.name[:50]}... "
                    f"({result['chunks']} chunks)"
                )
            elif result["status"] == "skipped":
                skipped_import_count += 1
                console.print(f"[yellow]⊘[/yellow] {md_file.name[:50]}... (已存在,跳过)")
            else:
                failed_count += 1
                console.print(
                    f"[red]✗[/red] {md_file.name[:50]}... "
                    f"({result['status']}: {result.get('error', '')[:30]})"
                )

            progress.update(task, advance=1)

    # 输出统计信息
    console.print("\n" + "=" * 80)
    console.print("[cyan]导入完成![/cyan]")
    console.print(f"  成功: {success_count}")
    console.print(f"  失败: {failed_count}")
    console.print(f"  跳过(已存在): {skipped_import_count}")
    console.print(f"  总计处理: {len(files_to_import)}")

    if failed_count > 0:
        console.print("\n[cyan]失败的文件:[/cyan]")
        for result in results:
            if result["status"] not in ["success", "skipped"]:
                console.print(
                    f"  {result['file']}: {result['status']} - {result.get('error', '')}"
                )


if __name__ == "__main__":
    import os

    main()
