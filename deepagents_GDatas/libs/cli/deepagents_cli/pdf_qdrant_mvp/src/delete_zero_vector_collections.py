#!/usr/bin/env python
"""
删除包含零向量的集合
"""
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from typing import List, Dict

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from ingest_markdown import get_markdown_files

console = Console()

def is_zero_vector(vector: List[float], tolerance: float = 1e-10) -> bool:
    """检查向量是否为零向量"""
    if not vector:
        return True
    return all(abs(v) < tolerance for v in vector)

def delete_zero_vector_collections():
    """删除包含零向量的集合"""
    try:
        # 连接Qdrant
        qdrant_client = QdrantClient(url="http://127.0.0.1:6333")
        console.print("[green]✓ 已连接到 Qdrant[/green]")
        
        # 获取所有集合
        collections = qdrant_client.get_collections()
        all_collections = [col.name for col in collections.collections]
        console.print(f"[cyan]总共有 {len(all_collections)} 个集合[/cyan]")
        
        # 获取本地markdown文件(用于集合名验证)
        md_dir = Path(__file__).parent / "markdown_docs"
        md_files = get_markdown_files(str(md_dir))
        console.print(f"[cyan]本地有 {len(md_files)} 个markdown文件[/cyan]")
        
        zero_vector_collections = []
        failed_checks = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]检查集合中的向量值...", total=len(all_collections))
            
            for collection_name in all_collections:
                try:
                    # 获取集合信息
                    collection_info = qdrant_client.get_collection(collection_name)
                    points_count = collection_info.points_count
                    
                    if points_count == 0:
                        # 如果集合中没有points,跳过
                        progress.update(task, advance=1)
                        continue
                    
                    # 采样一些points来检查向量(最多检查前5个)
                    # 使用with_payload=True获取完整信息, with_vectors=True获取向量
                    try:
                        sample_points = qdrant_client.scroll(
                            collection_name=collection_name,
                            limit=5,
                            with_payload=True,
                            with_vectors=True
                        )[0]  # scroll返回(points, next_page_offset)
                        
                        if not sample_points:
                            progress.update(task, advance=1)
                            continue
                        
                        # 检查这些points的向量是否为零向量
                        has_zero_vector = False
                        for point in sample_points:
                            if point.vector is not None:
                                # 向量可能是单个列表或者字典(取决于配置)
                                if isinstance(point.vector, dict):
                                    # 如果vector是字典,取第一个值
                                    vector = list(point.vector.values())[0]
                                else:
                                    vector = point.vector
                                
                                if is_zero_vector(vector):
                                    has_zero_vector = True
                                    break
                        
                        if has_zero_vector:
                            zero_vector_collections.append(collection_name)
                            console.print(f"[yellow]发现零向量集合: {collection_name}[/yellow]")
                    
                    except Exception as e:
                        failed_checks.append((collection_name, str(e)))
                        console.print(f"[red]检查集合 {collection_name} 失败: {e}[/red]")
                
                except Exception as e:
                    failed_checks.append((collection_name, str(e)))
                    console.print(f"[red]处理集合 {collection_name} 时出错: {e}[/red]")
                
                progress.update(task, advance=1)
        
        console.print(f"\n[cyan]检查完成![/cyan]")
        console.print(f"[yellow]发现 {len(zero_vector_collections)} 个零向量集合[/yellow]")
        console.print(f"[red]检查失败的集合: {len(failed_checks)}[/red]")
        
        if failed_checks:
            console.print("\n[red]检查失败的集合列表:[/red]")
            for col_name, error in failed_checks[:5]:  # 只显示前5个
                console.print(f"  - {col_name}: {error}")
            if len(failed_checks) > 5:
                console.print(f"  ... 还有 {len(failed_checks) - 5} 个")
        
        if zero_vector_collections:
            console.print(f"\n[red]将要删除的零向量集合 ({len(zero_vector_collections)}个):[/red]")
            
            # 删除零向量集合
            delete_progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            )
            
            with delete_progress as progress:
                delete_task = progress.add_task(
                    "[red]删除零向量集合...[/red]", total=len(zero_vector_collections)
                )
                
                deleted_count = 0
                failed_deletions = []
                
                for collection_name in zero_vector_collections:
                    try:
                        qdrant_client.delete_collection(collection_name)
                        deleted_count += 1
                        console.print(f"[green]✓ 已删除: {collection_name}[/green]")
                    except Exception as e:
                        failed_deletions.append((collection_name, str(e)))
                        console.print(f"[red]✗ 删除失败 {collection_name}: {e}[/red]")
                    
                    progress.update(delete_task, advance=1)
                
                console.print(f"\n[green]成功删除 {deleted_count} 个零向量集合[/green]")
                
                if failed_deletions:
                    console.print(f"[red]{len(failed_deletions)} 个集合删除失败:[/red]")
                    for col_name, error in failed_deletions:
                        console.print(f"  - {col_name}: {error}")
        else:
            console.print("[green]没有发现零向量集合[/green]")
        
        # 显示最终统计
        remaining_collections = qdrant_client.get_collections()
        console.print(f"\n[cyan]删除后剩余集合数: {len(remaining_collections.collections)}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_zero_vector_collections()
