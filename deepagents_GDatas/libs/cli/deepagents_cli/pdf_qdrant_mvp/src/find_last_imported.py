"""
查找最后一个导入的文件名
"""
import json

def main():
    """主函数"""
    # 从Qdrant获取所有已导入的集合名称
    import requests
    response = requests.get('http://127.0.0.1:6333/collections')
    collections = response.json()['result']['collections']
    imported_collections = [col['name'] for col in collections]
    
    print(f'已导入集合数: {len(imported_collections)}')
    
    if imported_collections:
        # 找到最后一个导入的集合
        last_imported = sorted(imported_collections)[-1]
        print(f'\n最后一个导入的集合名: {last_imported}')

if __name__ == '__main__':
    main()
