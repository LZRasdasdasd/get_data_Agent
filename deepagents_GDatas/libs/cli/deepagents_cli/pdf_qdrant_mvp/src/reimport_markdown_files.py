#!/usr/bin/env python
"""
重新导入markdown文件到向量数据库
针对之前删除的空集合，重新导入其对应的markdown文件
"""
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from ingest_markdown import get_markdown_files, sanitize_collection_name, chunk_markdown, read_markdown_file
from vector_tools import QdrantManager

console = Console()

def reimport_markdown_files():
    """重新导入markdown文件"""
    try:
        # 连接Qdrant
        qdrant_client = QdrantClient(url="http://127.0.0.1:6333")
        console.print("[green]✓ 已连接到 Qdrant[/green]")
        
        # 获取所有存在的集合
        collections_response = qdrant_client.get_collections()
        existing_collections = set(col.name for col in collections_response.collections)
        console.print(f"[cyan]Qdrant中现有 {len(existing_collections)} 个集合[/cyan]")
        
        # 初始化QdrantManager
        qdrant_manager = QdrantManager()
        
        # 获取本地markdown文件
        md_dir = Path(__file__).parent / "markdown_docs"
        md_files = get_markdown_files(str(md_dir))
        console.print(f"[cyan]本地有 {len(md_files)} 个markdown文件[/cyan]")
        
        # 找出需要导入的文件
        files_to_import = []
        
        for md_file in md_files:
            # 生成集合名称
            # md_file 是字典对象，包含 'path' 和 'name'
            file_path = md_file['path']
            file_name = md_file['name']
            collection_name = sanitize_collection_name(file_name)
            
            # 检查集合是否存在
            if collection_name not in existing_collections:
                files_to_import.append({
                    "file": md_file,
                    "collection_name": collection_name,
                    "status": "missing"
                })
            else:
                # 集合存在，检查是否有points
                try:
                    collection_info = qdrant_client.get_collection(collection_name)
                    if collection_info.points_count == 0:
                        # 集合存在但是空的
                        files_to_import.append({
                            "file": md_file,
                            "collection_name": collection_name,
                            "status": "empty"
                        })
                except Exception as e:
                    console.print(f"[red]检查集合 {collection_name} 失败: {e}[/red]")
        
        console.print(f"\n[green]找到 {len(files_to_import)} 个需要导入的文件[/green]")
        
        if len(files_to_import) == 0:
            console.print("[yellow]所有文件都已正确导入[/yellow]")
            return
        
        # 导入文件
        success_count = 0
        fail_count = 0
        
        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[cyan]重新导入markdown文件...", total=len(files_to_import))
            
            for file_info in files_to_import:
                md_file = file_info["file"]
                collection_name = file_info["collection_name"]
                status = file_info["status"]
                
                # 从md_file字典中提取路径和名称
                file_path = md_file['path']
                file_name = md_file['name']
                
                try:
                    # 读取markdown文件
                    console.print(f"[yellow]读取: {file_name[:50]}...[/yellow]")
                    file_data = read_markdown_file(file_path)
                    
                    if not file_data or not file_data.get("text"):
                        console.print(f"[red]✗ 文件内容为空: {file_name}[/red]")
                        fail_count += 1
                        progress.update(task, advance=1)
                        continue
                    
                    # 分块
                    text_content = file_data["text"]
                    chunks = chunk_markdown(text_content)
                    
                    if not chunks:
                        console.print(f"[red]✗ 分块失败: {file_name}[/red]")
                        fail_count += 1
                        progress.update(task, advance=1)
                        continue
                    
                    console.print(f"[green]✓ 分块完成: {len(chunks)} 个块[/green]")
                    
                    # 如果集合为空且存在，先删除
                    if status == "empty" and collection_name in existing_collections:
                        try:
                            qdrant_client.delete_collection(collection_name)
                            console.print(f"[yellow]✓ 删除空集合: {collection_name}[/yellow]")
                        except Exception as e:
                            console.print(f"[red]删除集合失败: {e}[/red]")
                    
                    # 重新获取现有集合列表（因为我们可能删除了一些）
                    if status == "empty":
                        collections_response = qdrant_client.get_collections()
                        existing_collections = set(col.name for col in collections_response.collections)
                    
                    # 创建集合
                    collection_result = qdrant_manager.create_collection(collection_name)
                    if collection_result.get("status") != "created" and collection_result.get("status") != "exists":
                        console.print(f"[red]✗ 创建集合失败: {collection_result.get('error', 'Unknown error')}[/red]")
                        fail_count += 1
                        progress.update(task, advance=1)
                        continue
                    
                    console.print(f"[green]✓ 集合创建成功: {collection_name}[/green]")
                    
                    # 添加points
                    points = []
                    for idx, chunk in enumerate(chunks):
                        try:
                            # chunk 已经是字典格式，直接添加到 points 列表
                            # add_points 方法会自动处理 embedding 生成
                            points.append({
                                "text": chunk["text"],
                                "chunk_index": idx,
                                "source_file": file_name
                            })
                        except Exception as e:
                            console.print(f"[red]生成嵌入失败 chunk {idx}: {e}[/red]")
                    
                    if not points:
                        console.print(f"[red]✗ 没有生成任何嵌入向量[/red]")
                        fail_count += 1
                        progress.update(task, advance=1)
                        continue
                    
                    # 插入points
                    add_result = qdrant_manager.add_points(
                        collection_name=collection_name,
                        points=points
                    )
                    
                    if add_result.get("success"):
                        console.print(f"[green]✓ 成功导入 {len(points)} 个points[/green]")
                        success_count += 1
                    else:
                        console.print(f"[red]✗ 导入失败: {add_result.get('error')}[/red]")
                        fail_count += 1
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    console.print(f"[red]✗ 处理失败 {file_name}: {e}[/red]")
                    fail_count += 1
                    progress.update(task, advance=1)
        
        console.print(f"\n[green]导入完成![/green]")
        console.print(f"[green]成功: {success_count} 个文件[/green]")
        console.print(f"[red]失败: {fail_count} 个文件[/red]")
        
    except Exception as e:
        console.print(f"[red]执行出错: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reimport_markdown_files()
