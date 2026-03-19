#!/usr/bin/env python
"""检查剩余需要导入的文件数量"""
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ingest_markdown import get_markdown_files
from vector_tools import QdrantManager

def main():
    """主函数"""
    md_dir = Path(__file__).parent / "markdown_docs"
    
    # 获取所有markdown文件
    all_files = get_markdown_files(str(md_dir))
    print(f"总共找到 {len(all_files)} 个markdown文件")
    
    # 初始化Qdrant管理器
    qdrant_manager = QdrantManager()
    
    # 获取所有现有集合
    existing_collections = qdrant_manager.list_collections()
    
    print(f"当前共有 {len(existing_collections)} 个集合")
    
    # 找出尚未被导入的文件集合
    local_collection_names = {md_file['collection_name'] for md_file in all_files}
    
    # 找出需要导入的文件（已有集合中没有对应的文件）
    files_to_import = [
        md_file for md_file in all_files
        if md_file['collection_name'] not in existing_collections
    ]
    
    print(f"需要导入 {len(files_to_import)} 个文件")
    
    if len(files_to_import) > 0:
        print("\n需要导入的文件列表:")
        for i, md_file in enumerate(files_to_import[:10]):  # 只显示前10个
            print(f"{i+1}. {md_file['name']}")
        
        if len(files_to_import) > 10:
            print(f"... 还有 {len(files_to_import) - 10} 个文件")
    else:
        print("\n所有文件都已经在Qdrant中导入完成！")

if __name__ == "__main__":
    main()
