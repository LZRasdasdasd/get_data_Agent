"""
从 集合中提取双原子催化剂合成的结构化数据
1. 查询集合获取相关文本
2. 使用 LLM 和 EXPERT_PROMPT 提取结构化数据
3. 保存为论文名称命名的 JSON 文件到 queried_datas 目录
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# 将脚本所在目录加入路径，确保能导入同级模块
sys.path.insert(0, str(Path(__file__).parent))

from vector_tools import QdrantManager
from qdrant_config import Config
from openai import OpenAI


# 化学合成领域专家提示词
EXPERT_PROMPT = """
'''你是一位化学合成领域的资深专家。你的任务是根据给定的论文内容（包括正文和补充材料），找出其实验部分与结论部分，判断其是否与双原子催化剂的合成相关，并提取与合成相关的详细信息。

判断标准：
- 与双原子催化剂合成无关：如果论文不涉及双原子催化剂的实验合成（例如纯理论计算、综述、或催化剂用于催化反应但无双原子合成细节），请输出 "-"。
- 与双原子催化剂合成相关：如果涉及双原子催化剂的合成（包括前驱体制备、热解、负载等步骤），请按下列要求提取合成步骤的信息。

提取字段说明：

1. paper_title：论文的完整英文标题（字符串）。

2. reaction_steps：合成步骤总数（整数）。

3. step_1, step_2, ...：按顺序提取每一步的详细信息。
   - reactants：数组，每个元素为字典，包含 "reactant"（优先使用化学式，同时用括号保留原始描述，如 "CuSO4·5H2O (copper(II) sulfate pentahydrate)"）、"amount"（用量，如 "10 mg", "5 mmol"）、"catalyst"（布尔值，仅当该物质在此步中作为催化剂使用时为 true，否则为 false）。注意：最终催化剂本身不作为催化步骤中的催化剂标记。
   - temperature：反应温度（摄氏度，如 "500 °C"；若为室温写 "25 °C"；不是摄氏度的转换为摄氏度，例如：873 K 需要等价600 °C；若有多个温度用逗号分隔；）。未提供则写 ""。
   - reaction_time：反应时间（小时，可包含多步操作）。未提供则写 ""。
   - atmosphere：气氛（如 "air", "Ar", "N2", "O2"，"vacuum"）。未提供则写 ""。
   - product：该步产物名称（优先使用化学式或标准缩写，可保留原始描述）。未提供则写 ""。

4. double_atom_catalyst_active_site：最终双原子催化剂活性位点的结构信息。
   - active_site：活性位点描述（如 "N3-Fe-Co-N3", "CuC4/CoN4@HC"）。未提供则写 ""。
   - loading：金属负载量（字符串，如 "Fe: 1.08 wt%, Co: 1.03 wt%"）。未提供则写 ""。
   - metal_metal_distance：两个金属原子之间的距离（字符串，单位 Å，如 "2.5 Å"）。未提供则写 ""。
   - metal_coordination：每个金属的配位环境（字典）。格式：
     {
       "金属1": {"coordinating_elements": ["N", "O"], "coordination_numbers": {"N": 数值, "O": 数值}},
       "金属2": {"coordinating_elements": ["N", "O"], "coordination_numbers": {"N": 数值, "O": 数值}}
     }
     若某种配位元素是混合配位（例如 N 和 O 共同贡献但无法区分具体数量），则使用 "N/O" 作为键合元素，如 {"N/O": 5.6}。若配位数未提供，则 coordination_numbers 写 {}。

5. catalytic_performance（可选）：论文中报告的主要催化性能指标（字典格式）。未提供则写 {}。

输出格式：
- 使用 JSON 格式输出，所有字段名和字符串值使用英文双引号。
- 对于多步反应，按 step_1, step_2, ... 依次记录。
- 所有化学物质尽量使用化学式，同时在化学式的右边用括号保留原始描述（如原文提供了英文名称或俗名）。
- 未提供的信息统一写空字符串 "" 或空对象 {}，不要写 "not specified"。

示例：

{
  "paper_title": "Dual-Metal Hetero-Single-Atoms with Different Coordination for Efficient Synergistic Catalysis",
  "reaction_steps": 3,
  "step_1": {
    "reactants": [
      {"reactant": "H2BDC (p-phthalic acid)", "amount": "12 mmol (1.994 g)", "catalyst": false},
      {"reactant": "NaOH", "amount": "25 mmol (1.0 g)", "catalyst": false},
      {"reactant": "CuSO4·5H2O (copper(II) sulfate pentahydrate)", "amount": "15 mmol (3.75 g)", "catalyst": false},
      {"reactant": "H2O (deionized water)", "amount": "360 mL", "catalyst": false}
    ],
    "temperature": "25 °C",
    "reaction_time": "5 h (stirring) + 24 h (vacuum drying)",
    "atmosphere": "air",
    "product": "Cu-MOF"
  },
  "step_2": {
    "reactants": [
      {"reactant": "Cu-MOF", "amount": "mixed with KCl-KBr 1:40 by weight", "catalyst": false},
      {"reactant": "KCl-KBr (1:3 by weight)", "amount": "", "catalyst": false}
    ],
    "temperature": "730 °C",
    "reaction_time": "180 min (heating rate 2 °C/min) + 4 h (aqua regia immersion)",
    "atmosphere": "Ar",
    "product": "CuC4@HC"
  },
  "step_3": {
    "reactants": [
      {"reactant": "CuC4@HC", "amount": "0.1 g", "catalyst": false},
      {"reactant": "MTPP-Co (vitamin B12 derivative)", "amount": "0.1 g", "catalyst": false},
      {"reactant": "C2H5OH (ethanol)", "amount": "20 mL", "catalyst": false}
    ],
    "temperature": "70 °C (rotary evaporation) + 800 °C (pyrolysis)",
    "reaction_time": "2 h (pyrolysis, heating rate 2 °C/min)",
    "atmosphere": "Ar",
    "product": "CuC4/CoN4@HC"
  },
  "double_atom_catalyst_active_site": {
    "active_site": "CuC4 (Cu-C4) and CoN4 (Co-N4) on hollow carbon",
    "loading": {"Cu": "1.20 wt%", "Co": "1.84 wt%"},
    "metal_metal_distance": "",
    "metal_coordination": {
      "Cu": {"coordinating_elements": ["C"], "coordination_numbers": {"C": 3.8}},
      "Co": {"coordinating_elements": ["N", "C"], "coordination_numbers": {"N/O": 5.6, "C": 3.8}}
    }
  },
  "catalytic_performance": {
    "oxidative esterification of furfural to methyl furoate": "100% conversion, 100% yield"
  }
}

注意事项：
- 仅提取催化剂合成部分，不提取催化剂用于催化反应的步骤。
- 若论文中合成了多个不同金属组合的 DAC，请分别输出每个催化剂的完整 JSON 对象（可作为数组或在回答中分条列出）。
- 所有温度统一转换为摄氏度（°C），时间统一使用小时（h）。
- 对于从补充材料中获取的数据，直接提取，无需额外标注来源。
- 未提供的信息统一写空字符串 "" 或空对象 {}，不要写 "not specified"。
'''
"""


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    从 LLM 响应中提取 JSON 对象
    
    Args:
        response_text: LLM 返回的文本
        
    Returns:
        解析后的 JSON 字典，如果解析失败则返回 None
    """
    # 尝试直接解析
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # 尝试从 markdown 代码块中提取
    json_pattern = r'```json\s*(\{.*?\})\s*```'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    
    # 尝试找第一个 { 和最后一个 }
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(response_text[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def call_llm_for_extraction(client: OpenAI, text_content: str, model: str = "qwen-plus") -> Dict[str, Any]:
    """
    调用 LLM 提取结构化数据
    
    Args:
        client: OpenAI 客户端
        text_content: 要处理的文本内容
        model: 使用的模型名称
        
    Returns:
        提取的结构化数据
    """
    print(f"\n正在调用 LLM ({model}) 提取结构化数据...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXPERT_PROMPT},
                {"role": "user", "content": f"请根据以下论文内容提取双原子催化剂合成的结构化信息。\n\n【重要】请直接输出JSON，不要输出任何分析、解释或说明文字。只输出JSON对象。\n\n论文内容：\n{text_content}"}
            ],
            temperature=0.1,  # 低温度以获得更确定性的输出
            max_tokens=8192
        )
        
        response_text = response.choices[0].message.content
        print(f"\nLLM 原始响应长度: {len(response_text)} 字符")
        print(f"\nLLM 原始响应内容:\n{response_text[:500]}...")
        
        # 提取 JSON
        extracted_data = extract_json_from_response(response_text)
        
        if extracted_data:
            print("成功从响应中提取 JSON 数据")
            return {
                "success": True,
                "data": extracted_data,
                "raw_response": response_text
            }
        else:
            print("警告: 无法从响应中提取有效的 JSON")
            return {
                "success": False,
                "error": "无法解析 JSON",
                "raw_response": response_text
            }
            
    except Exception as e:
        print(f"调用 LLM 时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "raw_response": None
        }


def query_and_extract(collection_name: str = None, silent: bool = False):
    """
    从 Qdrant 集合中提取双原子催化剂（DAC）合成的结构化数据。
    
    该工具用于从已索引的科学论文中提取双原子催化剂的合成信息。
    它会先在指定的 Qdrant 集合中搜索与双原子催化剂合成相关的内容，
    然后使用 LLM（大语言模型）将非结构化文本转换为结构化的 JSON 数据。
    
    Use this tool when you need to:
    - Extract dual-atom catalyst synthesis information from scientific papers
    - Structure experimental details for catalyst preparation
    - Retrieve information about active sites, precursors, and reaction conditions
    - Parse catalyst synthesis procedures from research documents
    
    Args:
        collection_name: Qdrant 集合名称，通常是 PDF 文件名的小写下划线形式。
                        如果为 None，则使用默认值 "nl4c00576_si_002"
        silent: 静默模式，为 True 时禁用所有打印输出（用于工具调用时避免 markup 错误）
                        
    Returns:
        dict: 包含提取结果的字典，结构如下：
            - metadata (dict): 元数据（集合名、查询、时间戳等）
            - query_results (list): 向量搜索的原始结果
            - extraction (dict): LLM 提取的结构化数据，包含：
                - reaction_steps (int): 反应步数
                - step_X (dict): 每步的详细信息（反应物、温度、时间、产物等）
                - double_atom_catalyst_active_site (dict): 活性位点信息
    
    Example:
        >>> result = query_and_extract("paper_collection")
        >>> print(result["extraction"]["data"]["reaction_steps"])
    """
    import sys
    
    # 辅助函数：仅在非静默模式下打印
    def log(msg: str = ""):
        if not silent:
            print(msg)
    
    # 如果没有指定集合名称，从命令行参数获取
    if collection_name is None:
        if len(sys.argv) > 1:
            collection_name = sys.argv[1]
        else:
            collection_name = "nl4c00576_si_002"
    
    # 初始化配置和客户端
    config = Config()
    manager = QdrantManager()
    
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_api_base,
        timeout=60.0,  # 设置超时时间为 60 秒
        max_retries=2  # 失败后重试 2 次
    )
    
    # 检查集合是否存在
    collections = manager.list_collections()
    collection_names = [col['name'] for col in collections]
    
    if collection_name not in collection_names:
        log(f"[ERROR] 集合 '{collection_name}' 不存在！")
        log(f"\n可用的集合: {', '.join(collection_names)}")
        return None
    
    log(f"\n{'=' * 80}")
    log(f"查询集合: {collection_name}")
    log(f"{'=' * 80}")
    
    # 查询关键词 - 针对双原子催化剂合成
    query = """双原子催化剂合成实验 experimental synthesis of dual-atom catalysts
    diatomic catalyst double-atom catalyst preparation method reaction conditions temperature time atmosphere
    active site metal dimer precursor synthesis procedure distance between two metal atoms
    metal-metal bond length bond distance Å 间距 键长 原子间距
    实验部分 合成方法 制备步骤 反应条件 温度 时间 气氛 活性位点 双原子位点 Fe2 Co2 Ni2
    synthesis procedure experimental section"""
    
    log(f"\n查询关键词:\n{query[:200]}...")
    
    # 执行查询
    try:
        # search 方法直接返回列表
        search_results = manager.search(
            collection_name=collection_name,
            query=query,
            limit=10,
            score_threshold=0.3
        )
        
        if not search_results:
            log("没有找到相关结果")
            return None
        
        log(f"\n找到 {len(search_results)} 个结果")
        
        # 合并所有查询结果的文本
        combined_text = ""
        for i, result in enumerate(search_results):
            # 文本存储在payload字典中
            text = result.get("payload", {}).get("text", "")
            score = result.get("score", 0)
            combined_text += f"\n\n--- 结果 {i+1} (相似度: {score:.2%}) ---\n{text}"
        
        log(f"\n合并文本总长度: {len(combined_text)} 字符")
        
        # 调用 LLM 提取结构化数据
        extraction_result = call_llm_for_extraction(client, combined_text)
        
        # 检查是否成功提取数据
        if not extraction_result.get("success"):
            log(f"\n{'=' * 80}")
            log(f"JSON 解析失败: {extraction_result.get('error', '未知错误')}")
            log(f"未生成 JSON 文件（跳过保存）")
            log(f"{'=' * 80}")
            return None
        
        # 只有成功提取数据时才准备并保存输出
        # 使用集合名称（源自论文名称）转换为可读格式作为 JSON 文件名，不加时间戳
        # 集合名用下划线（Qdrant限制），文件名用空格更可读
        paper_name = collection_name.replace('_', ' ')
        output_filename = f"{paper_name}.json"
        output_dir = Path(__file__).parent.parent / "queried_datas"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / output_filename
        
        output_data = {
            "metadata": {
                "collection_name": collection_name,
                "query": query,
                "total_results": len(search_results),
                "combined_text_length": len(combined_text)
            },
            "query_results": [
                {
                    "text": (r.get("payload", {}).get("text", "")[:500] + "..." if len(r.get("payload", {}).get("text", "")) > 500 else r.get("payload", {}).get("text", "")),
                    "score": r.get("score", 0),
                    "chunk_index": r.get("payload", {}).get("chunk_index", -1)
                }
                for r in search_results
            ],
            "extraction": extraction_result
        }
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        log(f"\n{'=' * 80}")
        log(f"结果已保存到: {output_path}")
        log(f"{'=' * 80}")
        
        # 打印提取的结构化数据
        log("\n提取的结构化数据:")
        log(json.dumps(extraction_result.get("data", {}), ensure_ascii=False, indent=2))
        
        return output_data
        
    except Exception as e:
        log(f"[ERROR] 处理过程中出错: {e}")
        if not silent:
            import traceback
            traceback.print_exc()
        return None


if __name__ == "__main__":
    query_and_extract()
