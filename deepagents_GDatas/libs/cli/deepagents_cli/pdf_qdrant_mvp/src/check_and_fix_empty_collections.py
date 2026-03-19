#!/usr/bin/env python
"""
检查和修复空Points集合
"""
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from ingest_markdown import get_markdown_files, sanitize_collection_name, chunk_markdown, read_markdown_file
from vector_tools import QdrantManager

console = Console()

def check_and_fix_empty_collections():
    """检查并修复空Points集合"""
    try:
        # 连接Qdrant
        qdrant_client = QdrantClient(url="http://127.0.0.1:6333")
        console.print("[green]✓ 已连接到 Qdrant[/green]")
        
        # 获取所有集合
        collections_response = qdrant_client.get_collections()
        all_collections = [col.name for col in collections_response.collections]
        console.print(f"[cyan]总共有 {len(all_collections)} 个集合[/cyan]")
        
        # 获取本地markdown文件
        md_dir = Path(__file__).parent / "markdown_docs"
        md_files = get_markdown_files(str(md_dir))
        console.print(f"[cyan]本地有 {len(md_files)} 个markdown文件[/cyan]")
        
        # 找出需要处理的集合
        empty_point_collections = []
        
        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("[yellow]检查集合中的Points...", total=len(all_collections))
            
            for collection_name in all_collections:
                try:
                    # 获取集合信息
                    collection_info = qdrant_client.get_collection(collection_name)
                    points_count = collection_info.points_count
                    
                    if points_count == 0:
                        # 集合中没有 Points
                        empty_point_collections.append({
                            "collection": collection_name,
                            "points": points_count,
                            "status": "empty"
                        })
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    console.print(f"[red]✗ 检查集合 {collection_name} 失败: {e}[/red]")
                    progress.update(task, advance=1)
        
        # 统计结果
        total_empty = len(empty_point_collections)
        total_with_points = len(all_collections) - len(empty_point_collections)
        
        # 显示汇总
        console.print("\n[cyan]检查结果汇总:[/cyan]")
        console.print(f"  集合总数: {len(all_collections)}")
        console.print(f" 空Points集合数: {total_empty}")
        console.print(f" 有Points集合数: {total_with_points}")
        
        if empty_point_collections:
            console.print(f"\n[yellow]发现 {len(empty_point_collections)} 个空Points集合需要处理:[/yellow]")
            for i, col in enumerate(empty_point_collections[:10], 1):  # 只显示前10个
                console.print(f"  {i}. [cyan]{col['collection']:<20}[/cyan] (Points={col['points']}, Status={col['status']})")
            
            if len(empty_point_collections) > 10:
                console.print(f"  ... 还有 {len(empty_point_collections) - 10} 个未显示")
        
        # 处理空Points集合
        if empty_point_collections:
            console.print(f"\n[red]处理空Points集合...[/red]")
            
            fixed_count = 0
            deleted_count = 0
            
            # 创建QdrantManager实例（使用默认配置）
            qdrant_manager = QdrantManager()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
            ) as fix_progress:
                task = fix_progress.add_task("[yellow]处理空Points集合...", total=len(empty_point_collections))
            
                for col_data in empty_point_collections:
                    collection_name = col_data['collection']
                    try:
                        # 删除空集合
                        console.print(f"[cyan]删除空集合: {collection_name}[/cyan]")
                        qdrant_client.delete_collection(collection_name)
                        deleted_count += 1
                        console.print(f"[green]  ✓ 已删除[/green]")
                        
                        # 查找对应的markdown文件
                        # 尝试多种可能的文件名
                        possible_names = [
                            collection_name + ".md",
                            collection_name.replace("_", " ") + ".md",
                            collection_name.replace("-", " ") + ".md",
                        ]
                        
                        md_file_path = None
                        for name in possible_names:
                            test_path = md_dir / name
                            if test_path.exists():
                                md_file_path = test_path
                                break
                        
                        if md_file_path:
                            console.print(f"[cyan]重新导入数据: {collection_name}[/cyan]")
                            
                            # 读取markdown文件
                            file_data = read_markdown_file(str(md_file_path))
                            
                            # 创建集合
                            qdrant_manager.create_collection(collection_name, vectors_config={
                                "size": 1536,
                                "distance": "Cosine"
                            })
                            
                            # 分块并导入数据
                            chunks = chunk_markdown(file_data['text'], chunk_size=1000, overlap=200, min_chunk_size=500)
                            points = []
                            
                            for j, chunk in enumerate(chunks, 0):
                                points.append({
                                    "id": j,
                                    "vector": qdrant_manager.generate_embedding(chunk),
                                    "payload": {
                                        "text": chunk,
                                        "file": file_data['name'],
                                        "chunk_id": j
                                    }
                                })
                            
                            # 使用qdrant_manager.add_points() 批量导入
                            if points:
                                qdrant_manager.add_points(
                                    collection_name=collection_name,
                                    points=points
                                )
                                console.print(f"[green]  ✓ {collection_name}: 导入 {len(points)} 个Points[/green]")
                                fixed_count += 1
                            else:
                                console.print(f"[yellow]  ⚠ {collection_name}: 没有生成任何chunks[/yellow]")
                        else:
                            console.print(f"[yellow]  ⚠ {collection_name}: 未找到对应的markdown文件[/yellow]")
                        
                    except Exception as e:
                        console.print(f"[red]✗ 处理集合 {collection_name} 失败: {e}[/red]")
                        import traceback
                        traceback.print_exc()
                    
                    fix_progress.update(task, advance=1)
            
            # 显示最终统计
            console.print(f"\n[cyan]修复完成:[/cyan]")
            console.print(f"  成功删除: {deleted_count} 个空集合")
            console.print(f"  成功重建并导入: {fixed_count} 个集合")
            console.print(f"\n[green]✓ 所有集合现在都应该包含有效的Points了！[/green]")
        else:
            console.print(f"\n[green]✓ 所有集合都包含有效的Points，无需修复！[/green]")
        
    except Exception as e:
        console.print(f"[red]发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_fix_empty_collections()
