"""
搜索单原子催化剂合成相关内容并使用 LLM 提取结构化信息
"""

import sys
import json
sys.path.insert(0, '.')

from vector_tools import QdrantManager
from openai import OpenAI
from config import config

# 化学合成领域专家提示词
EXPERT_PROMPT = """你是一位化学合成领域的资深专家。你的任务是根据给定的论文内容，找出其实验部分与结论部分，判断其是否与单原子催化剂的合成相关，并提取与模型反应相关的详细信息，提取的信息若有化学式，必须以化学式而不是名称表示。

### **判断标准：**
- **与化学合成无关：** 如果论文内容与化学合成无关，请输出 -。
- **与化学合成相关：** 如果涉及化学合成，请按下列要求提取**模型反应**的信息。

### **模型反应定义：**
模型反应是文献中用于验证某类反应的可行性或优化反应条件的实验，通常展示最优条件和结果。

### **信息提取要求：**
请按照以下字段提取相关信息，确保符合有机化学领域的描述习惯：

1. **反应步数：**
   - 提取反应的步数，直接记录为 1 或 2。
   - 示例：1 或 2。

2. **反应单体：**
   - 提取反应物名称及其用量，使用字典格式记录。
   - 示例：{"单体":"三聚氰胺(C3H6N6)", "计量":"0.4 mol"}。

3. **单原子催化剂活性位点：**
   - 提取催化剂的活性位点通常包括单个金属原子、该单个金属原子在载体表面的邻近原子，通常在其制备的最后一步，是最后一步反应的反应产物。
   - 示例：{"活性位点":"CuN4", "计量":"10 mol%"}。

4. **温度：**
   - 提取反应温度，若包含多个操作步骤，分别记录每个步骤的温度。
   - 示例：{"反应1":"20℃", "反应2":"90℃"}。

5. **反应时间：**
   - 提取反应时间，若包含多个操作步骤，分别记录每个步骤的时间。
   - 示例：{"反应1":"30分钟", "反应2":"6小时"}。

6. **反应产物：**
   - 提取产物名称。若有多步反应，则反应产物是下一步反应的反应单体。
   - 示例："反应1产物":"三羟甲基三聚氰胺(C6H12N6O3)"。

7. **气氛：**
   - 提取反应的气氛。
   - 示例："O2"。

8. **催化剂：**
   - 若在某个反应步骤中有催化剂，则需要进行标记。

### **多步反应的处理：**
- **多步反应：**
  - 对于多步反应，依次提取每一步的详细信息，并记录在同一 json 对象内。

### **输出格式：**
- 使用 json 格式并用英文输出。
- 每个模型反应独立记录。对于多步反应，按顺序提取每步信息并记录在同一对象中。

**示例输出:**
```json
{
  "is_related_to_synthesis": true,
  "reaction_steps": 2,
  "step_1": {
    "reactants": [
      {"reactant_A": "melamine (C3H6N6)", "amount": "10 g"},
      {"reactant_B": "formaldehyde solution (37%, stabilized with 10-15% methanol)", "amount": "20 mL"},
      {"reactant_C": "ethanol (C2H5OH)", "amount": "30 mL"},
      {"catalyst": "DMAP"}
    ],
    "temperature": "80°C",
    "reaction_time": "1 hour",
    "atmosphere": "O2",
    "product": "trimethylolmelamine"
  },
  "step_2": {
    "reactants": [
      {"reactant_A": "trimethylolmelamine", "amount": "10 g"},
      {"reactant_B": "copper nitrate (Cu(NO3)2)", "amount": "19.6 mg"},
      {"reactant_C": "ethanol (C2H5OH)", "amount": "30 mL"}
    ],
    "temperature": "550°C",
    "reaction_time": "4 hours",
    "atmosphere": "O2",
    "product": "Cu1/CN single-atom catalyst (0.4 wt% Cu)"
  },
  "single_atom_catalyst_active_site": {
    "active_site": "CuN4"
  }
}
```

如果内容与化学合成无关，请输出：
```json
{
  "is_related_to_synthesis": false,
  "reason": "brief explanation"
}
```
"""


class CatalystInfoExtractor:
    """单原子催化剂信息提取器"""
    
    def __init__(self):
        self.qdrant = QdrantManager()
        self.llm_client = OpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_api_base
        )
    
    def search_related_content(self, query: str = None, top_k: int = 10, score_threshold: float = 0.4):
        """
        搜索相关内容
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            list: 搜索结果列表
        """
        if query is None:
            query = """单原子催化剂合成实验 experimental synthesis of single-atom catalysts 
            preparation method reaction conditions temperature time atmosphere 
            active site metal precursor precursor synthesis procedure
            实验部分 合成方法 制备步骤 反应条件 温度 时间 气氛 活性位点"""
        
        collections = self.qdrant.list_collections()
        print(f"\n找到 {len(collections)} 个集合")
        
        all_results = []
        
        for col in collections:
            collection_name = col['name']
            try:
                results = self.qdrant.search(
                    collection_name=collection_name,
                    query_text=query,
                    n_results=top_k,
                    score_threshold=score_threshold
                )
                
                if results:
                    for r in results:
                        r['collection'] = collection_name
                        all_results.append(r)
            except Exception as e:
                print(f"  搜索集合 {collection_name} 失败: {e}")
        
        # 按相似度排序
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return all_results[:top_k]
    
    def extract_with_llm(self, content: str, source_file: str = ""):
        """
        使用 LLM 提取结构化信息
        
        Args:
            content: 论文内容
            source_file: 来源文件名
            
        Returns:
            dict: 提取的结构化信息
        """
        prompt = f"""{EXPERT_PROMPT}

请分析以下论文内容并提取相关信息：

---论文内容开始---
{content}
---论文内容结束---

请严格按照上述 JSON 格式输出提取结果。只输出 JSON，不要输出其他内容。"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": "你是一位化学合成领域的资深专家，专门负责从论文中提取单原子催化剂合成的相关信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 尝试提取 JSON
            # 移除可能的 markdown 代码块标记
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            result['source_file'] = source_file
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            return {
                "is_related_to_synthesis": False,
                "reason": "JSON parsing failed",
                "raw_response": result_text if 'result_text' in locals() else "No response",
                "source_file": source_file
            }
        except Exception as e:
            print(f"LLM 调用错误: {e}")
            return {
                "is_related_to_synthesis": False,
                "reason": str(e),
                "source_file": source_file
            }
    
    def process_and_extract(self, query: str = None, top_k: int = 10):
        """
        搜索并提取信息的主函数
        
        Args:
            query: 查询文本
            top_k: 处理的结果数量
            
        Returns:
            list: 提取结果列表
        """
        print("=" * 80)
        print("搜索单原子催化剂合成相关内容...")
        print("=" * 80)
        
        # 搜索相关内容
        results = self.search_related_content(query=query, top_k=top_k)
        print(f"\n找到 {len(results)} 个相关结果")
        
        extracted_results = []
        
        for i, result in enumerate(results):
            print(f"\n[{i+1}/{len(results)}] 处理: {result.get('source_file', '未知')}")
            print(f"  相似度: {result['score']:.2%}")
            
            # 提取信息
            extracted = self.extract_with_llm(
                content=result['text'],
                source_file=result.get('source_file', '未知')
            )
            
            extracted['score'] = result['score']
            extracted['collection'] = result.get('collection', '未知')
            extracted_results.append(extracted)
            
            # 显示结果
            if extracted.get('is_related_to_synthesis'):
                print(f"  ✓ 与化学合成相关")
                print(f"  反应步数: {extracted.get('reaction_steps', 'N/A')}")
                if 'single_atom_catalyst_active_site' in extracted:
                    print(f"  活性位点: {extracted['single_atom_catalyst_active_site']}")
            else:
                print(f"  ✗ 与化学合成无关: {extracted.get('reason', '未知原因')}")
        
        return extracted_results
    
    def save_results(self, results: list, output_file: str = "catalyst_extraction_results.json"):
        """
        保存结果到文件
        
        Args:
            results: 提取结果列表
            output_file: 输出文件名
        """
        import os
        output_path = os.path.join(os.path.dirname(__file__), '..', output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_path}")


def main():
    """主函数"""
    extractor = CatalystInfoExtractor()
    
    # 搜索并提取信息
    results = extractor.process_and_extract(top_k=10)
    
    # 过滤出与化学合成相关的结果
    related_results = [r for r in results if r.get('is_related_to_synthesis')]
    
    print("\n" + "=" * 80)
    print("提取结果汇总")
    print("=" * 80)
    print(f"总处理数: {len(results)}")
    print(f"与化学合成相关: {len(related_results)}")
    print(f"与化学合成无关: {len(results) - len(related_results)}")
    
    # 显示相关结果的详细信息
    for i, result in enumerate(related_results):
        print(f"\n--- 相关结果 {i+1} ---")
        print(f"来源: {result.get('source_file', '未知')}")
        print(f"相似度: {result.get('score', 0):.2%}")
        print(f"反应步数: {result.get('reaction_steps', 'N/A')}")
        
        # 显示每步反应信息
        for step_key in [k for k in result.keys() if k.startswith('step_')]:
            step_info = result[step_key]
            print(f"\n{step_key}:")
            print(f"  反应物: {step_info.get('reactants', [])}")
            print(f"  温度: {step_info.get('temperature', 'N/A')}")
            print(f"  时间: {step_info.get('reaction_time', 'N/A')}")
            print(f"  气氛: {step_info.get('atmosphere', 'N/A')}")
            print(f"  产物: {step_info.get('product', 'N/A')}")
        
        if 'single_atom_catalyst_active_site' in result:
            print(f"\n活性位点: {result['single_atom_catalyst_active_site']}")
    
    # 保存结果
    extractor.save_results(results)
    
    return results


if __name__ == "__main__":
    main()
