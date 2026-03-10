"""
删除指定名称模式的 Qdrant 集合
"""

import sys
sys.path.insert(0, '.')

from vector_tools import QdrantManager

def delete_collections_by_pattern(pattern: str) -> dict:
    """
    删除 Qdrant 向量数据库中名称包含指定模式的所有集合。
    
    该工具用于批量清理 Qdrant 数据库中的集合。它会查找所有名称中
    包含指定模式的集合，然后逐一删除。这是一个破坏性操作，请谨慎使用。
    
    Use this tool when you need to:
    - Clean up test collections from the database
    - Remove outdated document collections
    - Batch delete collections with similar names
    - Manage database storage by removing unwanted collections
    
    Args:
        pattern: 要匹配的集合名称模式字符串，所有名称中包含此字符串的集合都会被删除
        
    Returns:
        dict: 操作结果，包含以下字段：
            - status (str): 操作状态 ("success" 或 "partial")
            - deleted_count (int): 成功删除的集合数量
            - failed_count (int): 删除失败的集合数量
            - deleted_collections (list): 已删除的集合名称列表
            - failed_collections (list): 删除失败的集合名称列表
    
    Example:
        >>> result = delete_collections_by_pattern("test_")
        >>> print(f"Deleted {result['deleted_count']} collections")
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
