#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找导入中断点，确定需要从哪个文件继续导入
"""

import os
import sys
import requests
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入sanitize_collection_name函数
from ingest_markdown import sanitize_collection_name

def main():
    # 获取Qdrant中已存在的所有集合
    qdrant_url = 'http://127.0.0.1:6333'
    response = requests.get(f'{qdrant_url}/collections')
    
    if response.status_code != 200:
        print(f"无法连接到Qdrant: {response.status_code}")
        return
    
    collections = response.json()['result']['collections']
    imported_collections = {col['name'] for col in collections}
    
    print(f"已导入的集合数: {len(imported_collections)}")
    
    # 获取markdown_docs目录
    md_dir = Path(__file__).parent / 'markdown_docs'
    
    if not md_dir.exists():
        print(f"目录不存在: {md_dir}")
        return
    
    # 获取所有markdown文件并按名称排序
    md_files = sorted(md_dir.glob('*.md'))
    total_files = len(md_files)
    
    print(f"\nmarkdown文档总数: {total_files}")
    print(f"剩余未导入的文件数: {total_files - len(imported_collections)}")
    
    # 找到最后一个导入的文件
    last_imported_file = None
    last_imported_collection = None
    first_unimported_file = None
    first_unimported_collection = None
    
    for md_file in md_files:
        # 计算该文件对应的集合名称
        collection_name = sanitize_collection_name(md_file.name)
        
        if collection_name in imported_collections:
            last_imported_file = md_file
            last_imported_collection = collection_name
        else:
            # 第一个不在已导入集合中的文件，就是需要继续导入的文件
            if first_unimported_file is None:
                first_unimported_file = md_file
                first_unimported_collection = collection_name
            break
    
    print("\n" + "="*80)
    if last_imported_file:
        print(f"\n最后一个已导入的文件:")
        print(f"  文件名: {last_imported_file.name}")
        print(f"  集合名: {last_imported_collection}")
    else:
        print("\n还没有任何文件被导入")
    
    if first_unimported_file:
        print(f"\n需要从以下文件开始继续导入:")
        print(f"  文件名: {first_unimported_file.name}")
        print(f"  集合名: {first_unimported_collection}")
        
        # 统计从该文件开始剩余的文件数
        idx = md_files.index(first_unimported_file)
        remaining_count = len(md_files) - idx
        print(f"  剩余文件数: {remaining_count}")
    
    print("\n" + "="*80)
    print("\n继续导入的命令:")
    if first_unimported_file:
        # 找到第一个需要导入的文件
        # 由于ingest_markdown.py会处理所有文件，我们需要使用另一个方法
        print("\n建议方案:")
        print("1. 修改ingest_markdown.py以跳过已导入的集合，或")
        print("2. 将已导入的文件移动到另一个目录，或")
        print("3. 创建一个新的脚本，只处理未导入的文件")
        
        # 输出未导入文件的列表（前10个）
        print(f"\n前10个未导入的文件:")
        unimported_count = 0
        for md_file in md_files:
            collection_name = sanitize_collection_name(md_file.name)
            if collection_name not in imported_collections:
                print(f"  - {md_file.name}")
                unimported_count += 1
                if unimported_count >= 10:
                    break
        if unimported_count > 10:
            print(f"  ... 还有 {len(md_files) - md_files.index(first_unimported_file) - 10} 个文件")
    else:
        print("\n所有文件已导入完成!")

if __name__ == '__main__':
    main()
