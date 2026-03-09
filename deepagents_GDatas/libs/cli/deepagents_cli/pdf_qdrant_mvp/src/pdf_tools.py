"""
PDF 处理工具模块

提供 PDF 文件的读取、文本提取和分块功能
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pdfplumber


def sanitize_collection_name(filename: str) -> str:
    """
    将文件名转换为合法的 Qdrant 集合名称
    
    规则:
    1. 移除 .pdf 扩展名
    2. 转换为小写
    3. 空格和特殊字符替换为下划线
    4. 截断到 50 个字符
    
    Args:
        filename: PDF 文件名
        
    Returns:
        str: 合法的集合名称
    """
    # 移除扩展名
    name = Path(filename).stem
    
    # 转小写
    name = name.lower()
    
    # 替换特殊字符为下划线
    name = re.sub(r'[^a-z0-9_]', '_', name)
    
    # 合并连续下划线
    name = re.sub(r'_+', '_', name)
    
    # 移除首尾下划线
    name = name.strip('_')
    
    # 截断到 50 个字符
    if len(name) > 50:
        name = name[:50]
    
    # 确保不为空
    if not name:
        name = "unnamed_collection"
    
    return name


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    从 PDF 文件中提取文本内容
    
    Args:
        pdf_path: PDF 文件路径
        
    Returns:
        dict: 包含文本和元数据的字典
            - text: 完整文本
            - pages: 页数
            - char_count: 字符数
            - page_texts: 每页文本列表
    """
    result = {
        "text": "",
        "pages": 0,
        "char_count": 0,
        "page_texts": [],
        "success": False,
        "error": None
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["pages"] = len(pdf.pages)
            
            all_text = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                all_text.append(page_text)
                result["page_texts"].append({
                    "page_num": i + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
            
            result["text"] = "\n\n".join(all_text)
            result["char_count"] = len(result["text"])
            result["success"] = True
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def chunk_text(
    text: str, 
    chunk_size: int = 1000, 
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    将文本分割成块
    
    Args:
        text: 要分割的文本
        chunk_size: 每个块的最大字符数
        overlap: 块之间的重叠字符数
        
    Returns:
        list: 文本块列表，每个块包含:
            - text: 块文本
            - chunk_index: 块索引
            - start_pos: 起始位置
            - end_pos: 结束位置
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    chunk_index = 0
    
    while start < text_length:
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句子边界处分割
        if end < text_length:
            # 查找最近的句子结束符
            for sep in ['。', '.', '!', '?', '！', '？', '\n']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start + chunk_size // 2:
                    end = last_sep + 1
                    break
        
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": end
            })
            chunk_index += 1
        
        # 下一块的起始位置（考虑重叠）
        start = end - overlap if end < text_length else text_length
        
        # 避免无限循环
        if start <= chunks[-1]["start_pos"] if chunks else 0:
            start = end
    
    return chunks


def get_pdf_files(directory: str) -> List[Dict[str, Any]]:
    """
    获取目录下所有的 PDF 文件
    
    Args:
        directory: 目录路径
        
    Returns:
        list: PDF 文件信息列表
    """
    pdf_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return pdf_files
    
    for file_path in dir_path.glob("*.pdf"):
        pdf_files.append({
            "path": str(file_path),
            "name": file_path.name,
            "collection_name": sanitize_collection_name(file_path.name),
            "size_kb": file_path.stat().st_size / 1024
        })
    
    # 按文件名排序
    pdf_files.sort(key=lambda x: x["name"])
    
    return pdf_files


def clean_text(text: str) -> str:
    """
    清理文本
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空格
    text = " ".join(text.split())
    
    # 移除特殊控制字符
    text = text.replace("\x00", "")
    
    return text.strip()
