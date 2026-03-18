"""
增量提取新集合的双原子催化剂数据
1. 读取现有批处理摘要文件中的已处理集合
2. 查询数据库获取当前所有集合
3. 比较两者，找出新集合
4. 只对新集合执行提取
5. 将新结果追加到现有摘要中，生成新的摘要文件
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


def load_existing_summary(summary_file: str) -> dict:
    """加载现有的批处理摘要文件"""
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_processed_collections(summary: dict) -> set:
    """从摘要中获取已处理的集合名称集合"""
    processed = set()
    
    # 获取成功提取的集合
    for item in summary.get('successful_collections', []):
        processed.add(item['collection_name'])
    
    # 获取失败的集合
    for item in summary.get('failed_collections', []):
        processed.add(item['collection_name'])
    
    return processed


def extract_from_new_collections(
    existing_summary_file: str,
    output_prefix: str = "dac_batch_incremental"
):
    """
    只从新的集合中提取双原子催化剂数据
    
    Args:
        existing_summary_file: 现有摘要文件的路径
        output_prefix: 输出文件名前缀
    
    Returns:
        dict: 更新后的摘要报告
    """
    print("\n" + "="*80)
    print("增量提取新集合的双原子催化剂数据")
    print("="*80 + "\n")
    
    # 加载现有摘要
    print(f"加载现有摘要文件: {existing_summary_file}")
    existing_summary = load_existing_summary(existing_summary_file)
    
    # 获取已处理的集合
    processed_collections = get_processed_collections(existing_summary)
    print(f"已处理集合数量: {len(processed_collections)}")
    
    # 初始化
    config = Config()
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    all_collection_names = [col['name'] for col in collections]
    print(f"数据库中总集合数量: {len(all_collection_names)}")
    
    # 找出新集合
    new_collection_names = [name for name in all_collection_names if name not in processed_collections]
    print(f"新集合数量: {len(new_collection_names)}")
    
    if not new_collection_names:
        print("\n没有发现新集合，无需提取。")
        return existing_summary
    
    print(f"\n发现 {len(new_collection_names)} 个新集合:")
    for i, col_name in enumerate(new_collection_names, 1):
        points_count = next((col['points_count'] for col in collections if col['name'] == col_name), 0)
        print(f"  {i}. {col_name} ({points_count} 条记录)")
    
    print("\n" + "-"*80)
    print("开始处理新集合...")
    print("-"*80 + "\n")
    
    # 存储新提取结果
    new_results = []
    new_successful_extractions = []
    new_failed_extractions = []
    
    # 逐个处理新集合
    for idx, collection_name in enumerate(new_collection_names, 1):
        print(f"\n[{idx}/{len(new_collection_names)} 处理集合: {collection_name}")
        print("-" * 60)
        
        try:
            # 调用现有的提取函数(使用静默模式避免过多输出)
            result = query_and_extract(collection_name=collection_name, silent=True)
            
            if result is not None:
                print(f"  ✓ 成功提取双原子催化剂数据")
                new_successful_extractions.append({
                    "collection_name": collection_name,
                    "status": "success"
                })
                new_results.append(result)
            else:
                print(f"  ✗ 未找到双原子催化剂数据或提取失败")
                new_failed_extractions.append({
                    "collection_name": collection_name,
                    "status": "not_found_or_failed"
                })
                
        except Exception as e:
            print(f"  ✗ 处理出错: {e}")
            new_failed_extractions.append({
                "collection_name": collection_name,
                "status": "error",
                "error": str(e)
            })
    
    # 合并旧的和新的结果
    all_successful = existing_summary.get('successful_collections', []) + new_successful_extractions
    all_failed = existing_summary.get('failed_collections', []) + new_failed_extractions
    all_results = existing_summary.get('all_extraction_results', []) + new_results
    
    # 计算总计数量
    total_successful = len(all_successful)
    total_failed = len(all_failed)
    total_collections = total_successful + total_failed
    success_rate = f"{total_successful/total_collections*100:.1f}%" if total_collections > 0 else "0%"
    
    # 生成新的汇总报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    summary_report = {
        "metadata": {
            "extraction_type": "dual-atom catalyst synthesis",
            "timestamp": timestamp,
            "previous_summary": existing_summary_file,
            "total_collections": total_collections,
            "new_collections_processed": len(new_collection_names),
            "new_successful": len(new_successful_extractions),
            "new_failed": len(new_failed_extractions),
            "successful_count": total_successful,
            "failed_count": total_failed,
            "success_rate": success_rate
        },
        "successful_collections": all_successful,
        "failed_collections": all_failed,
        "all_extraction_results": all_results
    }
    
    # 保存新的汇总报告
    output_dir = Path(existing_summary_file).parent
    summary_file = output_dir / f"{output_prefix}_summary_{timestamp}.json"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    # 打印汇总信息
    print("\n" + "="*80)
    print("增量提取完成!")
    print("="*80)
    print(f"\n本次提取统计:")
    print(f"  新集合数: {len(new_collection_names)}")
    print(f"  本次成功: {len(new_successful_extractions)}")
    print(f"  本次失败: {len(new_failed_extractions)}")
    print(f"\n累计统计:")
    print(f"  总集合数: {total_collections}")
    print(f"  累计成功: {total_successful}")
    print(f"  累计失败: {total_failed}")
    print(f"  成功率: {success_rate}")
    print(f"\n新的汇总报告已保存到: {summary_file}")
    
    # 打印本次成功提取的集合列表
    if new_successful_extractions:
        print(f"\n本次成功提取的集合 ({len(new_successful_extractions)}):")
        for item in new_successful_extractions:
            print(f"  - {item['collection_name']}")
    
    # 打印本次失败的集合列表
    if new_failed_extractions:
        print(f"\n本次失败/未找到的集合 ({len(new_failed_extractions)}):")
        for item in new_failed_extractions:
            print(f"  - {item['collection_name']} ({item['status']})")
    
    print("\n" + "="*80 + "\n")
    
    return summary_report


if __name__ == "__main__":
    # 默认的现有摘要文件路径
    default_summary = Path(__file__).parent.parent / "dac_batch_summary_20260317_142400.json"
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        existing_summary_file = sys.argv[1]
    else:
        existing_summary_file = str(default_summary)
    
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "dac_batch_incremental"
    
    if not Path(existing_summary_file).exists():
        print(f"错误: 找不到摘要文件 {existing_summary_file}")
        sys.exit(1)
    
    extract_from_new_collections(
        existing_summary_file=existing_summary_file,
        output_prefix=output_prefix
    )
