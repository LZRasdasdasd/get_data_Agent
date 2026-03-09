# PDF数据提取最小可执行方案 (MVP)

## 一、方案概述

本方案是 PDF 数据提取 Agent 的**最小可执行版本**，重点实现两个核心功能：

1. **存入数据**：将 PDF 文件内容存入 Qdrant 向量数据库
2. **提取数据**：根据表名（集合名）查询和提取数据

### 核心设计原则
- **一个PDF对应一个数据库表（集合）**：表名 = PDF文件名（不含扩展名）
- **结果可被发现**：通过 Qdrant Dashboard 可视化查看数据
- **简化架构**：去除复杂的 Agent 系统，直接使用脚本操作

---

## 二、技术架构

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   PDF 文件目录    │────▶│   Python 脚本    │────▶│  Qdrant 向量库   │
│  (10个PDF文件)    │     │  (ingest_pdfs)   │     │  (Docker部署)    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │   查询结果输出    │◀────│  Python 脚本    │
                         │  (控制台/文件)    │     │  (query_pdfs)   │
                         └──────────────────┘     └──────────────────┘
```

---

## 三、项目结构

```
pdf_qdrant_mvp/
├── README.md                  # 使用说明
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── docker-compose.yml         # Qdrant Docker 配置
│
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── pdf_tools.py           # PDF 处理工具
│   ├── vector_tools.py        # Qdrant 向量工具
│   ├── ingest_pdfs.py         # 存入数据脚本
│   └── query_pdfs.py          # 提取数据脚本
│
└── qdrant_storage/            # Qdrant 数据持久化目录（自动生成）
```

---

## 四、核心功能实现

### 4.1 存入数据流程

```
1. 扫描 PDF 目录下的所有文件
2. 对每个 PDF 文件：
   a. 提取文件名作为集合名（表名）
   b. 读取 PDF 文本内容
   c. 将文本分块（chunk_size=1000, overlap=200）
   d. 生成向量嵌入（使用 OpenAI embeddings）
   e. 存入对应的 Qdrant 集合
3. 输出存入结果统计
```

### 4.2 提取数据流程

```
1. 列出所有可用的集合（表）
2. 用户选择或指定集合名
3. 输入查询文本
4. 在指定集合中进行向量相似性搜索
5. 返回最相关的文本块
```

---

## 五、数据库表（集合）命名规则

| PDF 文件名 | 集合名（表名） |
|-----------|--------------|
| CO electroreduction on single-atom copper.pdf | `co_electroreduction_on_single_atom_copper` |
| High-Density Cobalt Single-Atom Catalysts....pdf | `high_density_cobalt_single_atom_catalysts` |
| ... | ... |

**命名转换规则**：
1. 移除 `.pdf` 扩展名
2. 转换为小写
3. 空格和特殊字符替换为下划线
4. 截断过长的名称（保留前 50 个字符）

---

## 六、快速开始

### 步骤 1：安装依赖

```bash
cd pdf_qdrant_mvp
pip install -r requirements.txt
```

### 步骤 2：启动 Qdrant

```bash
docker-compose up -d
```

### 步骤 3：配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 OpenAI API Key
```

### 步骤 4：存入 PDF 数据

```bash
python src/ingest_pdfs.py
```

### 步骤 5：查询数据

```bash
# 列出所有集合
python src/query_pdfs.py --list

# 在指定集合中查询
python src/query_pdfs.py --collection "co_electroreduction_on_single_atom_copper" --query "copper catalyst"

# 在所有集合中搜索
python src/query_pdfs.py --search-all --query "single atom catalyst"
```

---

## 七、数据验证

### 通过 Qdrant Dashboard 查看

访问 http://localhost:6333/dashboard 可以：
- 查看所有集合
- 浏览向量数据
- 执行测试查询

### 通过 API 查看

```bash
# 列出所有集合
curl http://localhost:6333/collections

# 查看特定集合信息
curl http://localhost:6333/collections/{collection_name}
```

---

## 八、预期输出示例

### 存入数据输出

```
========================================
PDF 数据存入开始
========================================
PDF 目录: E:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\paper
Qdrant 地址: http://localhost:6333

[1/10] 处理: CO electroreduction on single-atom copper.pdf
  - 集合名: co_electroreduction_on_single_atom_copper
  - 提取文本: 成功 (15 页, 23456 字符)
  - 分块数量: 28 个
  - 存入向量: 成功

[2/10] 处理: High-Density Cobalt Single-Atom Catalysts....pdf
  ...

========================================
存入完成统计
========================================
总文件数: 10
成功: 10
失败: 0
总向量数: 285
========================================
```

### 查询数据输出

```
========================================
查询: copper catalyst
集合: co_electroreduction_on_single_atom_copper
========================================

[结果 1] (相似度: 0.89)
来源: 第 3 页, 块 5
内容: Single-atom copper catalysts have shown remarkable 
selectivity for CO2 electroreduction to CO...

[结果 2] (相似度: 0.85)
来源: 第 5 页, 块 12
内容: The copper active sites demonstrated high turnover...

========================================
共找到 5 个相关结果
========================================
```

---

## 九、依赖说明

| 依赖包 | 用途 |
|-------|-----|
| qdrant-client | Qdrant 客户端 |
| openai | 向量嵌入生成 |
| pdfplumber | PDF 文本提取 |
| python-dotenv | 环境变量管理 |
| rich | 终端美化输出 |

---

## 十、扩展方向

此 MVP 可扩展为完整 Agent 系统：
1. 添加 LLM 进行智能数据提取
2. 添加表格识别和结构化
3. 添加数据验证模块
4. 添加 Excel 导出功能
