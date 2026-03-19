#!/usr/bin/env python
"""
找出缺失的 markdown 文件
"""
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from rich.console import Console
from ingest_markdown import get_markdown_files, sanitize_collection_name

console = Console()

def find_missing_file():
    """找出缺失的 markdown 文件"""
    try:
        # 连接Qdrant
        qdrant_client = QdrantClient(url="http://127.0.0.1:6333")
        console.print("[green]✓ 已连接到 Qdrant[/green]")
        
        # 获取所有集合
        collections = qdrant_client.get_collections()
        existing_collections = {col.name for col in collections.collections}
        console.print(f"[cyan]Qdrant中现有 {len(existing_collections)} 个集合[/cyan]")
        
        # 获取本地markdown文件
        md_dir = Path(__file__).parent / "markdown_docs"
        md_files = get_markdown_files(str(md_dir))
        console.print(f"[cyan]本地有 {len(md_files)} 个markdown文件[/cyan]")
        
        # 找出缺失的文件
        missing_files = []
        for md_file in md_files:
            if isinstance(md_file, dict):
                # 如果是字典,获取文件名
                file_name = md_file.get('name', md_file.get('filename', ''))
            else:
                # 如果是Path或字符串
                file_name = str(md_file)
            
            if file_name:
                collection_name = sanitize_collection_name(file_name)
                if collection_name not in existing_collections:
                    missing_files.append((file_name, collection_name))
        
        if missing_files:
            console.print(f"\n[yellow]发现 {len(missing_files)} 个缺失的文件:[/yellow]")
            for file_name, collection_name in missing_files:
                console.print(f"  - {file_name}")
                console.print(f"    集合名: {collection_name}")
        else:
            console.print("\n[green]没有缺失的文件![/green]")
        
    except Exception as e:
        console.print(f"[red]发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_missing_file()
