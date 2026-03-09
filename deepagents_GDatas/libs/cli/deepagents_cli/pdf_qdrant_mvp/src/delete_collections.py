"""
删除指定名称模式的 Qdrant 集合
"""

import sys
sys.path.insert(0, '.')

from vector_tools import QdrantManager

def delete_collections_by_pattern(pattern: str):
    """
    删除名称包含指定模式的集合
    
    Args:
        pattern: 要匹配的模式字符串
    """
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    print(f"\n当前所有集合 ({len(collections)} 个):")
    for col in collections:
        print(f"  - {col['name']} ({col['points_count']} 点)")
    
    # 找到匹配的集合
    matching = [col for col in collections if pattern in col['name']]
    
    if not matching:
        print(f"\n没有找到包含 '{pattern}' 的集合")
        return
    
    print(f"\n找到 {len(matching)} 个包含 '{pattern}' 的集合:")
    for col in matching:
        print(f"  - {col['name']} ({col['points_count']} 点)")
    
    # 删除匹配的集合
    print(f"\n开始删除...")
    for col in matching:
        result = manager.delete_collection(col['name'])
        if result['status'] == 'deleted':
            print(f"  [OK] 已删除: {col['name']}")
        else:
            print(f"  [ERROR] 删除失败: {col['name']} - {result.get('message', 'Unknown error')}")
    
    print("\n删除完成!")

if __name__ == "__main__":
    # 删除包含 "gas_reduced" 的集合
    delete_collections_by_pattern("gas_reduced")
