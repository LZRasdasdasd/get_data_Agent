"""
PDF 转 Markdown 转换脚本

将 PDF 文件转换为 Markdown 格式并保存到指定文件夹。
转换后的 Markdown 文件可用于 MCP RAG 工具添加完整文档。

使用方法:
    python src/pdf_to_markdown.py --pdf-dir <PDF目录> --output-dir <输出目录>
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from config import config
from pdf_tools import extract_text_from_pdf, get_pdf_files


# 初始化控制台
console = Console()


def convert_pdf_to_markdown(pdf_path: str, output_dir: str, overwrite: bool = False) -> dict:
    """
    将单个 PDF 文件转换为 Markdown 格式
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        dict: 转换结果
    """
    result = {
        "success": False,
        "input_file": pdf_path,
        "output_file": None,
        "char_count": 0,
        "pages": 0,
        "error": None
    }
    
    try:
        # 获取文件名（无扩展名）
        pdf_name = Path(pdf_path).stem
        output_file = Path(output_dir) / f"{pdf_name}.md"
        
        # 检查文件是否已存在
        if output_file.exists() and not overwrite:
            result["output_file"] = str(output_file)
            result["error"] = "文件已存在，跳过（使用 --overwrite 覆盖）"
            return result
        
        # 提取 PDF 内容
        pdf_result = extract_text_from_pdf(pdf_path)
        
        if not pdf_result["success"]:
            result["error"] = f"提取失败: {pdf_result.get('error')}"
            return result
        
        # 构建 Markdown 内容
        markdown_lines = [
            f"# {pdf_name}",
            "",
            f"> **Source**: {pdf_path}",
            f"> **Pages**: {pdf_result['pages']}",
            f"> **Characters**: {pdf_result['char_count']}",
            f"> **Converted**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Full Content",
            "",
        ]
        
        # 添加完整文本（不分块）
        full_text = pdf_result["text"]
        markdown_lines.append(full_text)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        result["success"] = True
        result["output_file"] = str(output_file)
        result["char_count"] = pdf_result["char_count"]
        result["pages"] = pdf_result["pages"]
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF 转 Markdown 工具 - 将 PDF 文件转换为 Markdown 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--pdf-dir", "-d",
        type=str,
        default=None,
        help="PDF 文件目录路径 (默认使用 .env 中的配置)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="markdown_docs",
        help="Markdown 输出目录路径 (默认: markdown_docs)"
    )
    
    parser.add_argument(
        "--overwrite", "-w",
        action="store_true",
        help="覆盖已存在的文件"
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
        "[bold cyan]PDF 转 Markdown 工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"PDF 目录: {config.pdf_dir}")
    console.print(f"输出目录: {args.output_dir}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]输出目录已创建/确认: {output_dir}[/green]")
    
    # 获取 PDF 文件列表
    pdf_files = get_pdf_files(config.pdf_dir)
    
    if not pdf_files:
        console.print(f"[red]未找到 PDF 文件: {config.pdf_dir}[/red]")
        sys.exit(1)
    
    console.print(f"\n[bold]找到 {len(pdf_files)} 个 PDF 文件[/bold]")
    
    # 转换统计
    stats = {
        "total": len(pdf_files),
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "total_chars": 0,
        "files": []
    }
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]转换 PDF 文件...", 
            total=len(pdf_files)
        )
        
        for i in range(len(pdf_files)):
            pdf_file = pdf_files[i]
            progress.update(overall_task, advance=1)
            
            console.print(f"\n[{i+1}/{len(pdf_files)}] 处理: {pdf_file['name']}")
            
            # 转换 PDF
            result = convert_pdf_to_markdown(
                pdf_file["path"], 
                args.output_dir,
                args.overwrite
            )
            
            if result["success"]:
                stats["success"] += 1
                stats["total_chars"] += result["char_count"]
                stats["files"].append({
                    "name": pdf_file["name"],
                    "output": result["output_file"],
                    "chars": result["char_count"],
                    "pages": result["pages"]
                })
                console.print(f"  [green]成功: {result['output_file']}[/green]")
                console.print(f"  字符数: {result['char_count']}, 页数: {result['pages']}")
            elif "已存在" in str(result.get("error", "")):
                stats["skipped"] += 1
                console.print(f"  [yellow]跳过: {result['error']}[/yellow]")
            else:
                stats["failed"] += 1
                console.print(f"  [red]失败: {result.get('error')}[/red]")
    
    # 显示统计
    console.print("\n")
    console.print("=" * 60)
    console.print(Panel.fit(
        "[bold green]转换完成统计[/bold green]",
        border_style="green"
    ))
    
    console.print(f"总文件数: {stats['total']}")
    console.print(f"成功: {stats['success']}")
    console.print(f"跳过: {stats['skipped']}")
    console.print(f"失败: {stats['failed']}")
    console.print(f"总字符数: {stats['total_chars']}")
    
    # 显示生成的文件列表
    if stats["files"]:
        console.print("\n[bold]生成的 Markdown 文件:[/bold]")
        for f in stats["files"]:
            console.print(f"  - {f['output']}: {f['chars']} 字符, {f['pages']} 页")
    
    # 提示下一步
    console.print("\n")
    console.print(Panel(
        "[bold yellow]下一步操作[/bold yellow]\n\n"
        "Markdown 文件已生成，可以使用 MCP RAG 工具添加到 RAG 系统:\n"
        "  - 使用 add_document 工具添加完整文档\n"
        "  - 使用 search_documents 工具搜索文档\n\n"
        f"输出目录: {output_dir.absolute()}",
        border_style="yellow"
    ))


if __name__ == "__main__":
    main()
