"""
搜索所有集合中实验部分的温度信息
"""

import sys
sys.path.insert(0, '.')

from vector_tools import QdrantManager

def search_temperature_in_all_collections():
    """在所有集合中搜索温度信息"""
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    print(f"\n找到 {len(collections)} 个集合")
    
    # 查询关键词
    query = "实验部分的温度是多少 experimental temperature condition"
    
    print(f"\n查询: {query}")
    print("=" * 80)
    
    all_results = []
    
    for col in collections:
        collection_name = col['name']
        print(f"\n正在搜索集合: {collection_name}")
        
        try:
            results = manager.search(
                collection_name=collection_name,
                query_text=query,
                n_results=3,
                score_threshold=0.5
            )
            
            if results:
                for r in results:
                    r['collection'] = collection_name
                    all_results.append(r)
                    print(f"  [相似度: {r['score']:.2%}]")
                    print(f"  来源: {r.get('source_file', '未知')}")
                    text = r['text']
                    # 显示完整文本
                    print(f"  内容: {text[:500]}..." if len(text) > 500 else f"  内容: {text}")
                    print()
        except Exception as e:
            print(f"  搜索失败: {e}")
    
    # 按相似度排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "=" * 80)
    print("最相关的结果 (Top 5):")
    print("=" * 80)
    
    for i, r in enumerate(all_results[:5]):
        print(f"\n[{i+1}] 相似度: {r['score']:.2%}")
        print(f"集合: {r['collection']}")
        print(f"来源: {r.get('source_file', '未知')}")
        print(f"内容:\n{r['text']}")
        print("-" * 40)

if __name__ == "__main__":
    search_temperature_in_all_collections()
