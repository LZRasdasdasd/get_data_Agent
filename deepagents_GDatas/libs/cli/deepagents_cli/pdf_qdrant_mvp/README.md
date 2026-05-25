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

## Qdrant 连接与迁移指南

### 为什么迁移项目后会连接失败？
每次迁移项目或更换工作目录时，可能会遇到 `[WinError 10061] 由于目标计算机积极拒绝，无法连接` 的错误。常见原因：

1. **Docker 容器未启动**：迁移后未在新目录运行 `docker-compose up -d`
2. **端口未映射**：旧容器可能在没有 `-p 6333:6333` 参数的情况下启动，导致宿主机无法访问
3. **Docker Desktop 未运行**：Windows 上 Docker 需要 Docker Desktop 支持

### 迁移项目后的标准操作流程

```bash
# 1. 进入项目目录
cd deepagents_GDatas/libs/cli/deepagents_cli/pdf_qdrant_mvp

# 2. 检查 Docker 状态
docker info

# 3. 停止旧容器（如果有）
docker stop pdf-qdrant-mvp
docker rm pdf-qdrant-mvp

# 4. 重新启动 Qdrant
docker-compose up -d

# 5. 验证连接
python src/check_qdrant.py
```

### 连接诊断工具

项目内置了诊断脚本，运行后会自动检查 Docker、容器、端口和 API：

```bash
python src/check_qdrant.py
```

输出示例：
```
[1/4] 检查 Docker 状态...
[OK] Docker 正在运行

[2/4] 检查 Qdrant 容器...
[OK] 找到 1 个 Qdrant 容器: ...

[3/4] 检查端口 127.0.0.1:6333...
[OK] 端口 127.0.0.1:6333 已开放

[4/4] 检查 Qdrant API...
[OK] Qdrant API 响应正常
```

### 常见问题速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `Connection refused` / `10061` | Qdrant 容器未运行或未映射端口 | `docker-compose up -d` |
| `PORTS` 列为空 | 容器未做端口映射 | 删除旧容器后重新 `docker-compose up -d` |
| `docker info` 报错 | Docker Desktop 未启动 | 启动 Docker Desktop |
| 连接远程 Qdrant | 配置错误 | 修改 `.env` 中 `QDRANT_URL` |

### Docker 数据持久化

[`docker-compose.yml`](docker-compose.yml) 已配置卷映射，将容器内数据持久化到 `./qdrant_storage`：

```yaml
volumes:
  - ./qdrant_storage:/qdrant/storage
```

这样即使删除并重建容器，向量数据也不会丢失。

### 更换 Qdrant 容器/地址

如果需要连接到不同的 Qdrant 实例（例如远程服务器或其他 Docker 容器）：

1. **修改 `.env` 文件**：
   ```env
   QDRANT_URL=http://<新IP>:<新端口>
   ```

2. **验证新地址可访问**：
   ```bash
   curl http://<新IP>:<新端口>
   ```

3. **重新运行脚本**：
   ```bash
   python src/ingest_markdown.py --md-dir markdown_output
   ```

> **注意**：若切换到远程 Qdrant，需确保网络可达且防火墙放行了对应端口。
