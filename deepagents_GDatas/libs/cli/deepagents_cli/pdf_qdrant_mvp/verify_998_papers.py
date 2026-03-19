#!/usr/bin/env python3
"""
验证998篇论文是否全部存入Qdrant数据库

脚本功能：
1. 统计markdown_docs目录中的所有.md文件数量
2. 连接Qdrant数据库，获取所有集合(collection)名称
3. 对比文件列表与数据库集合，找出缺失的论文
4. 输出详细验证报告
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
        
        collections = client.get_collections()
        collection_names = {c.name for c in collections.collections}
        
        return collection_names
    
    except Exception as e:
        console.print(f"[red]连接Qdrant数据库失败: {e}[/red]")
        return set()


def verify_papers() -> Tuple[int, int, List[str]]:
    """
    验证论文存入情况
    
    Returns:
        Tuple[int, int, List[str]]: 
            - markdown文件总数
            - 数据库集合总数
            - 未存入数据库的论文列表
    """
    # 获取markdown文件列表
    md_files = get_markdown_files()
    md_set = set(md_files)
    
    # 获取Qdrant集合列表
    db_collections = get_qdrant_collections()
    
    # 找出未存入数据库的论文
    missing_files = sorted(md_set - db_collections)
    
    # 找出多余的数据库集合（数据库中有但文件中没有的）
    extra_collections = sorted(db_collections - md_set)
    
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
    
    if len(missing_files) == 0 and total_files == total_collections:
        status_text = "[green]✓ 全部998篇论文已存入数据库[/green]"
        summary_table.add_row("验证状态", "✓", "完美匹配！")
    else:
        status_text = f"[red]✗ 有 {len(missing_files)} 篇论文未存入数据库[/red]"
        summary_table.add_row("验证状态", "✗", "存在不匹配")
    
    console.print()
    console.print(Panel(summary_table, title="📊 论文存入验证报告"))
    console.print()
    
    # 显示缺失的文件
    if missing_files:
        console.print(Panel(
            f"[red]以下 {len(missing_files)} 篇论文未存入数据库：[/red]\n\n" + 
            "\n".join(f"  • {f}" for f in missing_files[:50]),  # 最多显示前50个
            title="❌ 未存入数据库的论文"
        ))
        if len(missing_files) > 50:
            console.print(f"[yellow]...还有 {len(missing_files) - 50} 个文件未显示[/yellow]")
        console.print()
    
    # 显示多余的集合
    if extra_collections:
        console.print(Panel(
            f"[yellow]以下 {len(extra_collections)} 个集合在数据库中但文件中不存在：[/yellow]\n\n" + 
            "\n".join(f"  • {c}" for c in extra_collections[:20]),
            title="⚠️  多余的数据库集合"
        ))
        if len(extra_collections) > 20:
            console.print(f"[yellow]...还有 {len(extra_collections) - 20} 个集合未显示[/yellow]")
        console.print()
    
    # 显示统计信息
    success_rate = ((total_files - len(missing_files)) / total_files * 100) if total_files > 0 else 0
    
    console.print(f"[blue]存入率:[/blue] {success_rate:.2f}%")
    console.print(f"[blue]已存入:[/blue] {total_files - len(missing_files)} 篇")
    console.print(f"[blue]未存入:[/blue] {len(missing_files)} 篇")
    
    console.print()
    console.print(f"[bold]{status_text}[/bold]")
    
    # 如果存在缺失文件，导出缺失列表
    if missing_files:
        missing_file_path = Path(__file__).parent / "missing_papers.txt"
        with open(missing_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(missing_files))
        console.print(f"[dim]缺失文件列表已保存到: {missing_file_path}[/dim]")


def main():
    """主函数"""
    console.print("[bold cyan]开始验证998篇论文存入情况...[/bold cyan]")
    console.print()
    
    # 执行验证
    total_files, total_collections, missing_files, extra_collections, md_files = verify_papers()
    
    # 显示结果
    display_results(total_files, total_collections, missing_files, extra_collections, md_files)
    
    # 返回状态码
    if len(missing_files) > 0:
        return 1  # 有论文未存入
    elif total_files != total_collections:
        return 2  # 数量不匹配
    else:
        return 0  # 全部成功


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
