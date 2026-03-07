"""
重置数据库并重新导入 Markdown 数据的脚本

执行步骤:
1. 删除所有现有的 Qdrant 集合
2. 将 Markdown 文件存入向量数据库（使用配置的分块大小）
3. 验证所有文件都已成功存储
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress

from config import config
from vector_tools import QdrantManager
from ingest_markdown import (
    get_markdown_files,
    read_markdown_file,
    chunk_markdown,
    sanitize_collection_name
)


# 初始化控制台
console = Console()


def delete_all_collections(qdrant: QdrantManager) -> int:
    """
    删除所有现有的 Qdrant 集合
    
    Args:
        qdrant: Qdrant 管理器实例
        
    Returns:
        int: 删除的集合数量
    """
    console.print("\n[bold yellow]步骤 1: 删除所有现有集合[/bold yellow]")
    
    # 获取所有集合
    collections = qdrant.list_collections()
    
    if not collections:
        console.print("[green]  没有找到现有集合，跳过删除[/green]")
        return 0
    
    console.print(f"[cyan]  找到 {len(collections)} 个现有集合:[/cyan]")
    for col in collections:
        console.print(f"    - {col['name']}")
    
    # 删除每个集合
    deleted_count = 0
    for col in collections:
        result = qdrant.delete_collection(col['name'])
        if result['status'] == 'deleted':
            console.print(f"  [green]✓[/green] 已删除: {col['name']}")
            deleted_count += 1
        else:
            console.print(f"  [red]✗[/red] 删除失败: {col['name']} - {result.get('message', '未知错误')}")
    
    console.print(f"[green]  成功删除 {deleted_count} 个集合[/green]")
    return deleted_count


def ingest_all_markdown(qdrant: QdrantManager, md_dir: str, chunk_size: int) -> dict:
    """
    将所有 Markdown 文件存入向量数据库
    
    Args:
        qdrant: Qdrant 管理器实例
        md_dir: Markdown 文件目录
        chunk_size: 分块大小
        
    Returns:
        dict: 存入统计信息
    """
    console.print("\n[bold yellow]步骤 2: 将 Markdown 文件存入向量数据库[/bold yellow]")
    console.print(f"[cyan]  Markdown 目录: {md_dir}[/cyan]")
    console.print(f"[cyan]  分块大小: {chunk_size} 字符[/cyan]")
    
    # 获取所有 Markdown 文件
    md_files = get_markdown_files(md_dir)
    
    if not md_files:
        console.print(f"[red]  未找到 Markdown 文件: {md_dir}[/red]")
        return {"total": 0, "success": 0, "failed": 0, "total_chunks": 0}
    
    console.print(f"[cyan]  找到 {len(md_files)} 个 Markdown 文件[/cyan]")
    
    # 存入统计
    stats = {
        "total": len(md_files),
        "success": 0,
        "failed": 0,
        "total_chunks": 0,
        "collections": []
    }
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]处理文件...", 
            total=len(md_files)
        )
        
        for md_file in md_files:
            collection_name = md_file["collection_name"]
            
            # 更新进度描述
            progress.update(
                overall_task, 
                description=f"[cyan]处理: {md_file['name'][:40]}..."
            )
            
            # 读取文件内容
            md_result = read_markdown_file(md_file["path"])
            if not md_result["success"]:
                console.print(f"  [red]✗[/red] 读取失败: {md_file['name']} - {md_result['error']}")
                stats["failed"] += 1
                progress.update(overall_task, advance=1)
                continue
            
            # 分块
            chunks = chunk_markdown(md_result["text"], chunk_size=chunk_size)
            
            if not chunks:
                console.print(f"  [yellow]⚠[/yellow] 无内容: {md_file['name']}")
                stats["failed"] += 1
                progress.update(overall_task, advance=1)
                continue
            
            # 为每个块添加源文件信息
            for chunk in chunks:
                chunk["source_file"] = md_file["name"]
            
            # 创建集合
            create_result = qdrant.create_collection(collection_name)
            if create_result["status"] == "error":
                console.print(f"  [red]✗[/red] 创建集合失败: {collection_name}")
                stats["failed"] += 1
                progress.update(overall_task, advance=1)
                continue
            
            # 添加向量点
            add_result = qdrant.add_points(collection_name, chunks)
            
            if add_result["status"] == "success":
                stats["success"] += 1
                stats["total_chunks"] += add_result["points_added"]
                stats["collections"].append({
                    "name": collection_name,
                    "file": md_file["name"],
                    "chunks": add_result["points_added"]
                })
            else:
                console.print(f"  [red]✗[/red] 添加向量失败: {collection_name}")
                stats["failed"] += 1
            
            progress.update(overall_task, advance=1)
    
    return stats


def verify_collections(qdrant: QdrantManager, expected_count: int) -> bool:
    """
    验证所有集合都已成功创建
    
    Args:
        qdrant: Qdrant 管理器实例
        expected_count: 预期的集合数量
        
    Returns:
        bool: 验证是否通过
    """
    console.print("\n[bold yellow]步骤 3: 验证数据存储[/bold yellow]")
    
    # 获取所有集合
    collections = qdrant.list_collections()
    
    console.print(f"[cyan]  预期集合数: {expected_count}[/cyan]")
    console.print(f"[cyan]  实际集合数: {len(collections)}[/cyan]")
    
    # 创建验证表格
    table = Table(title="集合验证结果")
    table.add_column("集合名称", style="cyan")
    table.add_column("向量点数", style="green")
    table.add_column("状态", style="bold")
    
    total_points = 0
    for col in collections:
        info = qdrant.get_collection_info(col['name'])
        points_count = info.get('points_count', 0)
        total_points += points_count
        status = "[green]✓[/green]" if info.get('status') == 'success' else "[red]✗[/red]"
        table.add_row(col['name'], str(points_count), status)
    
    console.print(table)
    console.print(f"[green]  总向量点数: {total_points}[/green]")
    
    if len(collections) >= expected_count:
        console.print(f"[bold green]✓ 验证通过！所有 {len(collections)} 个集合都已成功创建[/bold green]")
        return True
    else:
        console.print(f"[bold red]✗ 验证失败！预期 {expected_count} 个集合，实际只有 {len(collections)} 个[/bold red]")
        return False


def test_search(qdrant: QdrantManager):
    """
    测试搜索功能
    
    Args:
        qdrant: Qdrant 管理器实例
    """
    console.print("\n[bold yellow]步骤 4: 测试数据提取功能[/bold yellow]")
    
    # 获取所有集合
    collections = qdrant.list_collections()
    
    if not collections:
        console.print("[red]  没有集合可测试[/red]")
        return
    
    # 选择第一个集合进行测试
    test_collection = collections[0]['name']
    test_query = "carbon nitride"
    
    console.print(f"[cyan]  测试集合: {test_collection}[/cyan]")
    console.print(f"[cyan]  测试查询: '{test_query}'[/cyan]")
    
    # 执行搜索
    results = qdrant.search(
        collection_name=test_collection,
        query_text=test_query,
        n_results=3
    )
    
    if results:
        console.print(f"[green]  ✓ 搜索成功，找到 {len(results)} 个结果[/green]")
        
        # 显示搜索结果
        for i, result in enumerate(results):
            console.print(f"\n  [bold]结果 {i+1}:[/bold]")
            console.print(f"    相似度: {result['score']:.4f}")
            console.print(f"    来源: {result['source_file']}")
            text_preview = result['text'][:200].replace('\n', ' ')
            console.print(f"    内容预览: {text_preview}...")
    else:
        console.print("[yellow]  ⚠ 搜索未返回结果[/yellow]")


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold cyan]重置数据库并重新导入数据[/bold cyan]\n"
        f"[dim]分块大小: {config.chunk_size} 字符[/dim]",
        border_style="cyan"
    ))
    
    # 显示配置信息
    console.print(f"\n[bold]配置信息:[/bold]")
    console.print(f"  Qdrant 地址: {config.qdrant_url}")
    console.print(f"  嵌入模型: {config.embedding_model}")
    console.print(f"  嵌入维度: {config.embedding_dimension}")
    console.print(f"  分块大小: {config.chunk_size}")
    
    # 初始化 Qdrant 管理器
    console.print("\n[bold]连接 Qdrant...[/bold]")
    try:
        qdrant = QdrantManager()
    except Exception as e:
        console.print(f"[red]连接 Qdrant 失败: {e}[/red]")
        sys.exit(1)
    
    # Markdown 目录
    md_dir = Path(__file__).parent.parent / "markdown_docs"
    if not md_dir.exists():
        console.print(f"[red]Markdown 目录不存在: {md_dir}[/red]")
        sys.exit(1)
    
    # 步骤 1: 删除所有现有集合
    delete_all_collections(qdrant)
    
    # 步骤 2: 存入所有 Markdown 文件
    stats = ingest_all_markdown(qdrant, str(md_dir), config.chunk_size)
    
    # 显示存入统计
    console.print("\n[bold]存入统计:[/bold]")
    console.print(f"  总文件数: {stats['total']}")
    console.print(f"  成功: [green]{stats['success']}[/green]")
    console.print(f"  失败: [red]{stats['failed']}[/red]")
    console.print(f"  总向量块数: {stats['total_chunks']}")
    
    # 步骤 3: 验证
    verify_collections(qdrant, stats['success'])
    
    # 步骤 4: 测试搜索
    test_search(qdrant)
    
    # 完成
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✓ 数据重置和导入完成！[/bold green]\n"
        f"[dim]成功导入 {stats['success']} 个文件，共 {stats['total_chunks']} 个向量块[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
