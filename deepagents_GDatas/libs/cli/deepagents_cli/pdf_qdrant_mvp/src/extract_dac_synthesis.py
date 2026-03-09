"""
从 nl4c00576_si_001 集合中提取双原子催化剂合成的结构化数据
1. 查询集合获取相关文本
2. 使用 LLM 和 EXPERT_PROMPT 提取结构化数据
3. 保存为时间戳命名的 JSON 文件到 queried_datas 目录
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, '.')

from vector_tools import QdrantManager
from config import Config
from openai import OpenAI


# 化学合成领域专家提示词
EXPERT_PROMPT = """你是一位化学合成领域的资深专家。你的任务是根据给定的论文内容，找出其实验部分与结论部分，判断其是否与**双原子催化剂**的合成相关，并提取与模型反应相关的详细信息，提取的信息若有化学式，必须以化学式而不是名称表示。

### **判断标准：**
- **与化学合成无关：** 如果论文内容与化学合成无关，请输出 `-`。
- **与双原子催化剂合成相关：** 如果涉及双原子催化剂的合成，请按下列要求提取**模型反应**的信息。

### **模型反应定义：**
模型反应是文献中用于验证某类反应的可行性或优化反应条件的实验，通常展示最优条件和结果。

### **信息提取要求：**
请按照以下字段提取相关信息，确保符合化学领域的描述习惯：

1. **反应步数：**
   - 提取反应的步数，直接记录为 1 或 2（或更多步数）。
   - 示例：`3`

2. **反应单体（起始原料）：**
   - 提取每一步中使用的反应物名称及其用量，使用字典格式记录。若该步使用了催化剂，需标记 `"catalyst": true`。
   - 示例：`{"reactant": "Zn(NO3)2·6H2O", "amount": "1186 mg"}`

3. **双原子催化剂活性位点：**
   - 提取最终催化剂中活性位点的结构（通常由两个金属原子及其邻近的配位原子构成），并注明金属负载量（若提供）。
   - **如果文中明确给出了两个金属原子之间的距离（如键长、间距），请一并提取，单位应为 Å（埃），并记录在 `metal_metal_distance` 字段中。**
   - 示例：`{"active_site": "Fe2N6", "loading": "0.1 mg/cm²", "metal_metal_distance": "2.88 Å"}`

4. **温度：**
   - 提取每一步的反应温度。若有多个温度，用逗号分隔。
   - 示例：`{"step1": "room temperature", "step2": "900°C"}`

5. **反应时间：**
   - 提取每一步的反应时间。若包含多个操作（如搅拌、离心、干燥），可用文字描述。
   - 示例：`{"step1": "20 min stirring, 5 min centrifugation, overnight drying"}`

6. **反应产物：**
   - 提取每一步的中间产物或最终产物名称。若有多步，下一步的产物应是上一步的产物经处理后得到。
   - 示例：`{"step1": "solution A", "step2": "white powder (ZIF-8)", "step3": "Fe2@NG DAC"}`

7. **气氛：**
   - 提取每一步反应的气氛（如空气、Ar、N2、O2等）。
   - 示例：`{"step1": "air", "step2": "Ar"}`

8. **催化剂（如有）：**
   - 若某一步中使用了催化剂（非最终产物），需在反应物列表中标记 `"catalyst": true`。

### **输出格式：**
- 使用 JSON 格式并用英文输出。
- 对于多步反应，按顺序提取每一步信息，并记录在同一 JSON 对象中。

**示例（基于 Fe2@NG DAC 的合成）：**
```json
{
  "reaction_steps": 4,
  "step_1": {
    "reactants": [
      {"reactant": "Zn(NO3)2·6H2O", "amount": "8000 mg"},
      {"reactant": "cetyltrimethylammonium bromide", "amount": "8000 mg"},
      {"reactant": "deionized water", "amount": "8000 mL"}
    ],
    "temperature": "room temperature",
    "reaction_time": "dissolved",
    "atmosphere": "air",
    "product": "solution A"
  },
  "step_2": {
    "reactants": [
      {"reactant": "2-methylimidazole", "amount": "18.16 g"},
      {"reactant": "deionized water", "amount": "280 mL"}
    ],
    "temperature": "room temperature",
    "reaction_time": "dissolved",
    "atmosphere": "air",
    "product": "solution B"
  },
  "step_3": {
    "reactants": [
      {"reactant": "solution A", "amount": "all"},
      {"reactant": "solution B", "amount": "all"}
    ],
    "temperature": "room temperature",
    "reaction_time": "stirred at 900 rpm for 20 min, centrifuged at 5000 rpm for 5 min, vacuum-dried at 80°C overnight",
    "atmosphere": "air",
    "product": "white powder (ZIF-8)"
  },
  "step_4": {
    "reactants": [
      {"reactant": "cyclopentadienyliron dicarbonyl dimer (Fe dimer)", "amount": "2.1 mg"},
      {"reactant": "dimethyl formamide", "amount": "150 mL"},
      {"reactant": "white powder (ZIF-8)", "amount": "150 mg"},
      {"reactant": "dopamine hydrochloride", "amount": "45 mg"}
    ],
    "temperature": "room temperature, 900°C",
    "reaction_time": "stirred at 800 rpm for 12 h, collected, added to Tris-HCl + dopamine, stirred 6 h, dried, annealed at 900°C for 1 h under Ar",
    "atmosphere": "Ar (final annealing)",
    "product": "Fe2@NG DAC"
  },
  "double_atom_catalyst_active_site": {
    "active_site": "Fe2N6",
    "loading": "0.1 mg/cm² (on electrode)",
    "metal_metal_distance": "2.88 Å"
  }
}
```
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
                {"role": "user", "content": f"请根据以下论文内容提取双原子催化剂合成的结构化信息：\n\n{text_content}"}
            ],
            temperature=0.1,  # 低温度以获得更确定性的输出
            max_tokens=4096
        )
        
        response_text = response.choices[0].message.content
        print(f"\nLLM 原始响应长度: {len(response_text)} 字符")
        
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


def query_and_extract(collection_name: str = None):
    """
    查询指定集合并提取结构化数据
    
    Args:
        collection_name: 集合名称，如果为 None 则使用默认值
    """
    import sys
    
    # 如果没有指定集合名称，从命令行参数获取
    if collection_name is None:
        if len(sys.argv) > 1:
            collection_name = sys.argv[1]
        else:
            collection_name = "nl4c00576_si_001"
    
    # 初始化配置和客户端
    config = Config()
    manager = QdrantManager()
    
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=config.openai_api_key,
        base_url=config.openai_api_base
    )
    
    # 检查集合是否存在
    collections = manager.list_collections()
    collection_names = [col['name'] for col in collections]
    
    if collection_name not in collection_names:
        print(f"[ERROR] 集合 '{collection_name}' 不存在！")
        print(f"\n可用的集合: {', '.join(collection_names)}")
        return None
    
    print(f"\n{'=' * 80}")
    print(f"查询集合: {collection_name}")
    print(f"{'=' * 80}")
    
    # 查询关键词 - 针对双原子催化剂合成
    query = """双原子催化剂合成实验 experimental synthesis of dual-atom catalysts
    diatomic catalyst double-atom catalyst preparation method reaction conditions temperature time atmosphere
    active site metal dimer precursor synthesis procedure distance between two metal atoms
    metal-metal bond length bond distance Å 间距 键长 原子间距
    实验部分 合成方法 制备步骤 反应条件 温度 时间 气氛 活性位点 双原子位点 Fe2 Co2 Ni2
    synthesis procedure experimental section"""
    
    print(f"\n查询关键词:\n{query[:200]}...")
    
    # 执行查询
    try:
        # search 方法直接返回列表
        search_results = manager.search(
            collection_name=collection_name,
            query_text=query,
            n_results=10,
            score_threshold=0.3
        )
        
        if not search_results:
            print("没有找到相关结果")
            return None
        
        print(f"\n找到 {len(search_results)} 个结果")
        
        # 合并所有查询结果的文本
        combined_text = ""
        for i, result in enumerate(search_results):
            text = result.get("text", "")
            score = result.get("score", 0)
            combined_text += f"\n\n--- 结果 {i+1} (相似度: {score:.2%}) ---\n{text}"
        
        print(f"\n合并文本总长度: {len(combined_text)} 字符")
        
        # 调用 LLM 提取结构化数据
        extraction_result = call_llm_for_extraction(client, combined_text)
        
        # 准备输出数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"nl4c00576_si_001_extraction_{timestamp}.json"
        output_dir = Path(__file__).parent.parent / "queried_datas"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / output_filename
        
        output_data = {
            "metadata": {
                "collection_name": collection_name,
                "query": query,
                "timestamp": timestamp,
                "total_results": len(search_results),
                "combined_text_length": len(combined_text)
            },
            "query_results": [
                {
                    "text": r.get("text", "")[:500] + "..." if len(r.get("text", "")) > 500 else r.get("text", ""),
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
        
        print(f"\n{'=' * 80}")
        print(f"结果已保存到: {output_path}")
        print(f"{'=' * 80}")
        
        # 打印提取的结构化数据
        if extraction_result.get("success"):
            print("\n提取的结构化数据:")
            print(json.dumps(extraction_result.get("data", {}), ensure_ascii=False, indent=2))
        else:
            print(f"\n提取失败: {extraction_result.get('error', '未知错误')}")
        
        return output_data
        
    except Exception as e:
        print(f"[ERROR] 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    query_and_extract()
