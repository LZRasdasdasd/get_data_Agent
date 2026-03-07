# PDF Qdrant MVP

# 最小可执行版本 - PDF 数据存入与查询

这是一个基于 Qdrant 向量数据库的最小可执行方案，用于将 PDF 文件内容存入向量数据库并进行语义搜索。

## 功能特性

- **一个 PDF 对应一个集合（表）**: 每个 PDF 文件存入独立的 Qdrant 集合
- **表名即文件名**: 集合名称由 PDF 文件名自动生成
- **语义搜索**: 使用 OpenAI Embeddings 进行向量相似性搜索
- **结果可发现**: 可通过 Qdrant Dashboard 可视化查看数据

## 目录结构

```
pdf_qdrant_mvp/
├── README.md                  # 本文件
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── docker-compose.yml         # Qdrant Docker 配置
├── MVP_PLAN.md               # 详细方案说明
├── src/
│   ├── config.py              # 配置管理
│   ├── pdf_tools.py           # PDF 处理工具
│   ├── vector_tools.py        # Qdrant 向量工具
│   ├── ingest_pdfs.py         # 存入数据脚本
│   └── query_pdfs.py          # 查询数据脚本
```

## 快速开始

### 1. 安装依赖
```bash
cd pdf_qdrant_mvp
pip install -r requirements.txt
```

### 2. 启动 Qdrant
```bash
docker-compose up -d
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件，填入 OpenAI API Key
notepad .env
```

### 4. 存入 PDF 数据
```bash
# 使用默认 PDF 目录
python src/ingest_pdfs.py

# 或指定自定义目录
python src/ingest_pdfs.py --pdf-dir "E:\path\to\your\pdfs"
```

### 5. 查询数据
```bash
# 列出所有集合
python src/query_pdfs.py --list

# 在指定集合中查询
python src/query_pdfs.py --collection co_electroreduction_on_single_atom_copper --query "copper catalyst"

```

### 6. 访问 Qdrant Dashboard
打开浏览器访问: http://localhost:6333/dashboard

## PDF 文件位置

默认 PDF 目录: `E:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\paper`

包含的论文文件:
1. CO electroreduction on single-atom copper.pdf
2. High-Density Cobalt Single-Atom Catalysts for Enhanced Oxygen Evolution Reaction.pdf
3. ... (共 10 个 PDF 文件)

## 集合命名规则
PDF 文件名转换为集合名称的规则:
1. 移除 `.pdf` 扩展名
2. 转换为小写
3. 空格和特殊字符替换为下划线
4. 截断到 50 个字符

示例:
- `CO electroreduction on single-atom copper.pdf` → `co_electroreduction_on_single_atom_copper`
- `High-Density Cobalt Single-Atom Catalysts....pdf` → `high_density_cobalt_single_atom_catalysts`

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| OPENAI_API_KEY | OpenAI API 密钥 | (必填) |
| QDRANT_URL | Qdrant 服务地址 | http://localhost:6333 |
| PDF_DIR | PDF 文件目录 | (见 .env.example) |
| CHUNK_SIZE | 文本块大小 | 1000 |
| CHUNK_OVERLAP | 块之间重叠 | 200 |
| EMBEDDING_MODEL | 嵌入模型 | text-embedding-3-small |

## 常用命令

```bash
# 存入数据
python src/ingest_pdfs.py -d <PDF目录> -s <块大小> -o <重叠大小>

# 查询数据
python src/query_pdfs.py -l                    # 列出集合
python src/query_pdfs.py -c <集合名> -q <查询>  # 查询
python src/query_pdfs.py -c <集合名>          # 交互式查询

# Docker 命令
docker-compose up -d       # 启动 Qdrant
docker-compose down         # 停止 Qdrant
docker-compose logs -f     # 查看日志
```

## 注意事项
- 需要先启动 Qdrant 服务再存入数据
- 需要配置 OpenAI API Key
- PDF 文件名会自动转换为集合名称
- 可通过 Qdrant Dashboard 查看和管理数据
