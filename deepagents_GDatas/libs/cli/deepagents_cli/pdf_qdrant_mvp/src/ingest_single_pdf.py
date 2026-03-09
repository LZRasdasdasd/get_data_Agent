"""
单个 PDF 文件存入脚本

专门用于存入指定的单个PDF文件
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

from config import config
from pdf_tools import extract_text_from_pdf, chunk_text, sanitize_collection_name
from vector_tools import QdrantManager


# 初始化控制台
console = Console()


def ingest_single_pdf(pdf_path: str) -> bool:
    """
    存入单个PDF文件到Qdrant
    
    Args:
        pdf_path: PDF文件的完整路径
        
    Returns:
        bool: 是否成功
    """
    # 验证配置
    if not config.validate():
        console.print("[red]配置验证失败![/red]")
        return False
    
    # 初始化 Qdrant 管理器
    qdrant = QdrantManager()
    
    # 检查连接
    console.print("\n[bold]检查 Qdrant 连接...[/bold]")
    console.print("[green]Qdrant 连接成功![/green]")
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        console.print(f"[red]文件不存在: {pdf_path}[/red]")
        return False
    
    # 获取文件名
    filename = os.path.basename(pdf_path)
    console.print(f"\n[bold cyan]处理文件: {filename}[/bold cyan]")
    
    # 生成集合名称
    collection_name = sanitize_collection_name(filename)
    console.print(f"  集合名: {collection_name}")
    
    # 提取文本
    console.print("  提取文本...")
    text_result = extract_text_from_pdf(pdf_path)
    
    if not text_result or not text_result.get("success"):
        error_msg = text_result.get("error", "未知错误") if text_result else "提取失败"
        console.print(f"[red]  提取文本失败: {error_msg}[/red]")
        return False
    
    text = text_result.get("text", "")
    if not text or len(text) < 10:
        console.print(f"[red]  提取的文本过少 ({len(text)} 字符)[/red]")
        return False
    
    console.print(f"  提取到 {len(text)} 个字符")
    
    # 分块
    console.print(f"  分块 (大小: {config.chunk_size}, 重叠: {config.chunk_overlap})...")
    chunks = chunk_text(text, config.chunk_size, config.chunk_overlap)
    console.print(f"  分块: {len(chunks)} 个")
    
    # 创建集合
    console.print("  创建集合...")
    create_result = qdrant.create_collection(collection_name)
    
    if create_result.get("status") == "error":
        console.print(f"[red]  创建集合失败: {create_result.get('error')}[/red]")
        return False
    
    # 准备点数据
    console.print("  准备数据...")
    points = []
    for chunk in chunks:
        points.append({
            "text": chunk["text"],
            "chunk_index": chunk["chunk_index"],
            "source_file": filename
        })
    
    # 存入向量数据库
    console.print("  存入向量数据库...")
    result = qdrant.add_points(
        collection_name=collection_name,
        points=points,
        batch_size=10
    )
    
    if result.get("status") == "success":
        console.print(f"[green]  ✓ 成功: {len(chunks)} 个块[/green]")
        return True
    else:
        console.print("[red]  ✗ 存入失败[/red]")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="单个PDF文件存入工具")
    parser.add_argument("pdf_path", help="PDF文件的完整路径")
    
    args = parser.parse_args()
    
    # 显示标题
    console.print(Panel.fit(
        "[bold cyan]单个PDF存入工具[/bold cyan]",
        border_style="cyan"
    ))
    
    # 执行存入
    success = ingest_single_pdf(args.pdf_path)
    
    if success:
        console.print("\n[green bold]✓ 存入成功！[/green bold]")
        console.print(f"\n您可以使用以下命令查询:")
        collection_name = sanitize_collection_name(os.path.basename(args.pdf_path))
        console.print(f"  python src/query_pdfs.py --collection {collection_name} --query \"您的查询\"")
        sys.exit(0)
    else:
        console.print("\n[red bold]✗ 存入失败[/red bold]")
        sys.exit(1)


if __name__ == "__main__":
    main()
