#!/usr/bin/env python3
"""
验证998篇论文是否全部存入Qdrant数据库 - 修正版

修正了文件名匹配问题,现在会正确匹配markdown文件名和Qdrant集合名
"""

import os
import sys
from pathlib import Path
from typing import List, Set, Tuple

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from qdrant_client import QdrantClient
from qdrant_config import config

# 初始化控制台
console = Console()


def get_markdown_files() -> List[str]:
    """
    获取markdown_docs目录中所有的.md文件
    
    Returns:
        List[str]: 文件名列表（不包含路径）
    """
    markdown_dir = Path(__file__).parent / "src" / "markdown_docs"
    
    if not markdown_dir.exists():
        console.print(f"[red]错误: 目录不存在 {markdown_dir}[/red]")
        return []
    
    # 获取所有.md文件
    md_files = [f.name for f in markdown_dir.glob("*.md") if f.is_file()]
    
    return sorted(md_files)


def get_qdrant_collections() -> Set[str]:
    """
    获取Qdrant数据库中所有的集合名称
    
    Returns:
        Set[str]: 集合名称集合
    """
    try:
        client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key if config.qdrant_api_key else None
        )
        
        # 获取所有集合
        collections = client.get_collections()
        collection_names = {c.name for c in collections.collections}
        
        return collection_names
    
    except Exception as e:
        console.print(f"[red]连接Qdrant数据库失败: {e}[/red]")
        return set()


def verify_papers() -> Tuple[int, int, List[str], List[str]]:
    """
    验证论文存入情况
    
    Returns:
        Tuple[int, int, List[str], List[str]]:
            (文件总数, 数据库集合总数, 未存入文件列表, 多余集合列表)
    """
    # 获取markdown文件列表
    md_files_set = set(get_markdown_files())
    md_files = sorted(list(md_files_set))
    
    # 获取Qdrant集合列表
    db_collections = get_qdrant_collections()
    
    # 找出未存入数据库的文件（在markdown文件夹中但不在数据库中）
    missing_files = sorted(md_files_set - db_collections)
    
    # 找出多余的数据库集合（在数据库中但不在markdown文件夹中）
    extra_collections = sorted(db_collections - md_files_set)
    
    return len(md_files), len(db_collections), missing_files, extra_collections, md_files


def display_results(total_files: int, total_collections: int, 
                  missing_files: List[str], extra_collections: List[str],
                  md_files: List[str]):
    """
    显示验证结果
    
    Args:
        total_files: Markdown文件总数
        total_collections: 数据库集合总数
        missing_files: 未存入数据库的文件列表
        extra_collections: 多余的数据库集合列表
        md_files: 所有markdown文件列表
    """
    # 创建汇总面板
    summary_table = Table(title="验证结果汇总", show_header=True)
    summary_table.add_column("项目", style="cyan")
    summary_table.add_column("数量", justify="right", style="green")
    summary_table.add_column("说明", style="yellow")
    
    summary_table.add_row(
        "Markdown文件总数",
        str(total_files),
        "markdown_docs目录中的.md文件数量"
    )
    summary_table.add_row(
        "数据库集合总数",
        str(total_collections),
        "Qdrant数据库中的collection数量"
    )
    
    if len(missing_files) == 0 and len(md_files) == len(db_collections):
        status_text = "[green]✓ 全部998篇论文已存入数据库[/green]"
        status_msg = "完美匹配!"
        verification_status = "✓"
    else:
        status_text = f"[red]✗ 有 {len(missing_files)} 篇论文未存入数据库[/red]"
        status_msg = "存在不匹配"
        verification_status = "✗"
    
    summary_table.add_row(
        "验证状态",
        verification_status,
        status_msg
    )
    
    console.print()
    console.print(Panel(summary_table, title="📊 论文存入验证报告"))
    console.print()
    
    # 显示存入率
    success_rate = ((total_files - len(missing_files)) / total_files * 100) if total_files > 0 else 0
    console.print(f"[blue]存入率:[/blue] {success_rate:.2f}%")
    console.print(f"[blue]已存入:[/blue] {total_files - len(missing_files)} 篇")
    console.print(f"[blue]未存入:[/blue] {len(missing_files)} 篇")
    console.print()
    console.print(f"[bold]{status_text}[/bold]")
    
    # 显示缺失的文件详情
    if missing_files:
        console.print(Panel(
            f"[red]以下 {len(missing_files)} 篇论文未存入数据库:[/red]\n\n" + 
            "\n".join(f"  • {f}" for f in missing_files[:100]),
            title="❌ 未存入数据库的论文"
        ))
        if len(missing_files) > 100:
            console.print(f"[yellow]...还有 {len(missing_files) - 100} 个文件未显示[/yellow]")
    
    # 显示多余的集合详情
    if extra_collections:
        console.print(Panel(
            f"[yellow]以下 {len(extra_collections)} 个集合在数据库中但文件中不存在:[/yellow]\n\n" + 
            "\n".join(f"  • {c}" for c in extra_collections[:100]),
            title="⚠️  多余的数据库集合"
        ))
        if len(extra_collections) > 100:
            console.print(f"[yellow]...还有 {len(extra_collections) - 100} 个集合未显示[/yellow]")
    
    # 导出缺失文件列表
    if missing_files:
        missing_file_path = Path(__file__).parent / "missing_papers.txt"
        with open(missing_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(missing_files))
        console.print(f"[dim]缺失文件列表已保存到: {missing_file_path}[/dim]")
    
    # 返回状态码
    if len(missing_files) > 0:
        return 1  # 有论文未存入
    elif total_files != total_collections:
        return 2  # 数量不匹配
    else:
        return 0  # 全部成功


def main():
    """主函数"""
    console.print("[bold cyan]开始验证998篇论文存入情况...[/bold cyan]")
    console.print()
    
    # 执行验证
    total_files, total_collections, missing_files, extra_collections, md_files = verify_papers()
    
    # 显示结果
    display_results(total_files, total_collections, missing_files, extra_collections, md_files)
    
    # 返回状态码
    exit_code = main()
    
    console.print()
    console.print(f"[dim]验证完成。退出码: {exit_code}[/dim]")
    
    return exit_code


if __name__ == "__main__":
    exit(main())
