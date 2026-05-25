"""
Qdrant 连接诊断工具

用于快速检查 Qdrant 服务状态、Docker 容器状态和端口映射情况。
迁移项目或遇到连接问题时，优先运行此脚本进行自检。

用法:
    python src/check_qdrant.py
"""

import os
import sys
import subprocess
import socket
import requests
from pathlib import Path

# 尝试加载项目配置
try:
    from qdrant_config import config
    QDRANT_URL = config.qdrant_url
except Exception:
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


def check_docker_running() -> bool:
    """检查 Docker 是否正在运行"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("[OK] Docker 正在运行")
            return True
        else:
            print("[ERROR] Docker 未运行或无法连接")
            print("  -> 请启动 Docker Desktop")
            return False
    except FileNotFoundError:
        print("[ERROR] 未找到 docker 命令")
        print("  -> 请确保 Docker 已安装并添加到 PATH")
        return False
    except Exception as e:
        print(f"[ERROR] 检查 Docker 状态时出错: {e}")
        return False


def check_qdrant_containers():
    """检查运行中的 Qdrant 容器"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "ancestor=qdrant/qdrant", "--format", "{{.ID}}|{{.Names}}|{{.Ports}}|{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        
        if not lines:
            print("[WARNING] 未找到运行中的 Qdrant 容器")
            print("  -> 在项目目录执行: docker-compose up -d")
            return None
        
        print(f"[OK] 找到 {len(lines)} 个 Qdrant 容器:")
        containers = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 4:
                cid, name, ports, status = parts[0], parts[1], parts[2], parts[3]
                print(f"    - 名称: {name}")
                print(f"      ID: {cid}")
                print(f"      状态: {status}")
                print(f"      端口: {ports if ports else '(无端口映射!)'}")
                containers.append({"id": cid, "name": name, "ports": ports, "status": status})
        return containers
    except Exception as e:
        print(f"[ERROR] 检查容器时出错: {e}")
        return None


def check_port_open(host: str, port: int) -> bool:
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"[OK] 端口 {host}:{port} 已开放")
            return True
        else:
            print(f"[ERROR] 端口 {host}:{port} 未开放 (错误码: {result})")
            return False
    except Exception as e:
        print(f"[ERROR] 检查端口时出错: {e}")
        return False


def check_qdrant_api(url: str) -> bool:
    """尝试访问 Qdrant HTTP API"""
    try:
        response = requests.get(f"{url.rstrip('/')}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get("result", {}).get("version", "unknown")
            print(f"[OK] Qdrant API 响应正常 (版本: {version})")
            return True
        else:
            print(f"[ERROR] Qdrant API 返回异常状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] 无法连接到 Qdrant API: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 访问 Qdrant API 时出错: {e}")
        return False


def main():
    print("=" * 60)
    print("Qdrant 连接诊断工具")
    print("=" * 60)
    print(f"\n配置地址: {QDRANT_URL}\n")
    
    # 解析 URL
    parsed = requests.utils.urlparse(QDRANT_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6333
    
    checks = []
    
    # 1. 检查 Docker
    print("[1/4] 检查 Docker 状态...")
    checks.append(check_docker_running())
    print()
    
    # 2. 检查容器
    print("[2/4] 检查 Qdrant 容器...")
    containers = check_qdrant_containers()
    checks.append(containers is not None and len(containers) > 0)
    
    # 如果容器存在但无端口映射，给出警告
    if containers:
        for c in containers:
            if not c["ports"]:
                print("\n[WARNING] 发现容器端口未映射到宿主机!")
                print(f"  -> 容器 '{c['name']}' 没有端口映射")
                print("  -> 解决: docker stop {name} & docker rm {name}".format(name=c["name"]))
                print("  -> 然后: docker-compose up -d")
    print()
    
    # 3. 检查端口
    print(f"[3/4] 检查端口 {host}:{port}...")
    checks.append(check_port_open(host, port))
    print()
    
    # 4. 检查 API
    print("[4/4] 检查 Qdrant API...")
    checks.append(check_qdrant_api(QDRANT_URL))
    print()
    
    # 总结
    print("=" * 60)
    if all(checks):
        print("[诊断结果] 所有检查通过，Qdrant 连接正常!")
        print("=" * 60)
        return 0
    else:
        print("[诊断结果] 检测到问题，请根据上方提示修复")
        print("=" * 60)
        print("\n[常用修复命令]")
        print("  cd deepagents_GDatas/libs/cli/deepagents_cli/pdf_qdrant_mvp")
        print("  docker-compose up -d")
        print("\n[迁移项目后必做]")
        print("  1. 确保 Docker Desktop 已启动")
        print("  2. 在新项目目录下运行 docker-compose up -d")
        print("  3. 运行 python src/check_qdrant.py 验证")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
