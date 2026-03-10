"""
配置管理模块

负责加载和管理所有配置项
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """配置类"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            env_file: 环境变量文件路径，默认为当前目录的 .env
        """
        # 加载环境变量
        if env_file:
            load_dotenv(env_file)
        else:
            # 尝试从多个位置加载 .env
            possible_paths = [
                Path(__file__).parent.parent / ".env",
                Path.cwd() / ".env",
            ]
            for path in possible_paths:
                if path.exists():
                    load_dotenv(path)
                    break
        
        # OpenAI 配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        # 支持两种环境变量名：OPENAI_BASE_URL 或 OPENAI_API_BASE
        self.openai_api_base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        # Qdrant 配置
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        
        # PDF 配置
        self.pdf_dir = os.getenv(
            "PDF_DIR", 
            r"E:\get_data_Agent\deepagents_GDatas\libs\cli\deepagents_cli\paper"
        )
        
        # 向量化配置
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        # 嵌入模型配置
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
        
        # 日志级别
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> bool:
        """
        验证配置是否完整
        
        Returns:
            bool: 配置是否有效
        """
        if not self.openai_api_key:
            print("错误: 未设置 OPENAI_API_KEY")
            return False
        
        if not self.pdf_dir:
            print("错误: 未设置 PDF_DIR")
            return False
        
        pdf_path = Path(self.pdf_dir)
        if not pdf_path.exists():
            print(f"错误: PDF 目录不存在: {self.pdf_dir}")
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """
        转换为字典（隐藏敏感信息）
        
        Returns:
            dict: 配置字典
        """
        return {
            "openai_api_key": "***" if self.openai_api_key else "未设置",
            "openai_api_base": self.openai_api_base,
            "qdrant_url": self.qdrant_url,
            "pdf_dir": self.pdf_dir,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "log_level": self.log_level,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        items = [f"  {k}: {v}" for k, v in self.to_dict().items()]
        return "配置信息:\n" + "\n".join(items)


# 全局配置实例
config = Config()
