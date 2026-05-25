# Qdrant 连接问题解决方案

> 本文档针对迁移项目、更换 Docker 容器或初次部署时出现的 Qdrant 连接失败问题，提供系统性的分析与解决步骤。

---

## 一、问题现象

运行 `ingest_markdown.py` 或任何需要连接 Qdrant 的脚本时，出现如下错误：

```
[ERROR] Qdrant 连接失败: HTTPConnectionPool(host='127.0.0.1', port=6333): 
Max retries exceeded with url: / (Caused by NewConnectionError(...
[WinError 10061] 由于目标计算机积极拒绝，无法连接。))
```

核心信息：
- **错误码**：`10061` / `Connection refused`
- **含义**：Python 尝试连接 `127.0.0.1:6333`，但该端口上没有服务在监听

---

## 二、根本原因分析

### 原因 1：Qdrant Docker 容器根本没有启动（最常见）

迁移项目到新目录后，原来目录下通过 `docker-compose up -d` 启动的容器并不会自动跟随到新位置。如果在新目录没有重新启动，宿主机 6333 端口就没有服务。

### 原因 2：容器已启动，但端口未映射到宿主机

某些情况下，用户可能使用 `docker run qdrant/qdrant` 直接启动容器，却忘记了添加端口映射参数 `-p 6333:6333`。此时容器内部 Qdrant 确实在运行，但宿主机无法从外部访问。

**如何识别**：运行 `docker ps`，查看 `PORTS` 列：

| 情况 | PORTS 列显示 | 说明 |
|------|-------------|------|
| ✅ 正常 | `0.0.0.0:6333->6333/tcp` | 端口已映射，可访问 |
| ❌ 异常 | `6333/tcp` 或空白 | 端口未映射，不可访问 |

### 原因 3：Docker Desktop 未运行

Windows 11 环境下，Docker 服务依赖 Docker Desktop。如果 Docker Desktop 没有启动，`docker` 命令虽然存在，但无法创建或管理容器。

### 原因 4：Qdrant URL 配置错误

如果 `.env` 文件中的 `QDRANT_URL` 配置为远程地址或其他端口，而实际服务在本地，则会出现连接失败。

---

## 三、标准修复流程（按步骤执行）

### Step 1：确认 Docker Desktop 已启动

在 CMD 或 PowerShell 中执行：

```cmd
docker info
```

- 若返回大量系统信息 → Docker 正常
- 若报错 `error during connect` 或 `Docker Desktop is not running` → **启动 Docker Desktop**

### Step 2：检查现有 Qdrant 容器

```cmd
docker ps -a
```

查看是否有 Qdrant 容器：

- **如果有，但 PORTS 列为空**：该容器端口未映射，需要删除重建
- **如果有，且状态为 Up**：进入 Step 4 验证端口
- **如果没有**：进入 Step 3 重新启动

### Step 3：删除旧容器并重新启动

**在项目根目录下**（即 `docker-compose.yml` 所在目录）执行：

```cmd
cd deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp

:: 停止并删除可能冲突的旧容器
docker stop pdf-qdrant-mvp
docker rm pdf-qdrant-mvp

:: 使用 docker-compose 启动（已包含端口映射配置）
docker-compose up -d
```

> **为什么必须在项目目录执行？**  
> 因为 `docker-compose.yml` 定义了端口映射 `6333:6333` 和数据卷 `./qdrant_storage:/qdrant/storage`，在其他目录执行会使用默认配置或找不到文件。

### Step 4：验证端口映射

```cmd
docker ps
```

确认输出中包含：

```
PORTS: 0.0.0.0:6333-6334->6333-6334/tcp, [::]:6333-6334->6333-6334/tcp
```

### Step 5：运行诊断脚本

```cmd
python src/check_qdrant.py
```

该脚本会自动完成以下检查：
1. Docker 是否运行
2. Qdrant 容器是否存在且端口已映射
3. 本地端口 6333 是否开放
4. Qdrant HTTP API 是否响应

如果全部通过，会显示：

```
[诊断结果] 所有检查通过，Qdrant 连接正常!
```

### Step 6：重新运行数据存入脚本

```cmd
python src/ingest_markdown.py --md-dir markdown_output
```

---

## 四、迁移项目的完整 checklist

每次将项目复制到新电脑、新目录或重装系统后，按此清单操作：

- [ ] 安装 Docker Desktop 并启动
- [ ] 进入 `pdf_qdrant_mvp` 目录
- [ ] 执行 `docker-compose up -d` 启动 Qdrant
- [ ] 执行 `python src/check_qdrant.py` 验证连接
- [ ] 确认 `.env` 文件存在且配置正确（特别是 `QDRANT_URL`）
- [ ] 运行业务脚本（如 `ingest_markdown.py`）

---

## 五、更换 Qdrant 容器/地址的详细步骤

如果你不想使用本地 Docker，而要连接到其他 Qdrant 实例（如远程服务器、云端 Qdrant、或其他 Docker 容器），按以下步骤操作：

### 场景 A：连接到同一台机器上的另一个 Docker 容器

1. 查看目标容器的端口映射：
   ```cmd
   docker port <容器名>
   ```

2. 若目标容器映射到不同端口（如 `6335`），修改 `.env`：
   ```env
   QDRANT_URL=http://localhost:6335
   ```

### 场景 B：连接到局域网/远程服务器的 Qdrant

1. 修改 `.env` 中的 `QDRANT_URL`：
   ```env
   QDRANT_URL=http://192.168.1.100:6333
   ```

2. 确保远程服务器防火墙放行了 6333 端口

3. 在本地测试连通性：
   ```cmd
   curl http://192.168.1.100:6333
   ```

4. 通过验证后再运行 Python 脚本

### 场景 C：完全更换为新的 Docker Compose 环境

1. 备份原数据（可选）：
   ```cmd
   xcopy /E /I qdrant_storage qdrant_storage_backup
   ```

2. 停止并删除旧容器：
   ```cmd
   docker stop pdf-qdrant-mvp
   docker rm pdf-qdrant-mvp
   ```

3. 在新目录启动：
   ```cmd
   cd <新项目路径>\pdf_qdrant_mvp
   docker-compose up -d
   ```

4. 如果之前备份了数据，将 `qdrant_storage_backup` 复制回新项目目录的 `qdrant_storage`，然后重启容器：
   ```cmd
   docker-compose restart
   ```

---

## 六、数据持久化说明

当前 [`docker-compose.yml`](docker-compose.yml) 已配置数据卷：

```yaml
volumes:
  - ./qdrant_storage:/qdrant/storage
```

这意味着：
- 向量数据、集合定义、索引等都保存在 `./qdrant_storage` 目录
- 删除容器不会丢失数据，只要 `qdrant_storage` 文件夹还在
- 迁移项目时，**务必将 `qdrant_storage` 文件夹一并复制**，否则数据需要重新导入

---

## 七、常用调试命令汇总

| 命令 | 用途 |
|------|------|
| `docker ps` | 查看运行中的容器及其端口映射 |
| `docker ps -a` | 查看所有容器（含已停止） |
| `docker port <容器名>` | 检查容器的端口映射详情 |
| `docker logs pdf-qdrant-mvp` | 查看 Qdrant 容器日志 |
| `docker-compose up -d` | 启动 Qdrant 服务 |
| `docker-compose down` | 停止并移除 Qdrant 服务 |
| `docker-compose restart` | 重启 Qdrant 服务 |
| `python src/check_qdrant.py` | 一键诊断连接状态 |
| `curl http://localhost:6333` | 直接测试 HTTP API |

---

## 八、代码层面的改进

为帮助用户更快地定位问题，代码已做以下增强：

### 1. `vector_tools.py` 连接失败时打印诊断信息

当 [`QdrantManager.__init__`](src/vector_tools.py:18) 检测到连接被拒绝时，会自动调用 `_print_connection_help()`，输出：
- 目标地址
- 可能原因（容器未运行 / 端口未映射 / 配置错误）
- 对应的解决步骤
- 常用检查命令

### 2. 新增 `check_qdrant.py` 诊断脚本

[`src/check_qdrant.py`](src/check_qdrant.py) 是一个独立的诊断工具，无需运行主业务逻辑即可验证环境。

---

## 九、总结

| 问题场景 | 关键动作 |
|---------|---------|
| 迁移项目后连接失败 | 新目录执行 `docker-compose up -d` |
| 端口未映射 | 删除旧容器，用 docker-compose 重建 |
| Docker 没启动 | 启动 Docker Desktop |
| 更换 Qdrant 地址 | 修改 `.env` 中的 `QDRANT_URL` |
| 不确定哪里出错 | 运行 `python src/check_qdrant.py` |

按照本文档的 **Step 1~6** 逐步排查，99% 的 Qdrant 连接问题都可以解决。
