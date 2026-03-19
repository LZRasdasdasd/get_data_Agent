"""
从中断点继续导入markdown文件到Qdrant

此脚本会:
1. 读取find_resume_point.py的输出,获取开始导入的文件
2. 使用ingest_markdown.py中的函数处理剩余的文件
3. 避免重复导入已处理的文件
"""
import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 从ingest_markdown导入需要的函数
from ingest_markdown import (
    get_markdown_files, 
    read_markdown_file,
    chunk_markdown,
    sanitize_collection_name
)
from vector_tools import QdrantManager

def main():
    # 设置参数
    md_dir = Path(__file__).parent / "markdown_docs"
    
    # 上次导入停止的点
    last_imported_file = "Li 等 - 2019 - Nickel-catalyzed copolymerization of carbon dioxide with internal epoxides by di-nuclear bis(benzotr.md"
    start_from_next_file = True  # 是否从下一个文件开始
    
    print(f"Markdown文件目录: {md_dir}")
    print(f"上次导入的文件: {last_imported_file}")
    print(f"从下一个文件开始: {start_from_next_file}")
    print()
    
    # 获取所有markdown文件
    print("正在扫描markdown文件...")
    md_files = get_markdown_files(str(md_dir))
    md_files = sorted(md_files)  # 按文件名排序
    
    print(f"找到 {len(md_files)} 个markdown文件")
    print()
    
    # 找到开始位置
    start_index = -1
    for i, md_path in enumerate(md_files):
        if Path(md_path).name == last_imported_file:
            start_index = i
            break
    
    if start_index == -1:
        print(f"警告: 未找到上次导入的文件 '{last_imported_file}'")
        print("将从第一个文件开始导入")
        start_index = 0
        start_from_next_file = False
    else:
        print(f"上次导入的文件在索引 {start_index}")
    
    # 确定要导入的文件
    if start_from_next_file:
        files_to_import = md_files[start_index + 1:]
        print(f"将从索引 {start_index + 1} 开始,共 {len(files_to_import)} 个文件待导入")
    else:
        files_to_import = md_files[start_index:]
        print(f"将从索引 {start_index} 开始,共 {len(files_to_import)} 个文件待导入")
    
    print()
    print("=" * 80)
    print("开始导入...")
    print("=" * 80)
    print()
    
    # 初始化Qdrant管理器
    print("正在初始化Qdrant管理器...")
    qdrant = QdrantManager()
    print("Qdrant管理器初始化成功")
    print()
    
    # 导入每个文件
    success_count = 0
    fail_count = 0
    skipped_count = 0
    
    for idx, md_path in enumerate(files_to_import, start=1):
        try:
            filename = Path(md_path).name
            
            # 生成集合名称
            collection_name = sanitize_collection_name(filename)
            
            # 检查集合是否已存在
            try:
                existing_collections = qdrant.list_collections()
                existing_names = [col['name'] for col in existing_collections]
                
                if collection_name in existing_names:
