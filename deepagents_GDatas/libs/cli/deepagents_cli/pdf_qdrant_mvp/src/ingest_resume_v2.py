#!/usr/bin/env python
"""继续导入中断的markdown文件到Qdrant向量数据库"""
import sys
from pathlib import Path
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 从现有的ingest_markdown导入函数
from ingest_markdown import (
    sanitize_collection_name,
    get_markdown_files,
    read_markdown_file,
    is_heading,
    split_paragraph_at_period,
    merge_small_paragraphs,
    chunk_markdown
)

# 导入QdrantManager
from vector_tools import QdrantManager

console = Console()

QDRANT_URL = "http://127.0.0.1:6333"

def get_existing_collections():
    """获取已存在的集合名称"""
    try:
        response = requests.get(f"{QDRANT_URL}/collections")
        if response.status_code == 200:
            data = response.json()
            return {col['name'] for col in data['result']['collections']}
    except Exception as e:
        console.print(f"[red]获取已存在集合时出错: {e}[/red]")
    return set()

def main():
    """主函数"""
    md_dir = Path(__file__).parent / "markdown_docs"
    
    console.print("[cyan]开始继续导入markdown文件...[/cyan]")
    
    # 获取所有markdown文件
    all_files = get_markdown_files(str(md_dir))
    console.print(f"[yellow]总共找到 {len(all_files)} 个markdown文件[/yellow]")
    
    # 获取已存在的集合
    existing_collections = get_existing_collections()
    console.print(f"[yellow]已存在 {len(existing_collections)} 个集合[/yellow]")
    
    # 初始化Qdrant管理器
    qdrant_manager = QdrantManager()
    
    # 筛选未导入的文件
    remaining_files = []
    for md_file in all_files:
        collection_name = md_file['collection_name']
        if collection_name not in existing_collections:
            remaining_files.append(md_file)
    
    console.print(f"[green]需要导入 {len(remaining_files)} 个文件[/green]")
    
    if len(remaining_files) == 0:
        console.print("[green]所有文件已经导入完成！[/green]")
        return
    
    # 开始导入
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]导入文件中...", total=len(remaining_files))
        
        success_count = 0
        failed_files = []
        
        for md_file in remaining_files:
            try:
                progress.update(task, description=f"[cyan]处理: {md_file['name']}[/cyan]")
                
                # 读取markdown文件
                md_data = read_markdown_file(md_file['path'])
                if not md_data['text']:
                    console.print(f"[yellow]跳过空文件: {md_file['name']}[/yellow]")
                    continue
                
                # 分块markdown文本
                chunks = chunk_markdown(md_data['text'], chunk_size=1000, overlap=200, min_chunk_size=500)
                
                if len(chunks) == 0:
                    console.print(f"[yellow]跳过无内容的文件: {md_file['name']}[/yellow]")
                    continue
                
                # 创建集合并添加数据
                collection_name = md_file['collection_name']
                
                # 使用QdrantManager创建集合
                qdrant_manager.create_collection(collection_name)
                
                # 准备数据点 - 使用QdrantManager.add_points期望的格式
                points = []
                for i, chunk in enumerate(chunks):
                    # QdrantManager.add_points会自动生成向量嵌入
                    payload = {
                        "text": chunk,
                        "file": md_file['name'],
                        "chunk_id": i
                    }
                    points.append(payload)
                
                # 将数据添加到集合（add_points会自动生成向量嵌入）
                qdrant_manager.add_points(collection_name, points, batch_size=10)
                
                success_count += 1
                
            except Exception as e:
                console.print(f"[red]导入失败 {md_file['name']}: {e}[/red]")
                failed_files.append(md_file['name'])
                continue
            
            progress.update(task, advance=1)
    
    # 输出总结
    console.print(f"\n[green]✓ 导入完成！[/green]")
    console.print(f"[green]成功导入 {success_count} 个文件[/green]")
    
    if failed_files:
        console.print(f"[red]失败 {len(failed_files)} 个文件:[/red]")
        for f in failed_files:
            console.print(f"  - {f}")

if __name__ == "__main__":
    main()
