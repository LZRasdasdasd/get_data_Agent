"""
Markdown 文本分块与向量数据库存储工具

核心功能：
1. 文本分块 (Text Chunking) - 将长文本智能分割成适合向量嵌入的文本块
2. 向量存储 (Vector Storage) - 将分块后的文本存入 Qdrant 向量数据库

工作流程：
扫描 markdown_docs 目录 -> 读取 Markdown 文件 -> 智能分块 -> 生成向量嵌入 -> 存入 Qdrant

Use this tool when you need to:
- Chunk text into smaller pieces for vector embedding
- Store text chunks into Qdrant vector database
- Prepare documents for semantic search
"""

import os
import re
import sys
import logging
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from qdrant_config import config
from vector_tools import QdrantManager


# 初始化控制台
console = Console()

# 配置日志
logger = logging.getLogger(__name__)
def extract_paper_title(text: str, api_key: str, api_base: str, model: str = "qwen-plus") -> str | None:
    """
    使用 LLM 从论文 Markdown 内容中提取标题
    
    Args:
        text: Markdown 文本（建议传入前 2000 字符以节省 token）
        api_key: OpenAI 兼容 API 的密钥
        api_base: OpenAI 兼容 API 的基础 URL
        model: 使用的 LLM 模型名称，默认 qwen-plus
        
    Returns:
        str | None: 提取到的论文标题，失败时返回 None
    """
    if not text or not text.strip():
        return None
    
    try:
        client = OpenAI(api_key=api_key, base_url=api_base)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个学术论文标题提取助手。"
                        "从用户提供的论文文本中提取论文标题。"
                        "只返回标题的纯文本，不要包含任何其他内容（如引号、解释、前缀等）。"
                        "如果找不到明确的论文标题，返回空字符串。"
                    )
                },
                {
                    "role": "user",
                    "content": f"请从以下学术论文文本中提取论文标题：\n\n{text}"
                }
            ],
            temperature=0.1,
            max_tokens=200,
        )
        
        title = response.choices[0].message.content.strip() if response.choices else ""
        
        if not title:
            return None
        
        # 清理可能的多余标记
        title = title.strip('"\'""''`')
        if not title:
            return None
        
        logger.debug(f"LLM 提取标题成功: {title}")
        return title
        
    except Exception as e:
        logger.warning(f"LLM 提取标题失败: {e}")
        return None


def sanitize_collection_name(name: str, max_length: int = 80) -> str:
    """
    将文件名或标题转换为合法的 Qdrant 集合名称
    
    规则:
    1. 如果输入是文件名（含扩展名），先移除扩展名
    2. 转换为小写
    3. 非法字符（非小写字母、数字、下划线）替换为下划线
    4. 合并连续下划线
    5. 移除首尾下划线
    6. 截断到指定长度（默认 80 字符）
    7. 确保不为空
    """
    # 如果是文件名（含扩展名），移除扩展名
    if '.' in name and name.rsplit('.', 1)[-1].lower() in ('md', 'txt', 'pdf', 'docx'):
        name = Path(name).stem
    
    # 转小写
    name = name.lower()
    
    # 替换特殊字符为下划线（只保留小写字母、数字、下划线）
    name = re.sub(r'[^a-z0-9_]', '_', name)
    
    # 合并连续下划线
    name = re.sub(r'_+', '_', name)
    
    # 移除首尾下划线
    name = name.strip('_')
    
    # 截断到指定长度
    if len(name) > max_length:
        name = name[:max_length]
    
    # 确保不为空
    if not name:
        name = "unnamed_collection"
    
    return name


def get_markdown_files(md_dir: str, use_title: bool = True, model: str = "qwen-plus") -> list:
    """
    获取目录下所有 Markdown 文件，并为每个文件确定集合名称
    
    Args:
        md_dir: Markdown 文件目录
        use_title: 是否使用 LLM 从内容中提取标题作为集合名（默认 True）
        model: LLM 模型名称（默认 qwen-plus）
        
    Returns:
        list: 文件信息列表，每项包含 name, path, collection_name, title
    """
    md_path = Path(md_dir)
    
    if not md_path.exists():
        console.print(f"[red]目录不存在: {md_dir}[/red]")
        return []
    
    files = []
    for md_file in sorted(md_path.glob("*.md")):
        # 处理文件名：如果前缀包含"补充材料"，去掉前缀及后续分隔符
        raw_name = md_file.name
        stem = md_file.stem
        if stem.startswith("补充材料"):
            cleaned_stem = stem[len("补充材料"):].lstrip(" -_")
            raw_name = cleaned_stem + md_file.suffix if cleaned_stem else md_file.name
        
        file_info = {
            "name": md_file.name,
            "path": str(md_file.absolute()),
            "collection_name": sanitize_collection_name(raw_name),
            "title": None
        }
        
        # 如果启用标题提取模式，尝试从内容中提取标题
        if use_title:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    head_text = f.read(2000)
                
                title = extract_paper_title(
                    text=head_text,
                    api_key=config.openai_api_key,
                    api_base=config.openai_api_base,
                    model=model
                )
                
                if title:
                    collection_name = sanitize_collection_name(title)
                    file_info["title"] = title
                    file_info["collection_name"] = collection_name
                    console.print(f"  [green]提取标题:[/green] {title}")
                    console.print(f"  [dim]集合名:[/dim] {collection_name}")
                else:
                    console.print(f"  [yellow]标题提取失败，使用文件名作为集合名[/yellow]")
                    
            except Exception as e:
                logger.warning(f"处理文件 {md_file.name} 时出错: {e}")
                console.print(f"  [yellow]标题提取异常，使用文件名: {e}[/yellow]")
        
        files.append(file_info)
    
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
    【文本分块工具】将 Markdown 文本智能分割成适合向量嵌入的文本块。
    
    核心功能：Text Chunking / 文本分块
    - 将长文本分割成适当大小的块，以便进行向量嵌入和语义搜索
    - 采用智能分块策略：在句号位置分割、合并小段落、保留标题上下文
    
    这是向量数据库存储流程中的第一步：文本分块 (Text Chunking)
    分块后的文本将通过 embed_and_store() 存入 Qdrant 向量数据库
    
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
        >>> chunks = chunk_markdown("# Title\\n\\nContent...", chunk_size=800)
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
    """
    【分块并存入向量数据库】的主入口工具。
    
    核心功能：Text Chunking + Vector Database Storage
    ================================================
    步骤1: 文本分块 (Text Chunking)
        - 将 Markdown 文件智能分割成适当大小的文本块
        - 保持语义完整性，在句号位置分割、合并小段落
    
    步骤2: 向量存储 (Vector Storage)
        - 为每个文本块生成向量嵌入 (Embedding)
        - 将向量数据存入 Qdrant 向量数据库
        - 支持后续的语义搜索和检索
    
    Use this tool when you need to:
    - 分块文本并存入向量数据库 (Chunk text and store to vector database)
    - Ingest multiple Markdown files into Qdrant vector database
    - Batch process scientific papers converted to Markdown format
    - Prepare document corpus for semantic search and retrieval
    
    参数说明：
    - md-dir: Markdown 文件所在目录路径，默认为 'markdown_docs'
    - chunk-size: 每个文本块的目标最大字符数，默认为 1000
    - chunk-overlap: 文本块之间的重叠字符数，默认为 200
    - dry-run: 仅模拟运行，不实际存入数据库
    
    执行流程：
    1. 扫描指定目录下的所有 .md 文件
    2. 对每个文件进行智能分块（保持语义完整性）- chunk_markdown()
    3. 为每个文本块生成向量嵌入
    4. 将向量数据存入 Qdrant 集合 - qdrant.add_points()
    
    Returns:
        None: 该函数通过命令行参数运行，结果输出到控制台
        
    Example:
        >>> # 命令行调用方式
        >>> python ingest_markdown.py --md-dir markdown_docs --chunk-size 1000
        >>> python ingest_markdown.py -d ./papers -s 800 -o 150
        >>> python ingest_markdown.py --dry-run  # 仅模拟运行
    """
    parser = argparse.ArgumentParser(
        description="Markdown 数据存入工具 - 将 Markdown 文件存入 Qdrant 向量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--md-dir", "-d",
        type=str,
        default=str(Path(__file__).parent.parent / "markdown_docs"),
        help="Markdown 文件目录路径 (默认: pdf_qdrant_mvp/markdown_docs)"
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
    
    parser.add_argument(
        "--use-title", "-t",
        action="store_true",
        default=True,
        help="使用 LLM 从论文内容中提取标题作为集合名 (默认启用)"
    )
    
    parser.add_argument(
        "--no-title",
        action="store_true",
        help="禁用标题提取，使用文件名作为集合名"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="qwen-plus",
        help="用于标题提取的 LLM 模型名 (默认: qwen-plus)"
    )
    
    args = parser.parse_args()
    
    # 确定是否使用标题提取模式
    use_title = args.use_title and not args.no_title
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]Markdown 数据存入工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"Markdown 目录: {args.md_dir}")
    console.print(f"Qdrant 地址: {config.qdrant_url}")
    console.print(f"块大小: {args.chunk_size}")
    console.print(f"块重叠: {args.chunk_overlap}")
    console.print(f"标题提取: {'启用' if use_title else '禁用'}")
    if use_title:
        console.print(f"LLM 模型: {args.model}")
    
    # 初始化 Qdrant 管理器
    console.print("\n[bold]连接 Qdrant...[/bold]")
    qdrant = QdrantManager()
    
    # 获取 Markdown 文件列表（带标题提取）
    console.print("\n[bold]扫描 Markdown 文件并提取标题...[/bold]")
    md_files = get_markdown_files(args.md_dir, use_title=use_title, model=args.model)
    
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

