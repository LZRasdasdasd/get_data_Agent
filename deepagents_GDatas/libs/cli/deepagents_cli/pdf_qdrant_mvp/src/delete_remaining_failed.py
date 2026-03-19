#!/usr/bin/env python
"""删除剩余的失败集合（逐个删除以避免内存问题）"""
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from vector_tools import QdrantManager
from ingest_markdown import get_markdown_files

console = Console()

def main():
    """主函数"""
    md_dir = Path(__file__).parent / "markdown_docs"
    
    console.print("[cyan]开始查找剩余需要删除的集合...[/cyan]")
    
    # 获取所有markdown文件
    all_files = get_markdown_files(str(md_dir))
    console.print(f"[yellow]总共找到 {len(all_files)} 个markdown文件[/yellow]")
    
    # 初始化Qdrant管理器
    qdrant_manager = QdrantManager()
    
    # 获取所有现有集合
    existing_collections = qdrant_manager.list_collections()
    console.print(f"[yellow]当前共有 {len(existing_collections)} 个集合[/yellow]")
    
    # 找出未被本地文件对应的集合
    local_collection_names = {md_file['collection_name'] for md_file in all_files}
    
    # 需要删除的集合（本地文件中没有对应的集合名称）
    collections_to_delete = [
        col for col in existing_collections
        if col['name'] not in local_collection_names
    ]
    
    console.print(f"[yellow]需要删除 {len(collections_to_delete)} 个集合[/yellow]")
    
    if len(collections_to_delete) == 0:
        console.print("[green]没有需要删除的集合，已完成清理！[/green]")
        return
    
    # 逐个删除集合（避免内存问题）
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]删除集合中...", total=len(collections_to_delete))
        
        deleted_count = 0
        failed_count = 0
        
        for i, col in enumerate(collections_to_delete):
            try:
                progress.update(task, description=f"[cyan]删除: {col['name'][:40]}...[/cyan]")
                
                result = qdrant_manager.delete_collection(col['name'])
                if result['status'] == 'deleted':
                    deleted_count += 1
                else:
                    console.print(f"[red]删除失败 {col['name']}: {result.get('message', 'Unknown error')}[/red]")
                    failed_count += 1
                
                progress.update(task, advance=1)
                
            except Exception as e:
                console.print(f"[red]删除异常 {col['name']}: {e}[/red]")
                failed_count += 1
                progress.update(task, advance=1)
        
        # 输出总结
        console.print(f"\n[green]✓ 删除完成！[/green]")
        console.print(f"[green]成功删除 {deleted_count} 个集合[/green]")
        if failed_count > 0:
            console.print(f"[red]失败 {failed_count} 个集合[/red]")

if __name__ == "__main__":
    main()
