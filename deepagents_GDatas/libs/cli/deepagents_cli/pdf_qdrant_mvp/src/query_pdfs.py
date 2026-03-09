"""
PDF 数据查询脚本

从 Qdrant 向量数据库中查询数据
"""

import sys
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from config import config
from pdf_tools import sanitize_collection_name
from vector_tools import QdrantManager

# 初始化控制台
console = Console()


def list_collections(qdrant: QdrantManager):
    """列出所有集合"""
    console.print("\n[bold]获取集合列表...[/bold]")
    collections = qdrant.list_collections()
    
    if not collections:
        console.print("[yellow]没有找到任何集合[/yellow]")
        return
    
    # 创建表格
    table = Table(title="集合名", show_header=True)
    table.add_column("集合名", style="cyan")
    table.add_column("向量数", style="green")
    table.add_column("状态", style="yellow")
    
    for col in collections:
        table.add_row(col["name"], str(col["points_count"]), str(col.get("status", "active")))
    
    console.print(table)


def search_collection(qdrant: QdrantManager, collection_name: str, query_text: str, top_k: int = 5, threshold: float = 0.7):
    """在指定集合中搜索"""
    # 获取集合信息
    info = qdrant.get_collection_info(collection_name)
    
    if info["status"] == "error":
        console.print(f"[red]集合 '{collection_name}' 不存在，请先使用 --list 查看所有集合[/red]")
        return
    
    # 执行查询
    console.print(f"\n[bold]在集合 '{collection_name}' 中查询...[/bold]")
    console.print(f"查询: {query_text}")
    
    results = qdrant.search(
        collection_name=collection_name,
        query_text=query_text,
        n_results=top_k,
        score_threshold=threshold
    )
    
    if not results:
        console.print("[yellow]没有找到相关结果[/yellow]")
        return
    
    # 显示结果
    console.print("\n" + "=" * 60)
    for i, result in enumerate(results):
        score = result["score"]
        console.print(f"\n[bold]结果 {i+1}[/bold] (相似度: {score:.2%})")
        console.print(f"来源文件: {result.get('source_file', '未知')}")
        console.print(f"文本预览:")
        text = result["text"]
        if len(text) > 300:
            console.print(f"  {text[:150]}...")
            console.print(f"  ...{text[-100:]}")
        else:
            console.print(f"  {text}")
        console.print(f"  ({len(text)} 字符)")
    
    # 统计
    avg_score = sum(r["score"] for r in results) / len(results)
    console.print(f"\n[green]平均相似度: {avg_score:.2%}[/green]")


def interactive_mode(qdrant: QdrantManager, collection_name: str, top_k: int, threshold: float):
    """交互式查询模式"""
    console.print("\n[bold cyan]交互式查询模式[/bold cyan]")
    console.print("输入 'quit' 退出，输入 'help' 查看帮助\n")
    
    while True:
        try:
            query_text = Prompt.ask("[bold]查询[/bold]")
            
            if query_text.lower() == 'quit':
                console.print("[yellow]退出查询[/yellow]")
                break
            
            if query_text.lower() == 'help':
                console.print("命令:")
                console.print("  quit - 退出")
                console.print("  help - 显示帮助")
                console.print("  其他 - 执行查询")
                continue
            
            if not query_text.strip():
                continue
            
            search_collection(qdrant, collection_name, query_text, top_k, threshold)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]退出查询[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]查询错误: {e}[/red]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF 数据查询工具 - 从 Qdrant 向量数据库中查询数据",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--list", "-l", action="store_true", help="列出所有集合")
    parser.add_argument("--collection", "-c", type=str, default=None, help="指定集合名称")
    parser.add_argument("--query", "-q", type=str, default=None, help="查询文本")
    parser.add_argument("--top", "-t", type=int, default=5, help="返回结果数量")
    parser.add_argument("--threshold", type=float, default=0.7, help="相似度阈值")
    
    args = parser.parse_args()
    
    # 加载配置
    if not config.validate():
        console.print("[red]配置验证失败![/red]")
        console.print(config)
        sys.exit(1)
    
    # 初始化 Qdrant 管理器
    qdrant = QdrantManager()
    
    # 列出所有集合
    if args.list:
        list_collections(qdrant)
        return
    
    # 指定集合查询
    if args.collection:
        if args.query:
            # 单次查询
            search_collection(qdrant, args.collection, args.query, args.top, args.threshold)
        else:
            # 交互式模式
            interactive_mode(qdrant, args.collection, args.top, args.threshold)
        return
    
    # 显示帮助
    console.print(Panel.fit(
        "[bold cyan]PDF 数据查询工具[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print("\n[bold yellow]使用方法:[/bold yellow]")
    console.print("1. 列出所有集合:")
    console.print("   python src/query_pdfs.py --list")
    console.print("")
    console.print("2. 在指定集合中查询:")
    console.print("   python src/query_pdfs.py --collection <集合名> --query <查询文本>")
    console.print("")
    console.print("3. 交互式查询模式:")
    console.print("   python src/query_pdfs.py --collection <集合名>")
    console.print("")
    console.print("4. 访问 Qdrant Dashboard:")
    console.print("   http://localhost:6333/dashboard")
    
    console.print("\n[bold green]示例:[/bold green]")
    console.print("python src/query_pdfs.py -c co_electroreduction_on_single_atom_copper -q \"copper catalyst\"")


if __name__ == "__main__":
    main()
