"""
验证998篇论文是否全部存入数据库
使用sanitize_collection_name函数正确匹配文件名和集合名
"""

import sys
from pathlib import Path
from typing import List, Set, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vector_tools import QdrantManager


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


def get_markdown_files() -> List[str]:
    """获取markdown_docs目录中所有的.md文件"""
    markdown_dir = Path(__file__).parent / "src" / "markdown_docs"
    md_files = [f.name for f in markdown_dir.glob("*.md") if f.is_file()]
    return sorted(md_files)


def get_qdrant_collections() -> Set[str]:
    """获取Qdrant数据库中的所有collection名称"""
    try:
        qdrant_manager = QdrantManager()
        collections = qdrant_manager.list_collections()
        return set(col['name'] for col in collections)
    except Exception as e:
        print(f"❌ 获取数据库集合失败: {e}")
        return set()


def verify_papers():
    """验证论文存入情况"""
    console = Console()
    
    console.print("\n[bold cyan]开始验证998篇论文存入情况...[/bold cyan]\n", style="cyan")
    
    # 获取文件和集合
    md_files = get_markdown_files()
    db_collections = get_qdrant_collections()
    
    # 将文件名转换为集合名进行匹配
    md_to_collection = {}
    for md_file in md_files:
        collection_name = sanitize_collection_name(md_file)
        md_to_collection[md_file] = collection_name
    
    # 检查匹配情况
    matched_files = []
    missing_files = []
    mismatched_files = []
    
    for md_file, expected_collection in md_to_collection.items():
        if expected_collection in db_collections:
            matched_files.append(md_file)
        else:
            missing_files.append(md_file)
    
    # 找出多余集合(在数据库中但文件中不存在)
    all_expected_collections = set(md_to_collection.values())
    extra_collections = db_collections - all_expected_collections
    
    # 统计
    total_md = len(md_files)
    total_db = len(db_collections)
    matched_count = len(matched_files)
    missing_count = len(missing_files)
    extra_count = len(extra_collections)
    
    # 计算存入率
    ingestion_rate = (matched_count / total_md * 100) if total_md > 0 else 0
    
    # 显示汇总表
    summary_table = Table(title="📊 论文存入验证报告", show_header=True, header_style="bold magenta")
    summary_table.add_column("项目", style="cyan", width=30)
    summary_table.add_column("数量", style="green", width=10)
    summary_table.add_column("说明", style="yellow")
    
    summary_table.add_row(
        "Markdown文件总数",
        f"{total_md}",
        "markdown_docs目录中的.md文件数量"
    )
    summary_table.add_row(
        "数据库集合总数",
        f"{total_db}",
        "Qdrant数据库中的collection数量"
    )
    
    # 验证状态
    if missing_count == 0 and extra_count == 0:
        status = "✓ 匹配成功"
        status_style = "bold green"
    else:
        status = "✗ 存在不匹配" if missing_count > 0 else "⚠ 存在多余集合"
        status_style = "bold red"
    
    summary_table.add_row("验证状态", status, "")
    console.print(summary_table)
    console.print()
    
    # 显示详细结果
    console.print(f"[bold]存入率:[/bold] {ingestion_rate:.2f}%")
    console.print(f"[bold green]已存入:[/bold green] {matched_count} 篇")
    console.print(f"[bold red]未存入:[/bold red] {missing_count} 篇" if missing_count > 0 else "[bold green]未存入:[/bold green] 0 篇")
    console.print(f"[bold yellow]多余集合:[/bold yellow] {extra_count} 个" if extra_count > 0 else "[bold green]多余集合:[/bold green] 0 个")
    console.print()
    
    # 显示缺失文件
    if missing_files:
        console.print(f"[bold red]✗ 有 {missing_count} 篇论文未存入数据库[/bold red]")
        console.print(Panel(
            "\n".join(f"  • {f}" for f in missing_files[:20]),
            title="❌ 未存入数据库的论文",
            border_style="red"
        ))
        if missing_count > 20:
            console.print(f"...还有 {missing_count - 20} 个文件未显示", style="yellow")
        console.print()
        
        # 保存缺失文件列表
        missing_file_path = Path(__file__).parent / "missing_papers_v3.txt"
        with open(missing_file_path, 'w', encoding='utf-8') as f:
            for file in sorted(missing_files):
                expected_col = sanitize_collection_name(file)
                f.write(f"{file} -> 集合名: {expected_col}\n")
        console.print(f"缺失文件列表已保存到: {missing_file_path}", style="cyan")
    
    # 显示多余集合
    if extra_collections:
        console.print(f"[bold yellow]⚠️  有 {extra_count} 个集合在数据库中但文件中不存在[/bold yellow]")
        console.print(Panel(
            "\n".join(f"  • {c}" for c in sorted(extra_collections)[:20]),
            title="⚠️  多余的数据库集合",
            border_style="yellow"
        ))
        if extra_count > 20:
            console.print(f"...还有 {extra_count - 20} 个集合未显示", style="yellow")
        console.print()
        
        # 保存多余集合列表
        extra_file_path = Path(__file__).parent / "extra_collections_v3.txt"
        with open(extra_file_path, 'w', encoding='utf-8') as f:
            for col in sorted(extra_collections):
                f.write(f"{col}\n")
        console.print(f"多余集合列表已保存到: {extra_file_path}", style="cyan")
    
    # 显示成功信息
    if missing_count == 0:
        console.print("[bold green]✓ 所有998篇论文都已成功存入数据库![/bold green]")
        console.print("[bold green]✓ 文件名与集合名完全匹配![/bold green]")
    
    # 返回结果
    return {
        "total_md": total_md,
        "total_db": total_db,
        "matched": matched_count,
        "missing": missing_count,
        "extra": extra_count,
        "status": "matched" if missing_count == 0 else "unmatched"
    }


if __name__ == "__main__":
    result = verify_papers()
    
    # 输出结果用于脚本调用
    print(f"\n验证结果: {result['status']}")
    print(f"合计: {result['matched']}/{result['total_md']} 篇已匹配")
