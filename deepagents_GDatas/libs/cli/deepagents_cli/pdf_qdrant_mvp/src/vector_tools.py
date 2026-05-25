"""
Qdrant 向量数据库工具模块

提供与 Qdrant 的连接、集合管理和和向量操作
"""

import uuid
import sys
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI

from qdrant_config import config


def _print_connection_help(qdrant_url: str, error_msg: str):
    """打印连接失败的诊断帮助信息"""
    print("\n" + "=" * 60)
    print("[Qdrant 连接失败 - 诊断与解决方案]")
    print("=" * 60)
    print(f"\n目标地址: {qdrant_url}")
    print(f"错误信息: {error_msg}")
    
    if "Connection refused" in error_msg or "10061" in error_msg or "积极拒绝" in error_msg:
        print("\n[可能原因 1] Qdrant Docker 容器未运行或未映射端口")
        print("  -> 解决步骤:")
        print("     1. 确保 Docker Desktop 已启动")
        print("     2. 在项目目录执行: docker-compose up -d")
        print("     3. 验证容器状态: docker ps")
        print("     4. 确认 PORTS 列显示: 0.0.0.0:6333->6333/tcp")
        print("\n[可能原因 2] 使用了旧容器，端口未映射到宿主机")
        print("  -> 解决步骤:")
        print("     1. 查看所有容器: docker ps -a")
        print("     2. 停止旧容器: docker stop <容器名>")
        print("     3. 删除旧容器: docker rm <容器名>")
        print("     4. 重新启动: docker-compose up -d")
        print("\n[可能原因 3] Qdrant 服务地址配置错误")
        print("  -> 解决步骤:")
        print("     1. 检查 .env 文件中的 QDRANT_URL")
        print("     2. 若使用本地 Docker，应为 http://localhost:6333")
        print("     3. 若使用远程服务器，填写对应 IP 和端口")
    
    print("\n[快速检查命令]")
    print("  docker ps                    # 查看运行中的容器")
    print("  docker port <容器名>          # 检查端口映射")
    print("  curl http://localhost:6333   # 测试服务是否响应")
    print("=" * 60 + "\n")


class QdrantManager:
    """Qdrant 管理器"""
    
    def __init__(self):
        """初始化 Qdrant HTTP客户端"""
        self.base_url = config.qdrant_url.rstrip('/')
        self.timeout = 30
        
        # 测试连接
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            if response.status_code == 200:
                print(f"[OK] Qdrant 连接成功: {self.base_url}")
            else:
                raise Exception(f"状态码: {response.status_code}")
        except Exception as e:
            error_str = str(e)
            _print_connection_help(self.base_url, error_str)
            raise ConnectionError(f"无法连接到 Qdrant ({self.base_url}): {error_str}")
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """内部方法: 发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
    
    def create_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        创建 Qdrant 集合（表)
        
        Args:
            collection_name: 集合名称(对应 PDF 文件名)
            
        Returns:
            dict: 创建结果
        """
        try:
            # 检查集合是否存在
            collections_response = self._make_request("GET", "/collections")
            existing = [c['name'] for c in collections_response['result']['collections']]
            
            if collection_name in existing:
                return {
                    "status": "exists",
                    "collection_name": collection_name,
                    "message": f"集合 {collection_name} 已存在"
                }
            
            # 创建新集合
            payload = {
                "vectors": {
                    "size": config.embedding_dimension,
                    "distance": "Cosine"
                }
            }
            self._make_request("PUT", f"/collections/{collection_name}", payload)
            
            return {
                "status": "created",
                "collection_name": collection_name,
                "message": f"成功创建集合 {collection_name}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"创建集合失败: {e}"
            }
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        删除 Qdrant 集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            dict: 删除结果
        """
        try:
            self._make_request("DELETE", f"/collections/{collection_name}")
            return {
                "status": "deleted",
                "collection_name": collection_name,
                "message": f"成功删除集合 {collection_name}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"删除集合失败: {e}"
            }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        列出所有集合
        
        Returns:
            list: 集合列表
        """
        try:
            response = self._make_request("GET", "/collections")
            collections = []
            for col in response['result']['collections']:
                # 获取每个集合的详细信息
                try:
                    info_response = self._make_request("GET", f"/collections/{col['name']}")
                    info = info_response['result']
                    collections.append({
                        "name": col['name'],
                        "vector_count": info.get('points_count', 0),
                        "indexed_vector_count": info.get('indexed_vector_count', 0),
                        "segments_count": info.get('segments_count', 0),
                        "status": info.get('status', 'Unknown')
                    })
                except:
                    # 如果获取详细信息失败,至少返回基本信息
                    collections.append({
                        "name": col['name'],
                        "vector_count": 0,
                        "indexed_vector_count": 0,
                        "segments_count": 0,
                        "status": "Unknown"
                    })
            return collections
        except Exception as e:
            print(f"列出集合失败: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合详细信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            dict: 集合信息
        """
        try:
            response = self._make_request("GET", f"/collections/{collection_name}")
            return response['result']
        except Exception as e:
            return {
                "error": str(e),
                "collection_name": collection_name
            }
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        使用OpenAI生成文本的向量嵌入
        
        Args:
            text: 要向量化的文本
            
        Returns:
            list: 向量嵌入 (1024维)
        """
        try:
            # 创建 OpenAI 客户端，配置 base_url 和超时参数
            client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_api_base,
                timeout=60.0,  # 设置超时时间为 60 秒
                max_retries=2  # 失败后重试 2 次
            )
            
            response = client.embeddings.create(
                model=config.embedding_model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            print(f"生成嵌入失败: {e}")
            raise
    
    def add_points(
        self,
        collection_name: str,
        texts: Optional[List[str]] = None,
        points: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        批量添加文本向量点
        
        Args:
            collection_name: 集合名称
            texts: 文本列表(用于生成嵌入)
            points: 直接的点列表(用于兼容旧版本)
            batch_size: 批量大小
            metadatas: 元数据列表(可选)
            
        Returns:
            dict: 添加结果
        """
        try:
            # 确保提供了texts或points
            if not texts and not points:
                return {
                    "status": "error",
                    "error": "没有文本需要添加"
                }
            
            # 如果提供了points,需要转换为 Qdrant 格式(兼容模式)
            if points:
                # points 是来自 chunk_markdown 的字典列表,需要转换为 Qdrant point 格式
                texts_to_process = [p["text"] for p in points if "text" in p]
                existing_points = None
            else:
                texts_to_process = texts
                existing_points = None
            
            # 确保集合存在
            create_result = self.create_collection(collection_name)
            if create_result["status"] == "error" and "exists" not in create_result["status"]:
                return create_result
            
            # 如果需要,生成嵌入
            if texts_to_process:
                print(f"[INFO] 正在生成 {len(texts_to_process)} 个向量嵌入...")
                
                existing_points = []
                for i, text in enumerate(texts_to_process, start=1):
                    if i % 10 == 0:
                        print(f"[INFO] 进度: {i}/{len(texts_to_process)}")
                    
                    try:
                        embedding = self.generate_embedding(text)
                        print(f"[INFO] 已生成嵌入: {len(embedding)}维")
                    except Exception as e:
                        print(f"[ERROR] 生成嵌入失败: {e}")
                        raise
                    
                    point = {
                        "id": str(uuid.uuid4()),
                        "vector": embedding,
                        "payload": {
                            "text": text,
                            "index": i
                        }
                    }
                    
                    # 如果是通过 points 参数传入的,复制原始 chunk 的其他字段
                    if points and "text" in points[i-1]:
                        # 复制 chunk 的其他字段到 payload
                        for key, value in points[i-1].items():
                            if key not in ["text"]:
                                point["payload"][key] = value
                    
                    # 添加外部提供的元数据
                    if metadatas and i <= len(metadatas):
                        point["payload"].update(metadatas[i-1])
                    
                    existing_points.append(point)
            
            print(f"[INFO] 正在上传 {len(existing_points)} 个向量到Qdrant...")
            
            # 分批上传
            total_uploaded = 0
            
            for i in range(0, len(existing_points), batch_size):
                batch = existing_points[i:i+batch_size]
                payload = {"points": batch}
                
                self._make_request("PUT", f"/collections/{collection_name}/points", payload)
                total_uploaded += len(batch)
                print(f"[INFO] 已上传: {total_uploaded}/{len(existing_points)}")
            
            return {
                "status": "success",
                "total_points": len(points),
                "uploaded": total_uploaded,
                "collection_name": collection_name,
                "message": f"成功上传 {total_uploaded} 个向量到集合 {collection_name}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"添加向量失败: {e}"
            }
    
    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        在集合中搜索相似向量
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            list: 搜索结果
        """
        try:
            # 生成查询嵌入
            query_embedding = self.generate_embedding(query)
            
            # 搜索
            payload = {
                "vector": query_embedding,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True
            }
            
            response = self._make_request("POST", f"/collections/{collection_name}/points/search", payload)
            
            results = []
            for result in response['result']:
                results.append({
                    "id": result['id'],
                    "score": result['score'],
                    "payload": result['payload']
                })
            
            return results
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def ingest_pdf(
        self,
        pdf_path: str,
        collection_name: Optional[str] = None,
        chunk_size: int = 500
    ) -> Dict[str, Any]:
        """
        从PDF文件提取并存储向量
        
        Args:
            pdf_path: PDF文件路径
            collection_name: 集合名称(默认使用文件名)
            chunk_size: 分块大小
            
        Returns:
            dict: 导入结果
        """
        try:
            import fitz
            
            # 使用文件名作为集合名
            if collection_name is None:
                collection_name = pdf_path.split('/')[-1].replace('.pdf', '')
            
            # 提取文本
            doc = fitz.open(pdf_path)
            text_chunks = []
            
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_chunks.append(text)
            
            doc.close()
            
            # 分块并上传
            if not text_chunks:
                return {
                    "status": "error",
                    "message": "PDF文件中没有提取到文本"
                }
            
            # 合并所有文本
            full_text = "\n\n".join(text_chunks)
            
            # 简单分块
            chunks = []
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i+chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            
            print(f"[INFO] 从 {pdf_path} 提取了 {len(chunks)} 个文本块")
            
            # 上传到Qdrant
            result = self.add_points(collection_name, chunks)
            
            return {
                "status": "success" if result["status"] == "success" else "error",
                "pdf_path": pdf_path,
                "collection_name": collection_name,
                "chunk_count": len(chunks),
                "uploaded": result.get("uploaded", 0),
                "message": result.get("message", "")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"导入PDF失败: {e}"
            }
    
    def ingest_all_pdfs(
        self,
        pdf_dir: str = "./pdfs",
        **kwargs
    ) -> Dict[str, Any]:
        """
        批量导入PDF文件到向量数据库
        
        Args:
            pdf_dir: PDF文件目录
            **kwargs: 其他参数
            
        Returns:
            dict: 批量导入结果
        """
        import os
        from pathlib import Path
        
        try:
            pdf_dir = Path(pdf_dir)
            if not pdf_dir.exists():
                return {
                    "status": "error",
                    "message": f"目录不存在: {pdf_dir}"
                }
            
            pdf_files = sorted(pdf_dir.glob("*.pdf"))
            print(f"[INFO] 找到 {len(pdf_files)} 个PDF文件")
            
            if not pdf_files:
                return {
                    "status": "error",
                    "message": "没有找到PDF文件"
                }
            
            results = []
            successful = 0
            failed = 0
            
            for pdf_file in pdf_files:
                print(f"\n正在处理: {pdf_file.name}")
                result = self.ingest_pdf(str(pdf_file), **kwargs)
                results.append(result)
                
                if result["status"] == "success":
                    successful += 1
                else:
                    failed += 1
            
            return {
                "status": "success",
                "total": len(pdf_files),
                "successful": successful,
                "failed": failed,
                "results": results,
                "message": f"完成导入: {successful} 成功, {failed} 失败"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"批量导入失败: {e}"
            }
