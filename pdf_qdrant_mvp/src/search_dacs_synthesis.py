"""
搜索所有集合中双原子催化剂合成相关的实验和结论信息
"""

import sys
sys.path.insert(0, '.')

from vector_tools import QdrantManager

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
   - 示例：`{"active_site": "Fe2N6", "loading": "0.1 mg/cm²"}`

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
      {"reactant": "Zn(NO3)2·6H2O", "amount": "1186 mg"},
      {"reactant": "cetyltrimethylammonium bromide", "amount": "30 mg"},
      {"reactant": "deionized water", "amount": "40 mL"}
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
    "loading": "0.1 mg/cm² (on electrode)"
  }
}
"""


def search_catalyst_synthesis_in_all_collections():
    """在所有集合中搜索双原子催化剂合成信息"""
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    print(f"\n找到 {len(collections)} 个集合")
    
    # 查询关键词 - 针对双原子催化剂合成
    query = """双原子催化剂合成实验 experimental synthesis of dual-atom catalysts 
    diatomic catalyst double-atom catalyst preparation method reaction conditions temperature time atmosphere 
    active site metal dimer precursor synthesis procedure
    实验部分 合成方法 制备步骤 反应条件 温度 时间 气氛 活性位点 双原子位点 Fe2 Co2 Ni2"""
    
    print(f"\n专家提示词:\n{'-' * 40}")
    print(EXPERT_PROMPT[:500] + "...")
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
                n_results=5,
                score_threshold=0.4
            )
            
            if results:
                for r in results:
                    r['collection'] = collection_name
                    all_results.append(r)
                    print(f"  [相似度: {r['score']:.2%}]")
                    print(f"  来源: {r.get('source_file', '未知')}")
                    text = r['text']
                    # 显示完整文本
                    print(f"  内容: {text[:800]}..." if len(text) > 800 else f"  内容: {text}")
                    print()
            else:
                print(f"  未找到相关结果")
        except Exception as e:
            print(f"  搜索失败: {e}")
    
    # 按相似度排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "=" * 80)
    print("最相关的结果 (Top 10):")
    print("=" * 80)
    
    for i, r in enumerate(all_results[:10]):
        print(f"\n[{i+1}] 相似度: {r['score']:.2%}")
        print(f"集合: {r['collection']}")
        print(f"来源: {r.get('source_file', '未知')}")
        print(f"内容:\n{r['text']}")
        print("-" * 40)
    
    return all_results


def get_expert_prompt():
    """获取化学合成专家提示词"""
    return EXPERT_PROMPT


if __name__ == "__main__":
    search_catalyst_synthesis_in_all_collections()
