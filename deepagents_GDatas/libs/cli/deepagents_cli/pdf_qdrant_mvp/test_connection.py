#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试Qdrant连接"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_config import config
from vector_tools import QdrantManager

def main():
    print("=" * 60)
    print("Qdrant 连接测试")
    print("=" * 60)
    
    # 显示配置信息
    print(f"\n配置信息:")
    print(f"  QDRANT_URL: {config.qdrant_url}")
    print(f"  QDRANT_API_KEY: {config.qdrant_api_key if config.qdrant_api_key else '(未设置)'}")
    print(f"  EMBEDDING_MODEL: {config.embedding_model}")
    print(f"  EMBEDDING_DIMENSION: {config.embedding_dimension}")
    
    try:
        # 尝试连接
        print(f"\n正在连接到 {config.qdrant_url}...")
        manager = QdrantManager()
        print("✓ 连接成功!")
        
        # 获取集合列表
        print("\n获取集合列表...")
        collections = manager.list_collections()
        print(f"✓ 找到 {len(collections)} 个集合:")
        
        for col in collections:
            print(f"  - {col['name']}: {col['points_count']} 个向量点")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())