"""
PDF 数据存入脚本

扫描 PDF 目录，将所有 PDF 文件存入 Qdrant 向量数据库
"""

import os
import sys
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from config import config
from pdf_tools import extract_text_from_pdf, chunk_text, get_pdf_files, sanitize_collection_name
from vector_tools import QdrantManager


# 初始化控制台
console = Console()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF 数据存入工具 - 将 PDF 文件存入 Qdrant 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--pdf-dir", "-d",
        type=str,
        default=None,
        help="PDF 文件目录路径 (默认使用 .env 中的配置)"
    )
    
    parser.add_argument(
        "--chunk-size", "-s",
        type=int,
        default=None,
        help="文本块大小 (默认: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap", "-o",
        type=int,
        default=None,
        help="文本块之间的重叠 (默认: 200)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="只模拟运行，不实际存入"
    )
    
    args = parser.parse_args()
    
    # 加载配置
    if args.pdf_dir:
        config.pdf_dir = args.pdf_dir
    
    if not config.validate():
        console.print("[red]配置验证失败![/red]")
        console.print(config)
        sys.exit(1)
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]PDF 数据存入工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"PDF 目录: {config.pdf_dir}")
    console.print(f"Qdrant 地址: {config.qdrant_url}")
    console.print(f"块大小: {args.chunk_size or config.chunk_size}")
    console.print(f"块重叠: {args.chunk_overlap or config.chunk_overlap}")
    
    # 初始化 Qdrant 管理器
    qdrant = QdrantManager()
    
    # 开始前检查连接
    console.print("\n[bold]检查 Qdrant 连接...[/bold]")
    console.print("[green]Qdrant 连接成功![/green]")
    
    # 获取 PDF 文件列表
    pdf_files = get_pdf_files(config.pdf_dir)
    
    if not pdf_files:
        console.print(f"[red]未找到 PDF 文件: {config.pdf_dir}[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold]找到 {len(pdf_files)} 个 PDF 文件[/bold]")
    
    # 干运行模式
    if args.dry_run:
        console.print("[yellow]干运行模式 - 不会实际存入数据[/yellow]")
        console.print("=" * 60)
        return
    
    # 存入统计
    stats = {
        "total": len(pdf_files),
        "success": 0,
        "failed": 0,
        "total_chunks": 0,
        "collections": []
    }
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]处理 PDF 文件...", 
            total=len(pdf_files)
        )
        
        for i in range(len(pdf_files)):
            pdf_file = pdf_files[i]
            
            # 更新进度
            progress.update(overall_task, advance=1)
            
            # 获取集合名称
            collection_name = sanitize_collection_name(pdf_file["name"])
            
            console.print(f"\n[{i+1}/{len(pdf_files)}] 处理: {pdf_file['name']}")
            console.print(f"  集合名: {collection_name}")
            
            # 确保集合存在
            create_result = qdrant.create_collection(collection_name)
            if create_result["status"] == "error":
                console.print(f"  [red]创建集合失败: {create_result.get('error')}[/red]")
                stats["failed"] += 1
                continue
            elif create_result["status"] == "created":
                console.print(f"  [dim]创建新集合[/dim]")
            
            # 提取文本
            pdf_result = extract_text_from_pdf(pdf_file["path"])
            
            if not pdf_result["success"]:
                console.print(f"  [red]读取失败: {pdf_result.get('error')}[/red]")
                stats["failed"] += 1
                continue
            
            console.print(f"  提取到 {pdf_result['char_count']} 个字符")
            
            # 分块
            chunks = chunk_text(
                pdf_result["text"], 
                args.chunk_size or config.chunk_size, 
                args.chunk_overlap or config.chunk_overlap
            )
            
            console.print(f"  分块: {len(chunks)} 个")
            
            # 存入向量
            result = qdrant.add_points(
                collection_name=collection_name,
                points=chunks,
                batch_size=10
            )
            
            if result["status"] == "success":
                stats["success"] += 1
                stats["total_chunks"] += len(chunks)
                stats["collections"].append({
                    "name": collection_name,
                    "chunks": len(chunks)
                })
                console.print(f"  [green]成功: {len(chunks)} 个块[/green]")
            else:
                stats["failed"] += 1
                console.print(f"  [red]存入失败: {result.get('error')}[/red]")
    
    # 显示统计
    console.print("\n")
    console.print("=" * 60)
    console.print(Panel.fit(
        "[bold green]存入完成统计[/bold green]",
        border_style="green"
    ))
    
    # 创建统计表格
    table = Table(show_header=True, header_style="bold")
    table.add_column("统计项", style="cyan")
    table.add_column("值", style="green")
    table.add_row("总文件数", str(stats["total"]))
    table.add_row("成功", str(stats["success"]))
    table.add_row("失败", str(stats["failed"]))
    table.add_row("总块数", str(stats["total_chunks"]))
    
    console.print(table)
    
    # 显示集合列表
    if stats["collections"]:
        console.print("\n[bold]创建的集合:[/bold]")
        for col in stats["collections"]:
            console.print(f"  - {col['name']}: {col['chunks']} 个块")
    
    # 提示访问 Qdrant Dashboard
    console.print("\n")
    console.print(Panel(
        "[bold cyan]访问 Qdrant Dashboard[/bold cyan]\n\n"
        "地址: http://localhost:6333/dashboard\n\n"
        "可以在 Dashboard 中查看和管理数据。",
        border_style="cyan"
    ))
    
    # 提示如何使用命令行查询
    console.print(Panel(
        "[bold yellow]使用方法[/bold yellow]\n\n"
        "查询数据:\n"
        "  python src/query_pdfs.py --collection <集合名> --query <查询文本>\n\n"
        "列出所有集合:\n"
        "  python src/query_pdfs.py --list",
        border_style="yellow"
    ))


if __name__ == "__main__":
    main()
