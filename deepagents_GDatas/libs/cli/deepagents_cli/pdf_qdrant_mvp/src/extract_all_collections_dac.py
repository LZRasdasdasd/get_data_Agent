"""
从数据库所有集合中提取双原子催化剂数据
1. 获取所有集合列表
2. 对每个集合执行双原子催化剂提取
3. 汇总所有结果
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')

from vector_tools import QdrantManager
from qdrant_config import Config
from openai import OpenAI
from extract_dac_synthesis import query_and_extract


def extract_from_all_collections(output_prefix: str = "dac_batch"):
    """
    从数据库所有集合中提取双原子催化剂数据
    
    Args:
        output_prefix: 输出文件名前缀
    
    Returns:
        list: 所有提取结果的列表
    """
    print("\n" + "="*80)
    print("开始从数据库所有集合中提取双原子催化剂数据")
    print("="*80 + "\n")
    
    # 初始化
    config = Config()
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    collection_names = [col['name'] for col in collections]
    
    print(f"\n发现 {len(collection_names)} 个集合:")
    for i, col_name in enumerate(collection_names, 1):
        points_count = next((col['points_count'] for col in collections if col['name'] == col_name), 0)
        print(f"  {i}. {col_name} ({points_count} 条记录)")
    
    print("\n" + "-"*80)
    print("开始处理各个集合...")
    print("-"*80 + "\n")
    
    # 存储所有提取结果
    all_results = []
    successful_extractions = []
    failed_extractions = []
    
    # 逐个处理集合
    for idx, collection_name in enumerate(collection_names, 1):
        print(f"\n[{idx}/{len(collection_names)} 处理集合: {collection_name}")
        print("-" * 60)
        
        try:
            # 调用现有的提取函数(使用静默模式避免过多输出)
            result = query_and_extract(collection_name=collection_name, silent=True)
            
            if result is not None:
                print(f"  ✓ 成功提取双原子催化剂数据")
                successful_extractions.append({
                    "collection_name": collection_name,
                    "status": "success"
                })
                all_results.append(result)
            else:
                print(f"  ✗ 未找到双原子催化剂数据或提取失败")
                failed_extractions.append({
                    "collection_name": collection_name,
                    "status": "not_found_or_failed"
                })
                
        except Exception as e:
            print(f"  ✗ 处理出错: {e}")
            failed_extractions.append({
                "collection_name": collection_name,
                "status": "error",
                "error": str(e)
            })
    
    # 生成汇总报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    summary_report = {
        "metadata": {
            "extraction_type": "dual-atom catalyst synthesis",
            "timestamp": timestamp,
            "total_collections": len(collection_names),
            "successful_count": len(successful_extractions),
            "failed_count": len(failed_extractions),
            "success_rate": f"{len(successful_extractions)/len(collection_names)*100:.1f}%" if collection_names else "0%"
        },
        "successful_collections": successful_extractions,
        "failed_collections": failed_extractions,
        "all_extraction_results": all_results
    }
    
    # 保存汇总报告
    output_dir = Path(__file__).parent.parent / "queried_datas"
    output_dir.mkdir(exist_ok=True)
    summary_file = output_dir / f"{output_prefix}_summary_{timestamp}.json"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    # 打印汇总信息
    print("\n" + "="*80)
    print("提取完成!")
    print("="*80)
    print(f"\n汇总统计:")
    print(f"  总集合数: {len(collection_names)}")
    print(f"  成功提取: {len(successful_extractions)}")
    print(f"  失败/未找到: {len(failed_extractions)}")
    print(f"  成功率: {summary_report['metadata']['success_rate']}")
    print(f"\n汇总报告已保存到: {summary_file}")
    
    # 打印成功提取的集合列表
    if successful_extractions:
        print(f"\n成功提取的集合 ({len(successful_extractions)}):")
        for item in successful_extractions:
            print(f"  - {item['collection_name']}")
    
    # 打印失败的集合列表
    if failed_extractions:
        print(f"\n失败/未找到的集合 ({len(failed_extractions)}):")
        for item in failed_extractions:
            print(f"  - {item['collection_name']} ({item['status']})")
    
    print("\n" + "="*80 + "\n")
    
    return summary_report


if __name__ == "__main__":
    # 支持命令行参数指定输出文件前缀
    prefix = sys.argv[1] if len(sys.argv) > 1 else "dac_batch"
    extract_from_all_collections(output_prefix=prefix)
