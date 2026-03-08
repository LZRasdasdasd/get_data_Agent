"""
搜索所有集合中单原子催化剂合成相关的实验和结论信息
"""

import sys
sys.path.insert(0, '.')

from vector_tools import QdrantManager

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

**示例1:**
```json
{
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
"""


def search_catalyst_synthesis_in_all_collections():
    """在所有集合中搜索单原子催化剂合成信息"""
    manager = QdrantManager()
    
    # 获取所有集合
    collections = manager.list_collections()
    print(f"\n找到 {len(collections)} 个集合")
    
    # 查询关键词 - 针对单原子催化剂合成
    query = """单原子催化剂合成实验 experimental synthesis of single-atom catalysts 
    preparation method reaction conditions temperature time atmosphere 
    active site metal precursor precursor synthesis procedure
    实验部分 合成方法 制备步骤 反应条件 温度 时间 气氛 活性位点"""
    
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
