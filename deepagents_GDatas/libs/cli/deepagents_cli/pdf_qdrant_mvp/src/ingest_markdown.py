"""
Markdown 数据存入脚本

扫描 markdown_docs 目录，将所有 Markdown 文件存入 Qdrant 向量数据库
"""

import os
import re
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
from vector_tools import QdrantManager


# 初始化控制台
console = Console()


def sanitize_collection_name(filename: str) -> str:
    """
    将文件名转换为合法的 Qdrant 集合名称
    
    规则:
    1. 移除 .md 扩展名
    2. 转换为小写
    3. 空格和特殊字符替换为下划线
    4. 截断到 50 个字符
    """
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


def get_markdown_files(md_dir: str) -> list:
    """
    获取目录下所有 Markdown 文件
    
    Args:
        md_dir: Markdown 文件目录
        
    Returns:
        list: 文件信息列表
    """
    md_path = Path(md_dir)
    
    if not md_path.exists():
        console.print(f"[red]目录不存在: {md_dir}[/red]")
        return []
    
    files = []
    for md_file in sorted(md_path.glob("*.md")):
        files.append({
            "name": md_file.name,
            "path": str(md_file.absolute()),
            "collection_name": sanitize_collection_name(md_file.name)
        })
    
    return files


def read_markdown_file(md_path: str) -> dict:
    """
    读取 Markdown 文件内容
    
    Args:
        md_path: Markdown 文件路径
        
    Returns:
        dict: 包含内容和元数据的字典
    """
    result = {
        "text": "",
        "char_count": 0,
        "success": False,
        "error": None
    }
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            result["text"] = content
            result["char_count"] = len(content)
            result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    
    return result


def is_heading(paragraph: str) -> bool:
    """
    判断段落是否为Markdown标题
    
    Args:
        paragraph: 段落文本
        
    Returns:
        bool: 是否为标题
    """
    stripped = paragraph.strip()
    # Markdown 标题以 # 开头
    if stripped.startswith('#'):
        return True
    # 也检测一些常见的小标题格式（全大写、短行等）
    if len(stripped) < 50 and stripped.isupper():
        return True
    return False


def split_paragraph_at_period(paragraph: str) -> tuple:
    """
    在句号位置将段落分成两块
    
    Args:
        paragraph: 段落文本
        
    Returns:
        tuple: (前半部分, 后半部分)
    """
    # 查找所有句号位置（包括中英文句号）
    period_positions = []
    for i, char in enumerate(paragraph):
        if char in ['。', '.']:
            period_positions.append(i)
    
    # 如果没有句号，返回整个段落
    if not period_positions:
        return paragraph, ""
    
    # 找到中间位置的句号（尽可能接近中间）
    mid_point = len(paragraph) // 2
    best_pos = period_positions[0]
    min_dist = abs(period_positions[0] - mid_point)
    
    for pos in period_positions:
        dist = abs(pos - mid_point)
        if dist < min_dist:
            min_dist = dist
            best_pos = pos
    
    # 在句号后分割（包含句号）
    first_part = paragraph[:best_pos + 1].strip()
    second_part = paragraph[best_pos + 1:].strip()
    
    return first_part, second_part


def merge_small_paragraphs(paragraphs: list, min_chars: int = 100) -> list:
    """
    合并小段落：如果段落字数太少则向下合并，小标题合并到下一段落
    
    Args:
        paragraphs: 段落列表
        min_chars: 最小字符数（默认100）
        
    Returns:
        list: 合并后的段落列表
    """
    if not paragraphs:
        return []
    
    merged = []
    i = 0
    
    while i < len(paragraphs):
        current_para = paragraphs[i].strip()
        
        if not current_para:
            i += 1
            continue
        
        # 检查是否为标题
        is_title = is_heading(current_para)
        
        # 如果是标题或段落太小，尝试与下一段合并
        if is_title or len(current_para) < min_chars:
            # 收集需要合并的段落
            combined = current_para
            
            # 向下查找可以合并的段落
            j = i + 1
            while j < len(paragraphs):
                next_para = paragraphs[j].strip()
                
                if not next_para:
                    j += 1
                    continue
                
                # 如果下一段也是标题或也很小，继续合并
                if is_heading(next_para) or len(next_para) < min_chars:
                    combined += "\n\n" + next_para
                    j += 1
                else:
                    # 找到了足够大的段落，合并后退出
                    combined += "\n\n" + next_para
                    j += 1
                    break
            
            merged.append(combined)
            i = j
        else:
            # 段落足够大，直接添加
            merged.append(current_para)
            i += 1
    
    return merged


def chunk_markdown(text: str, chunk_size: int = 1000, overlap: int = 200, min_chunk_size: int = 500) -> list:
    """
    将 Markdown 文本分割成块（优化版）
    
    分块规则：
    1. 每一段分成两块，在句号位置分开
    2. 如果段落字数太少则合并段落
    3. 小标题一律合并到下一段落
    4. 如果每一段都只有不超过100字符则向下合并
    
    Args:
        text: Markdown 文本
        chunk_size: 每个块的最大字符数（默认1000，用于参考）
        overlap: 块之间的重叠字符数（保留接口兼容，暂未使用）
        min_chunk_size: 每个块的最小字符数（默认500）
        
    Returns:
        list: 文本块列表
    """
    if not text:
        return []
    
    # 按段落分割（Markdown 用 \n\n 分割段落）
    paragraphs = text.split('\n\n')
    
    # 第一步：合并小段落和标题
    merged_paragraphs = merge_small_paragraphs(paragraphs, min_chars=100)
    
    raw_chunks = []
    
    # 第二步：对每个合并后的段落进行分割
    for para in merged_paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果段落很大，在句号位置分成两块
        if len(para) > chunk_size:
            first_part, second_part = split_paragraph_at_period(para)
            
            if first_part:
                raw_chunks.append({
                    "text": first_part,
                    "chunk_index": len(raw_chunks),
                    "char_count": len(first_part)
                })
            
            # 如果后半部分仍然很大，递归分割
            remaining = second_part
            while len(remaining) > chunk_size:
                first_part, remaining = split_paragraph_at_period(remaining)
                if first_part:
                    raw_chunks.append({
                        "text": first_part,
                        "chunk_index": len(raw_chunks),
                        "char_count": len(first_part)
                    })
            
            if remaining:
                raw_chunks.append({
                    "text": remaining,
                    "chunk_index": len(raw_chunks),
                    "char_count": len(remaining)
                })
        else:
            # 段落大小合适，直接作为一个块
            raw_chunks.append({
                "text": para,
                "chunk_index": len(raw_chunks),
                "char_count": len(para)
            })
    
    # 第三步：后处理，合并仍然太小的块
    final_chunks = []
    temp_text = ""
    
    for chunk in raw_chunks:
        text = chunk["text"]
        
        if not temp_text:
            temp_text = text
            continue
        
        # 如果当前累积的块太小，继续合并
        if len(temp_text) < min_chunk_size:
            temp_text += "\n\n" + text
        else:
            # 当前块已经足够大，保存它
            final_chunks.append({
                "text": temp_text,
                "chunk_index": len(final_chunks),
                "char_count": len(temp_text)
            })
            temp_text = text
    
    # 处理最后剩余的文本
    if temp_text:
        # 如果最后一块太小，尝试与前一个块合并
        if len(temp_text) < min_chunk_size and final_chunks:
            final_chunks[-1]["text"] += "\n\n" + temp_text
            final_chunks[-1]["char_count"] = len(final_chunks[-1]["text"])
        else:
            final_chunks.append({
                "text": temp_text,
                "chunk_index": len(final_chunks),
                "char_count": len(temp_text)
            })
    
    # 重新编号
    for i, chunk in enumerate(final_chunks):
        chunk["chunk_index"] = i
    
    return final_chunks


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Markdown 数据存入工具 - 将 Markdown 文件存入 Qdrant 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--md-dir", "-d",
        type=str,
        default="markdown_docs",
        help="Markdown 文件目录路径 (默认: markdown_docs)"
    )
    
    parser.add_argument(
        "--chunk-size", "-s",
        type=int,
        default=1000,
        help="文本块大小 (默认: 1000)"
    )
    
    parser.add_argument(
        "--chunk-overlap", "-o",
        type=int,
        default=200,
        help="文本块之间的重叠 (默认: 200)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="只模拟运行，不实际存入"
    )
    
    args = parser.parse_args()
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]Markdown 数据存入工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"Markdown 目录: {args.md_dir}")
    console.print(f"Qdrant 地址: {config.qdrant_url}")
    console.print(f"块大小: {args.chunk_size}")
    console.print(f"块重叠: {args.chunk_overlap}")
    
    # 初始化 Qdrant 管理器
    console.print("\n[bold]连接 Qdrant...[/bold]")
    qdrant = QdrantManager()
    
    # 获取 Markdown 文件列表
    md_files = get_markdown_files(args.md_dir)
    
    if not md_files:
        console.print(f"[red]未找到 Markdown 文件: {args.md_dir}[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold]找到 {len(md_files)} 个 Markdown 文件[/bold]")
    
    # 干运行模式
    if args.dry_run:
        console.print("[yellow]干运行模式 - 不会实际存入数据[/yellow]")
        for md_file in md_files:
            console.print(f"  - {md_file['name']} -> {md_file['collection_name']}")
        return
    
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
            "[cyan]处理 Markdown 文件...", 
            total=len(md_files)
        )
        
        for i in range(len(md_files)):
            md_file = md_files[i]
            
            # 更新进度
            progress.update(overall_task, advance=1)
            
            # 获取集合名称
            collection_name = md_file["collection_name"]
            
            console.print(f"\n[{i+1}/{len(md_files)}] 处理: {md_file['name']}")
            console.print(f"  集合名: {collection_name}")
            
            # 确保集合存在
            create_result = qdrant.create_collection(collection_name)
            if create_result["status"] == "error":
                console.print(f"  [red]创建集合失败: {create_result.get('error')}[/red]")
                stats["failed"] += 1
                continue
            elif create_result["status"] == "created":
                console.print(f"  [dim]创建新集合[/dim]")
            
            # 读取 Markdown 文件
            md_result = read_markdown_file(md_file["path"])
            
            if not md_result["success"]:
                console.print(f"  [red]读取失败: {md_result.get('error')}[/red]")
                stats["failed"] += 1
                continue
            
            console.print(f"  提取到 {md_result['char_count']} 个字符")
            
            # 分块
            chunks = chunk_markdown(
                md_result["text"], 
                args.chunk_size, 
                args.chunk_overlap
            )
            
            console.print(f"  分块: {len(chunks)} 个")
            
            if not chunks:
                console.print(f"  [yellow]警告: 没有生成任何文本块[/yellow]")
                stats["failed"] += 1
                continue
            
            # 为每个块添加源文件信息
            for chunk in chunks:
                chunk["source_file"] = md_file["name"]
            
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
