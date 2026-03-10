"""
测试脚本 - 验证配置和连接
"""

import sys
import uuid
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_config():
    """测试配置加载"""
    print("=" * 50)
    print("1. 测试配置加载...")
    
    from config import config
    
    print(f"   API Key: {config.openai_api_key[:10]}...")
    print(f"   API Base: {config.openai_api_base}")
    print(f"   Qdrant URL: {config.qdrant_url}")
    print(f"   PDF Dir: {config.pdf_dir}")
    print(f"   Embedding Model: {config.embedding_model}")
    print(f"   Embedding Dimension: {config.embedding_dimension}")
    
    # 验证配置
    if not config.validate():
        print("   [ERROR] 配置验证失败!")
        return False
    
    print("   [OK] 配置加载成功!")
    return True


def test_qdrant_connection():
    """测试 Qdrant 连接"""
    print("\n" + "=" * 50)
    print("2. 测试 Qdrant 连接...")
    
    from vector_tools import QdrantManager
    
    try:
        manager = QdrantManager()
        collections = manager.list_collections()
        print(f"   现有集合: {[c['name'] for c in collections]}")
        print("   [OK] Qdrant 连接成功!")
        return True
    except Exception as e:
        print(f"   [ERROR] Qdrant 连接失败: {e}")
        return False


def get_pdf_files(directory: str):
    """获取目录中的所有 PDF 文件"""
    import re
    from pathlib import Path
    
    pdf_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return pdf_files
    
    for pdf_file in sorted(dir_path.glob("*.pdf")):
        name = pdf_file.stem
        collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        collection_name = re.sub(r'_+', '_', collection_name).strip('_')
        
        pdf_files.append({
            "name": pdf_file.name,
            "path": str(pdf_file),
            "collection_name": collection_name
        })
    
    return pdf_files


def test_pdf_files():
    """测试 PDF 文件检测"""
    print("\n" + "=" * 50)
    print("3. 测试 PDF 文件检测...")
    
    from config import config
    
    pdf_files = get_pdf_files(config.pdf_dir)
    print(f"   找到 {len(pdf_files)} 个 PDF 文件:")
    
    for pdf in pdf_files[:3]:
        print(f"      - {pdf['name'][:40]}... -> {pdf['collection_name']}")
    
    if len(pdf_files) > 3:
        print(f"      ... 还有 {len(pdf_files) - 3} 个文件")
    
    print("   [OK] PDF 文件检测成功!")
    return True


def test_embedding():
    """测试 Embedding 生成"""
    print("\n" + "=" * 50)
    print("4. 测试 Embedding 生成...")
    
    from vector_tools import QdrantManager
    from config import config
    
    try:
        manager = QdrantManager()
        test_text = "这是一个测试文本，用于验证 embedding 功能。"
        embedding = manager.generate_embedding(test_text)
        print(f"   Embedding 维度: {len(embedding)}")
        print(f"   前 5 个值: {embedding[:5]}")
        
        if len(embedding) == config.embedding_dimension:
            print(f"   [OK] Embedding 生成成功! (维度匹配)")
        else:
            print(f"   [WARN] Embedding 维度不匹配! 期望: {config.embedding_dimension}, 实际: {len(embedding)}")
            print(f"   [INFO] 将使用实际维度: {len(embedding)}")
        return True
    except Exception as e:
        print(f"   [ERROR] Embedding 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_text_from_pdf(pdf_path: str):
    """从 PDF 文件中提取文本"""
    import pdfplumber
    
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        
        return {
            "success": True,
            "text": text,
            "pages": len(pdf.pages) if 'pdf' in dir() else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "pages": 0
        }


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """将文本分割成重叠的块"""
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append({
                "text": chunk,
                "chunk_index": chunk_index,
                "start": start,
                "end": min(end, len(text))
            })
            chunk_index += 1
        
        start = end - overlap
        if start >= len(text) - overlap:
            break
    
    return chunks


def sanitize_collection_name(name: str) -> str:
    """将文件名转换为有效的集合名称"""
    import re
    collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    collection_name = re.sub(r'_+', '_', collection_name)
    collection_name = collection_name.strip('_')
    return collection_name


def test_single_pdf_ingest():
    """测试单个 PDF 的导入"""
    print("\n" + "=" * 50)
    print("5. 测试单个 PDF 导入...")
    
    from vector_tools import QdrantManager
    from config import config
    from qdrant_client.models import PointStruct
    
    # 获取第一个 PDF 文件
    pdf_files = get_pdf_files(config.pdf_dir)
    if not pdf_files:
        print("   [ERROR] 没有找到 PDF 文件!")
        return False
    
    test_pdf = pdf_files[0]
    collection_name = test_pdf['collection_name']
    
    print(f"   测试文件: {test_pdf['name'][:50]}...")
    print(f"   集合名称: {collection_name}")
    
    try:
        manager = QdrantManager()
        
        # 提取文本
        result = extract_text_from_pdf(test_pdf['path'])
        if not result['success']:
            print(f"   [ERROR] 无法提取文本: {result['error']}")
            return False
        
        text = result['text']
        
        # 只取前 1000 个字符测试
        test_text_chunk = text[:1000] if len(text) > 1000 else text
        chunks = chunk_text(test_text_chunk, chunk_size=200, overlap=50)
        
        print(f"   提取文本长度: {len(text)} 字符")
        print(f"   测试块数: {len(chunks)}")
        
        # 创建集合
        create_result = manager.create_collection(collection_name)
        print(f"   集合状态: {create_result['status']}")
        
        # 只导入第一个块
        if chunks:
            first_chunk = chunks[0]
            embedding = manager.generate_embedding(first_chunk['text'])
            point_id = str(uuid.uuid4())
            
            manager.client.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": first_chunk['text'][:200] + "...",
                        "chunk_index": first_chunk['chunk_index'],
                        "source": test_pdf['name']
                    }
                )]
            )
            print(f"   [OK] 成功导入测试数据!")
            
            # 验证数据已存入
            info = manager.client.get_collection(collection_name)
            print(f"   集合信息: {info.points_count} 个点")
        
        print("   [OK] 单个 PDF 导入测试成功!")
        return True
    except Exception as e:
        print(f"   [ERROR] 单个 PDF 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  PDF Qdrant MVP 测试脚本")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    tests = [
        ("配置加载", test_config),
        ("Qdrant连接", test_qdrant_connection),
        ("PDF文件检测", test_pdf_files),
        ("Embedding生成", test_embedding),
        ("单个PDF导入", test_single_pdf_ingest),
    ]
    
    for name, func in tests:
        try:
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 {name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"   {status} {name}")
        if result:
            passed += 1
    
    print(f"\n   通过: {passed}/{len(results)} 个测试")
    print("=" * 60)
    
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
