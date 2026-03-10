"""
Qdrant 向量数据库工具模块

提供与 Qdrant 的连接、集合管理和和向量操作
"""

import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI

from qdrant_config import config


class QdrantManager:
    """Qdrant 管理器"""
    
    def __init__(self):
        """初始化 Qdrant 客户端"""
        self.client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key if config.qdrant_api_key else None
        )
        
        # 测试连接
        try:
            self.client.get_collections()
            print(f"[OK] Qdrant 连接成功: {config.qdrant_url}")
        except Exception as e:
            print(f"[ERROR] Qdrant 连接失败: {e}")
            raise
    
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
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name in existing:
                return {
                    "status": "exists",
                    "collection_name": collection_name,
                    "message": f"集合 {collection_name} 已存在"
                }
            
            # 创建新集合
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
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
            self.client.delete_collection(collection_name=collection_name)
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
            list: 集合信息列表
        """
        try:
            collections = self.client.get_collections()
            result = []
            for col in collections.collections:
                # 需要调用 get_collection 获取 points_count
                try:
                    info = self.client.get_collection(collection_name=col.name)
                    points_count = info.points_count
                    status = info.status.value if hasattr(info.status, 'value') else "active"
                except:
                    points_count = 0
                    status = "unknown"
                
                result.append({
                    "name": col.name,
                    "points_count": points_count,
                    "status": status
                })
            return result
        except Exception as e:
            print(f"[Error] 获取集合列表失败: {e}")
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
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "status": "success",
                "collection_name": collection_name,
                "points_count": info.points_count,
                "vector_size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 0,
                "status": info.status.value if hasattr(info.status, 'value') else "unknown"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"获取集合信息失败: {e}"
            }
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        使用 OpenAI 生成文本的向量嵌入
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            list: 向量嵌入列表
        """
        try:
            client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_api_base
            )
            
            response = client.embeddings.create(
                model=config.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"[Error] 生成嵌入失败: {e}")
            raise
    
    def add_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        批量添加向量点到 Qdrant 集合
        
        Args:
            collection_name: 集合名称
            points: 点数据列表
            batch_size: 批量大小（每批处理的块数，用于控制 API 调用频率）
            
        Returns:
            dict: 操作结果
        """
        try:
            total_points_added = 0
            
            # 分批处理所有点
            for batch_start in range(0, len(points), batch_size):
                batch_end = min(batch_start + batch_size, len(points))
                batch = points[batch_start:batch_end]
                
                # 为当前批次准备 PointStruct 对象
                qdrant_points = []
                for chunk in batch:
                    # 生成唯一ID
                    point_id = str(uuid.uuid4())
                    
                    # 生成嵌入
                    embedding = self.generate_embedding(chunk["text"])
                    
                    qdrant_points.append(PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            "chunk_index": chunk.get("chunk_index", 0),
                            "source_file": chunk.get("source_file", ""),
                            "page_num": chunk.get("page_num", 0),
                        }
                    ))
                
                # 批量插入当前批次
                if qdrant_points:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=qdrant_points
                    )
                    total_points_added += len(qdrant_points)
                    print(f"  [批量 {batch_start//batch_size + 1}] 已添加 {len(qdrant_points)} 个向量点")
            
            return {
                "status": "success",
                "collection_name": collection_name,
                "points_added": total_points_added,
                "message": f"成功添加 {total_points_added} 个向量点到集合 {collection_name}"
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
        query_text: str,
        n_results: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        在 Qdrant 向量数据库中执行语义搜索，查找与查询文本最相似的内容。
        
        该工具使用 OpenAI Embeddings 将查询文本转换为向量，然后在指定的 Qdrant 集合中
        执行相似度搜索，返回与查询语义最相关的文本块。适用于从已索引的科学论文中
        检索相关信息。
        
        Use this tool when you need to:
        - Search for relevant content in indexed PDF documents
        - Find semantically similar text passages in scientific papers
        - Retrieve context for catalyst synthesis information
        - Query the vector database for specific research topics
        
        Args:
            collection_name: Qdrant 集合名称，通常是 PDF 文件名的小写下划线形式
            query_text: 搜索查询文本，支持自然语言描述和关键词
            n_results: 返回的最大结果数量，默认 5
            score_threshold: 相似度阈值（0-1），低于此值的结果会被过滤，默认 0.7
            
        Returns:
            list: 搜索结果列表，每个元素是包含以下字段的字典：
                - text (str): 匹配的文本内容
                - score (float): 相似度分数（0-1，越高越相似）
                - chunk_index (int): 文本块在原文中的索引
                - source_file (str): 来源文件名
                - page_num (int): 页码
        
        Example:
            >>> manager = QdrantManager()
            >>> results = manager.search("paper_collection", "催化剂合成方法", n_results=10)
            >>> for r in results:
            ...     print(f"Score: {r['score']:.2f}, Text: {r['text'][:100]}...")
        """
        try:
            # 生成查询向量
            query_embedding = self.generate_embedding(query_text)
            
            # 执行搜索 - 使用 query_points 方法（新版 qdrant-client API）
            search_results = self.client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                limit=n_results,
                score_threshold=score_threshold
            )
            
            # 格式化结果
            results = []
            for result in search_results.points:
                results.append({
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "chunk_index": result.payload.get("chunk_index", -1),
                    "source_file": result.payload.get("source_file", ""),
                    "page_num": result.payload.get("page_num", 0),
                })
            
            return results
            
        except Exception as e:
            print(f"[Error] 搜索失败: {e}")
            return []
    
    def ingest_pdf(
        self,
        pdf_path: str,
        collection_name: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        将单个 PDF 文件存入 Qdrant
        
        Args:
            pdf_path: PDF 文件路径
            collection_name: 集合名称
            chunk_size: 文本块大小
            chunk_overlap: 块之间的重叠
            
        Returns:
            dict: 存入结果
        """
        from .pdf_tools import extract_text_from_pdf, chunk_text
        
        # 使用配置中的默认值
        if chunk_size is None:
            chunk_size = config.chunk_size
        if chunk_overlap is None:
            chunk_overlap = config.chunk_overlap
        
        # 提取 PDF 文本
        print(f"  正在读取 PDF: {pdf_path}")
        pdf_result = extract_text_from_pdf(pdf_path)
        
        if not pdf_result["success"]:
            return {
                "status": "error",
                "error": pdf_result.get("error", "读取 PDF 失败"),
                "message": "无法读取 PDF 内容"
            }
        
        # 获取文本
        text = pdf_result["text"]
        print(f"  提取到 {len(text)} 个字符, 分成 {pdf_result['pages']} 页")
        
        # 分块
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        print(f"  分块完成: {len(chunks)} 个文本块")
        
        # 准备点数据
        points = []
        for chunk in chunks:
            points.append({
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
                "source_file": Path(pdf_path).name,
                "page_num": 0,
            })
        
        # 存入向量
        result = self.add_points(
            collection_name=collection_name,
            points=points,
            batch_size=10
        )
        
        return {
            "status": "success",
            "collection_name": collection_name,
            "chunks_count": len(chunks),
            "points_added": result.get("points_added", 0),
            "message": f"成功将 {len(chunks)} 个块存入集合 {collection_name}"
        }
    
    def ingest_all_pdfs(
        self,
        pdf_dir: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        将目录下所有 PDF 文件存入 Qdrant
        
        Args:
            pdf_dir: PDF 文件目录
            chunk_size: 文本块大小
            chunk_overlap: 块之间的重叠
            
        Returns:
            dict: 存入统计
        """
        from .pdf_tools import get_pdf_files, sanitize_collection_name
        
        # 存入结果
        stats = {
            "total_files": 0,
            "success": 0,
            "failed": 0,
            "total_chunks": 0,
            "total_points": 0,
            "collections": [],
            "errors": []
        }
        
        # 获取所有 PDF 文件
        pdf_files = get_pdf_files(pdf_dir)
        
        if not pdf_files:
            print(f"[Error] 未找到 PDF 文件: {pdf_dir}")
            return stats
        
        stats["total_files"] = len(pdf_files)
        print(f"\n找到 {len(pdf_files)} 个 PDF 文件")
        
        # 使用配置
        if config.chunk_size:
            chunk_size = config.chunk_size
        if config.chunk_overlap:
            chunk_overlap = config.chunk_overlap
        
        # 创建 Qdrant 预期
        for pdf_file in pdf_files:
            collection_name = sanitize_collection_name(pdf_file["name"])
            print(f"\n处理: {pdf_file['name']}")
            print(f"  集合名: {collection_name}")
            
            # 存入单个文件
            result = self.ingest_pdf(
                pdf_path=pdf_file["path"],
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if result["status"] == "success":
                stats["success"] += 1
                stats["total_chunks"] += result["chunks_count"]
                stats["total_points"] += result["points_added"]
                stats["collections"].append({
                    "name": collection_name,
                    "chunks": result["chunks_count"],
                    "points": result["points_added"]
                })
                print(f"  [OK] 成功: {result['chunks_count']} 个块, {result['points_added']} 个向量")
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "file": pdf_file["name"],
                    "error": result.get("error", "未知错误")
                })
                print(f"  [ERROR] 失败: {result.get('error', '未知错误')}")
        
        # 打印统计
        print("\n" + "=" * 60)
        print(f"存入完成统计:")
        print(f"总文件数: {stats['total_files']}")
        print(f"成功: {stats['success']}")
        print(f"失败: {stats['failed']}")
        print(f"总块数: {stats['total_chunks']}")
        print(f"总向量数: {stats['total_points']}")
        print("=" * 60)
        
        return stats


# 全局实例
qdrant_manager = QdrantManager()
