# 数据提取脚本终端运行指南

本文档提供在Windows CMD终端中运行数据提取脚本的详细说明。

## 快速开始

### 方法1: 批量提取所有集合(推荐)

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_all_collections_dac.py
```

### 方法2: 单个集合提取

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_dac_synthesis.py
```

## 详细操作步骤

### 1. 打开CMD终端

按 `Win + R` 键，输入 `cmd`，然后按回车键。

### 2. 切换到项目目录

```cmd
e:
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
```

### 3. 检查Python环境

```cmd
python --version
```

确保Python版本为3.7或更高。

### 4. 检查脚本文件

```cmd
dir extract_all_collections_dac.py
dir extract_dac_synthesis.py
```

### 5. 运行批量提取脚本

```cmd
python extract_all_collections_dac.py
```

### 6. 查看提取进度

在另一个CMD终端中：

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\queried_datas
dir *.json /o-d
```

## 高级用法

### 查看脚本帮助信息

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_all_collections_dac.py --help
```

### 指定特定集合进行提取

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python -c "from extract_dac_synthesis import query_and_extract; query_and_extract('your_collection_name')"
```

### 将JSON数据转换为Excel格式

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_json_to_excel.py
```

## 监控和调试

### 统计已提取文件数量

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\queried_datas
dir *.json | find /c ".json"
```

### 查看最新提取的文件

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\queried_datas
dir *.json /o-d | more
```

### 保存运行日志

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_all_collections_dac.py > extraction_log.txt 2>&1
```

## 常见问题解决

### 编码问题

如果遇到中文编码问题：

```cmd
chcp 65001
```

### Python命令不可用

如果提示找不到python命令，尝试：

```cmd
python3 --version
py --version
where python
```

### 网络连接问题

确保网络连接正常，脚本需要连接：
- Qdrant数据库
- LLM API服务

### 依赖包缺失

如果提示缺少依赖包：

```cmd
pip install -r e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\requirements.txt
```

## 数据输出说明

### 输出目录

提取的数据保存在：
```
e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\queried_datas\
```

### 文件命名格式

每个提取的JSON文件按以下格式命名：
```
_<提取时间>_<集合名称>.json
```

例如: `_20260319_144804_guo_2020_catalytic_reduction_of_organic_and_hexava.json`

### 数据结构

每个JSON文件包含：

```json
{
  "metadata": {
    "collection_name": "集合名称",
    "query": "查询条件",
    "timestamp": "提取时间戳",
    "total_results": 查询结果数量
  },
  "query_results": [
    {
      "text": "查询到的文本内容",
      "score": 相似度评分,
      "chunk_index": 块索引
    }
  ],
  "extracted_info": {
    "is_related": "是否相关",
    "synthesis_methods": [
      {
        "method_type": "方法类型",
        "steps": "详细步骤",
        "temperature": "温度",
        "time": "时间",
        "atmosphere": "气氛",
        "precursors": "前驱体"
      }
    ],
    "active_site": "活性位点",
    "metal_atomic_distance": "金属原子间距"
  },
  "raw_response": "LLM完整响应"
}
```

## 性能和运行时间

### 预期处理时间

- 单个集合: 30-60秒
- 全部集合: 根据数量可能需要数小时

### 资源使用

- CPU: 单核100%(LLM调用时)
- 内存: ~500MB
- 网络: 需要稳定连接

## 后续处理

### 数据验证

提取完成后，可以检查数据质量：

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\queried_datas
python -c "import json; data = json.load(open('your_file.json')); print(data['extracted_info'])"
```

### Excel转换

将JSON数据转换为Excel格式便于分析：

```cmd
cd e:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src
python extract_json_to_excel.py
```

## 注意事项

1. **环境要求**: 确保Python 3.7+已正确安装
2. **网络连接**: 运行期间保持网络连接稳定
3. **磁盘空间**: 确保有足够的磁盘空间存储提取的数据
4. **运行时间**: 脚本可能需要较长时间，建议在空闲时运行
5. **数据备份**: 提取前建议备份重要数据

## 技术支持

如遇到问题，请检查：
1. Python环境是否正确配置
2. 依赖包是否完整安装
3. 网络连接是否正常
4. 配置文件是否正确设置

## 脚本列表

### 主要脚本

- `extract_all_collections_dac.py` - 批量提取所有集合
- `extract_dac_synthesis.py` - 单个集合提取
- `extract_json_to_excel.py` - JSON转Excel工具

### 辅助脚本

- `vector_tools.py` - Qdrant数据库管理
- `qdrant_config.py` - 配置文件
- `test_connection.py` - 连接测试工具

---

**最后更新**: 2026-03-19  
**版本**: 1.0  
**维护者**: Data Extraction Team