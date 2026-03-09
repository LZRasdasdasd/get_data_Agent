"""
继续导入剩余 Markdown 数据的脚本

只导入尚未存入数据库的 Markdown 文件
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


def get_existing_collections(qdrant: QdrantManager) -> set:
    """获取已存在的集合名称"""
    collections = qdrant.list_collections()
    return {col['name'] for col in collections}


def ingest_remaining_markdown(qdrant: QdrantManager, md_dir: str, chunk_size: int) -> dict:
    """
    只导入尚未存入数据库的 Markdown 文件
    
    Args:
        qdrant: Qdrant 管理器实例
        md_dir: Markdown 文件目录
        chunk_size: 分块大小
        
    Returns:
        dict: 存入统计信息
    """
    console.print("\n[bold yellow]继续导入剩余的 Markdown 文件[/bold yellow]")
    console.print(f"[cyan]  Markdown 目录: {md_dir}[/cyan]")
    console.print(f"[cyan]  分块大小: {chunk_size} 字符[/cyan]")
    
    # 获取所有 Markdown 文件
    all_md_files = get_markdown_files(md_dir)
    
    if not all_md_files:
        console.print(f"[red]  未找到 Markdown 文件: {md_dir}[/red]")
        return {"total": 0, "success": 0, "failed": 0, "total_chunks": 0, "skipped": 0}
    
    # 获取已存在的集合
    existing_collections = get_existing_collections(qdrant)
    console.print(f"[cyan]  已存在 {len(existing_collections)} 个集合[/cyan]")
    
    # 过滤出需要导入的文件
    md_files_to_ingest = []
    for md_file in all_md_files:
        if md_file["collection_name"] not in existing_collections:
            md_files_to_ingest.append(md_file)
        else:
            console.print(f"  [green]✓[/green] 跳过已存在: {md_file['name']}")
    
    if not md_files_to_ingest:
        console.print("[green]  所有文件都已导入，无需处理[/green]")
        return {"total": len(all_md_files), "success": 0, "failed": 0, "total_chunks": 0, "skipped": len(all_md_files)}
    
    console.print(f"[cyan]  需要导入 {len(md_files_to_ingest)} 个文件[/cyan]")
    
    # 存入统计
    stats = {
        "total": len(all_md_files),
        "success": 0,
        "failed": 0,
        "total_chunks": 0,
        "skipped": len(all_md_files) - len(md_files_to_ingest),
        "collections": []
    }
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]处理文件...", 
            total=len(md_files_to_ingest)
        )
        
        for md_file in md_files_to_ingest:
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
                console.print(f"  [green]✓[/green] 成功: {md_file['name']} ({add_result['points_added']} 块)")
            else:
                console.print(f"  [red]✗[/red] 添加向量失败: {collection_name}")
                stats["failed"] += 1
            
            progress.update(overall_task, advance=1)
    
    return stats


def verify_all_collections(qdrant: QdrantManager, expected_count: int) -> bool:
    """
    验证所有集合都已成功创建
    
    Args:
        qdrant: Qdrant 管理器实例
        expected_count: 预期的集合数量
        
    Returns:
        bool: 验证是否通过
    """
    console.print("\n[bold yellow]验证数据存储[/bold yellow]")
    
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
        table.add_row(col['name'][:50], str(points_count), status)
    
    console.print(table)
    console.print(f"[green]  总向量点数: {total_points}[/green]")
    
    if len(collections) >= expected_count:
        console.print(f"[bold green]✓ 验证通过！所有 {len(collections)} 个集合都已成功创建[/bold green]")
        return True
    else:
        console.print(f"[bold yellow]⚠ 部分完成：{len(collections)}/{expected_count} 个集合已创建[/bold yellow]")
        return False


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold cyan]继续导入剩余数据[/bold cyan]\n"
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
    
    # 导入剩余文件
    stats = ingest_remaining_markdown(qdrant, str(md_dir), config.chunk_size)
    
    # 显示存入统计
    console.print("\n[bold]存入统计:[/bold]")
    console.print(f"  总文件数: {stats['total']}")
    console.print(f"  本次成功: [green]{stats['success']}[/green]")
    console.print(f"  本次失败: [red]{stats['failed']}[/red]")
    console.print(f"  已跳过: [yellow]{stats['skipped']}[/yellow]")
    console.print(f"  新增向量块数: {stats['total_chunks']}")
    
    # 验证
    verify_all_collections(qdrant, 10)  # 预期10个集合
    
    # 完成
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold green]✓ 导入完成！[/bold green]\n"
        f"[dim]本次新增 {stats['success']} 个文件，共 {stats['total_chunks']} 个向量块[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
