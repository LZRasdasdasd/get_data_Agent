"""
文本分块工具模块

核心功能：Text Chunking / 文本分块
- 将长文本智能分割成适当大小的块，以便进行向量嵌入和语义搜索
- 采用智能分块策略：在句号位置分割、合并小段落、保留标题上下文

这是向量数据库存储流程中的独立工具，只负责文本分块操作
分块后的文本可通过 vector_store_tool.py 存入 Qdrant 向量数据库

Use this tool when you need to:
- Chunk text / 分块文本：将长文档分割成小块
- Split long Markdown documents into chunks for vector embedding
- Prepare text data for semantic search
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table


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


def chunk_text(
    text: str, 
    chunk_size: int = 1000, 
    overlap: int = 200, 
    min_chunk_size: int = 500
) -> List[Dict[str, Any]]:
    """
    【文本分块工具】将 Markdown 文本智能分割成适合向量嵌入的文本块。
    
    核心功能：Text Chunking / 文本分块
    - 将长文本分割成适当大小的块，以便进行向量嵌入和语义搜索
    - 采用智能分块策略：在句号位置分割、合并小段落、保留标题上下文
    
    这是向量数据库存储流程中的第一步：文本分块 (Text Chunking)
    分块后的文本将通过 vector_store_tool 存入 Qdrant 向量数据库
    
    Use this tool when you need to:
    - Chunk text / 分块文本：将长文档分割成小块
    - Split long Markdown documents into chunks for vector embedding
    - Prepare text data for semantic search in Qdrant
    
    Args:
        text: 要分割的 Markdown 文本内容
        chunk_size: 每个块的目标最大字符数，默认 1000
        overlap: 块之间的重叠字符数（保留参数，当前未使用），默认 200
        min_chunk_size: 每个块的最小字符数，默认 500，小于此值的块会被合并
        
    Returns:
        list: 文本块列表，每个元素是包含以下字段的字典：
            - text (str): 文本块内容
            - chunk_index (int): 块的索引位置
            - char_count (int): 该块的字符数
    
    Example:
        >>> chunks = chunk_text("# Title\\n\\nContent...", chunk_size=800)
        >>> print(len(chunks))  # 分块数量
        >>> print(chunks[0]["text"])  # 第一个块的内容
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
        chunk_text = chunk["text"]
        
        if not temp_text:
            temp_text = chunk_text
            continue
        
        # 如果当前累积的块太小，继续合并
        if len(temp_text) < min_chunk_size:
            temp_text += "\n\n" + chunk_text
        else:
            # 当前块已经足够大，保存它
            final_chunks.append({
                "text": temp_text,
                "chunk_index": len(final_chunks),
                "char_count": len(temp_text)
            })
            temp_text = chunk_text
    
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


def chunk_single_file(
    md_path: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 500
) -> Dict[str, Any]:
    """
    对单个 Markdown 文件进行分块
    
    Args:
        md_path: Markdown 文件路径
        chunk_size: 目标块大小
        overlap: 块之间的重叠
        min_chunk_size: 最小块大小
        
    Returns:
        dict: 包含分块结果和元数据的字典
    """
    result = {
        "success": False,
        "file_path": md_path,
        "file_name": Path(md_path).name,
        "collection_name": sanitize_collection_name(Path(md_path).name),
        "chunks": [],
        "char_count": 0,
        "chunk_count": 0,
        "error": None
    }
    
    # 读取文件
    read_result = read_markdown_file(md_path)
    if not read_result["success"]:
        result["error"] = read_result["error"]
        return result
    
    text = read_result["text"]
    result["char_count"] = read_result["char_count"]
    
    # 分块
    chunks = chunk_text(text, chunk_size, overlap, min_chunk_size)
    
    # 为每个块添加源文件信息
    for chunk in chunks:
        chunk["source_file"] = result["file_name"]
    
    result["chunks"] = chunks
    result["chunk_count"] = len(chunks)
    result["success"] = True
    
    return result


def chunk_all_files(
    md_dir: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 500
) -> Dict[str, Any]:
    """
    对目录下所有 Markdown 文件进行分块
    
    Args:
        md_dir: Markdown 文件目录
        chunk_size: 目标块大小
        overlap: 块之间的重叠
        min_chunk_size: 最小块大小
        
    Returns:
        dict: 包含所有文件分块结果的字典
    """
    result = {
        "success": True,
        "md_dir": md_dir,
        "total_files": 0,
        "success_count": 0,
        "failed_count": 0,
        "total_chunks": 0,
        "files": []
    }
    
    # 获取所有 Markdown 文件
    md_files = get_markdown_files(md_dir)
    
    if not md_files:
        result["success"] = False
        result["error"] = f"未找到 Markdown 文件: {md_dir}"
        return result
    
    result["total_files"] = len(md_files)
    
    # 处理每个文件
    for md_file in md_files:
        file_result = chunk_single_file(
            md_file["path"],
            chunk_size,
            overlap,
            min_chunk_size
        )
        
        if file_result["success"]:
            result["success_count"] += 1
            result["total_chunks"] += file_result["chunk_count"]
        else:
            result["failed_count"] += 1
        
        result["files"].append(file_result)
    
    return result


def main():
    """
    命令行入口：文本分块工具
    
    用于对 Markdown 文件进行智能分块，不涉及向量数据库操作
    """
    parser = argparse.ArgumentParser(
        description="文本分块工具 - 将 Markdown 文件智能分割成文本块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--md-dir", "-d",
        type=str,
        default="markdown_docs",
        help="Markdown 文件目录路径 (默认: markdown_docs)"
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="单个 Markdown 文件路径（如果指定，则只处理该文件）"
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
        "--min-chunk-size", "-m",
        type=int,
        default=500,
        help="最小文本块大小 (默认: 500)"
    )
    
    parser.add_argument(
        "--output", "-O",
        type=str,
        default=None,
        help="输出 JSON 文件路径（可选）"
    )
    
    args = parser.parse_args()
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]文本分块工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"块大小: {args.chunk_size}")
    console.print(f"块重叠: {args.chunk_overlap}")
    console.print(f"最小块大小: {args.min_chunk_size}")
    
    # 处理单个文件或目录
    if args.file:
        console.print(f"\n[bold]处理单个文件: {args.file}[/bold]")
        result = chunk_single_file(
            args.file,
            args.chunk_size,
            args.chunk_overlap,
            args.min_chunk_size
        )
        
        if result["success"]:
            console.print(f"  [green]成功: {result['chunk_count']} 个块[/green]")
            console.print(f"  字符数: {result['char_count']}")
            console.print(f"  集合名: {result['collection_name']}")
        else:
            console.print(f"  [red]失败: {result.get('error')}[/red]")
    else:
        console.print(f"\n[bold]处理目录: {args.md_dir}[/bold]")
        result = chunk_all_files(
            args.md_dir,
            args.chunk_size,
            args.chunk_overlap,
            args.min_chunk_size
        )
        
        console.print(f"\n找到 {result['total_files']} 个文件")
        console.print(f"成功: {result['success_count']}")
        console.print(f"失败: {result['failed_count']}")
        console.print(f"总块数: {result['total_chunks']}")
    
    # 保存输出
    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]结果已保存到: {args.output}[/green]")
    
    return result


if __name__ == "__main__":
    main()
