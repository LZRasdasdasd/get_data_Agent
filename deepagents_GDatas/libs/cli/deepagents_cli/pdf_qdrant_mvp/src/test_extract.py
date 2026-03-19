"""
简单测试脚本：获取所有集合并输出
"""

import sys
from vector_tools import QdrantManager

def test_get_collections():
    """
    测试获取所有集合
    """
    try:
        manager = QdrantManager()
        collections = manager.list_collections()
        print(f"Found {len(collections)} collections")
        
        for col in collections:
            print(f"  - {col['name']}: {col.get('points_count', 0)} points")
        
        return collections
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_get_collections()
