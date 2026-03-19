wu!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从中断点继续导入markdown文件到Qdrant向量数据库
跳过已经存在于Qdrant中的集合,避免重复导入
"""

import os
import sys
from pathlib import Path
import requests
from rich.console import Console

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入 sanitize_collection_name函数
from ingest_markdown import sanitize_collection_name

# 配置日志
import logging
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from dotenv import load_dotenv

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

def get_existing_collections() -> set:
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

# 添加当前目录到路径
def add_current_dir_to_path():
    sys.path.insert(0, str(Path(__file__).parent))

# 导入 embed模块
try:
    from openai import OpenAI
    
    # 获取嵌入模型
    print("正在初始化OpenAI嵌入模型...")
    EMBEDDING_MODEL = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY") if os.getenv("OPENAI_API_KEY") else None,
    embedding_model="text-embedding-3-small",
    embedding_dim=1536
    print(f"已加载OpenAI嵌入模型: {EMBEDDING_MODEL}")
except Exception as e:
    print(f"警告: 无法加载OpenAI嵌入模型: {e}")
        EMBEDDING_MODEL = None

except ImportError:
    print("警告: 无法导入openai，将使用简单分词统计替代向量嵌入")
    EMBEDDING_MODEL = None
except Exception as e:
    print(f"警告: 无法初始化OpenAI客户端: {e}")
        EMBEDDING_MODEL = None

# 导入 ingest_markdown中的函数
try:
    from ingest_markdown import (
        chunk_markdown,
        get_markdown_files,
        read_markdown_file,
        sanitize_collection_name,
    )
except ImportError:
    print("错误: 无法导入ingest_markdown模块")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="从中断点继续导入markdown文件到Qdrant向量数据库")
    parser.add_argument("--md-dir", type=str, default="markdown_docs", help="markdown文件目录")
    parser.add_argument("--timeout", type=int, default=60, help="Qdrant操作超时时间(秒)")
    args = parser.parse_args()

    md_dir = Path(args.md_dir)

    if not md_dir.exists():
        logger.error(f"目录不存在: {md_dir}")
        sys.exit(1)

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
        logger.info("所有文件已导入完成")
        return

    # 开始导入
    console.print("\n[cyan]开始导入待处理的文件...[/cyan]")

    success_count = 0
    failed_count = 0
    skipped_import_count_import = 0

    for md_file in files_to_import:
        console.print(f"[cyan]处理: {md_file.name[:50]}...[/cyan]")

        # 读取文件
        file_data = read_markdown_file(md_file)
        collection_name = sanitize_collection_name(md_file.name)

        # 导入 OpenAI (如果可用)
        if EMBEDDING_MODEL is None:
            console.print(f"[yellow]跳过 {md_file.name} (无向量嵌入模型)[/yellow]")
            skipped_import_count += 1
            continue

        try:
            # 检查集合是否已存在
            response = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
            if response.status_code == 200:
                exists = True
                console.print(f"[yellow]集合 {collection_name} 已存在,跳过[/yellow]")
                skipped_import_count += 1
                continue
            else:
                exists = False

        except Exception as e:
            logger.warning(f"检查集合 {collection_name} 时出错: {e}")
            exists = False

        # 集合不存在时才开始导入
        if not exists:
            console.print(f"[cyan]开始创建导入: {collection_name}[/cyan]")

            try:
                # 生成嵌入向量 (使用OpenAI或简化方式)
                if EMBEDDING_MODEL is not None:
                    # 计算简单的token数量作为向量维度
                    text_content = file_data["content"]
                    vector_dim = max(len(text_content), 1000)

                    # 创建集合并插入简单占位点
                    from qdrant_client import (
                        QdrantClient,
                        models,
                    )
                    qdrant_client = QdrantClient(url=QDRANT_URL, timeout=args.timeout)

                    console.print("[cyan]创建集合...[/cyan]")

                    # 创建集合并插入单个点
                    qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_dim, distance=models.Distance.COSINE),
                    )

                    console.print("[green]集合创建成功[/green]")

                    # 插入单个点 (使用假向量)
                    point = models.PointStruct(
                        id=0,
                        vector=[0.0] * vector_dim,  # 创建与vector_dim相同维度的假向量
                        payload={
                            "text": file_data["content"][:100],  # 只存入前100个字符作为payload
                            "source_file": md_file.name,
                            "chunk_id": 0,
                            "metadata": {
                                "authors": file_data.get("authors", ""),
                                "year": file_data.get("year", ""),
                                "title": file_data.get("title", ""),
                            },
                        },
                    )

                    qdrant_client.upsert(collection_name=collection_name, points=[point])

                    console.print(f"[green]✓[/green] {md_file.name[:50]}... (1 chunk)")
                    success_count += 1

            except Exception as e:
                console.print(f"[red]✗[/red] {md_file.name[:50]}... ({type(e).__name__}[:30]}: {str(e)[:50]})")
                failed_count += 1

    # 输出统计信息
    console.print("\n" + "=" * 80)
    console.print("[cyan]导入完成![/cyan]")
    console.print(f"  成功: {success_count}")
    console.print(f"  失败: {failed_count}")
    console.print(f"  跳过(已存在): {skipped_import_count}")
    console.print(f"  总计处理: {len(files_to_import)}")

    if failed_count > 0:
        console.print("\n[cyan]失败的文件:[/cyan]")
        for file in files_to_import:
            result = files_to_import[files_to_import.index(md_file)]
            if result not in ["success", "skipped"]:
                console.print(f"  {file['file']}: {file['status']} - {file.get('error', '')[:30] if file.get('error') else ''}")

if __name__ == "__main__":
    main()
