#!/usr/bin/env python
"""删除最近导入的集合（具有零向量的问题集合）"""
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
    
    console.print("[cyan]开始查找需要删除的集合...[/cyan]")
    
    # 获取所有markdown文件
    all_files = get_markdown_files(str(md_dir))
    console.print(f"[yellow]总共找到 {len(all_files)} 个markdown文件[/yellow]")
    
    # 初始化Qdrant管理器
    qdrant_manager = QdrantManager()
    
    # 获取所有现有集合
    existing_collections = qdrant_manager.list_collections()
    console.print(f"[yellow]当前共有 {len(existing_collections)} 个集合[/yellow]")
    
    # 找出未被本地文件对应的集合（这些可能是之前错误导入的）
    local_collection_names = {md_file['collection_name'] for md_file in all_files}
    
    # 集合数量检查：如果比本地文件多，说明有额外集合（可能是错误导入）
    if len(existing_collections) > len(all_files):
        extra_count = len(existing_collections) - len(all_files)
        console.print(f"[red]检测到 {extra_count} 个额外集合[/red]")
        
        # 需要删除的集合（本地文件中没有对应的集合名称）
        extra_collections = [
            col for col in existing_collections 
            if col['name'] not in local_collection_names
        ]
        
        console.print(f"[yellow]准备删除 {len(extra_collections)} 个额外集合:[/yellow]")
        for col in extra_collections[:10]:  # 显示前10个
            console.print(f"  - {col['name']} (points: {col['points_count']})")
        
        if len(extra_collections) > 10:
            console.print(f"  ... 还有 {len(extra_collections) - 10} 个集合")
        
        # 询问确认
        console.print("\n[red]警告：这将会永久删除这些集合！[/red]")
        
        # 开始删除
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]删除集合中...", total=len(extra_collections))
            deleted_count = 0
            failed_count = 0
            
            for col in extra_collections:
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
    else:
        console.print("[green]没有检测到额外集合，无需删除[/green]")
        console.print(f"[green]当前集合数: {len(existing_collections)}[/green]")
        console.print(f"[green]本地文件数: {len(all_files)}[/green]")

if __name__ == "__main__":
    main()
