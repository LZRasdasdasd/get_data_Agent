#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF批量转换为Markdown脚本
将指定目录下的所有PDF文件转换为Markdown格式

使用方法:
    python convert_pdf_to_markdown.py
"""

import os
import sys
from pathlib import Path


def main():
    # 设置路径
    script_dir = Path(__file__).parent
    pdf_dir = Path(r"D:\数据集\论文分段存储0\pdf4001-5000")
    output_dir = script_dir / "markdown_output_4001-5000"
    script_path = script_dir / "deepagents_GDatas" / "libs" / "cli" / "deepagents_cli" / "pdf_qdrant_mvp" / "src" / "pdf_to_markdown.py"
    
    print("=" * 60)
    print("PDF批量转换为Markdown工具")
    print("=" * 60)
    print(f"\nPDF源目录: {pdf_dir}")
    print(f"输出目录: {output_dir}")
    print(f"脚本路径: {script_path}")
    print()
    
    # 检查路径
    if not pdf_dir.exists():
        print(f"[错误] PDF目录不存在: {pdf_dir}")
        return 1
    
    if not script_path.exists():
        print(f"[错误] 脚本文件不存在: {script_path}")
        return 1
    
    # 统计PDF文件数
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[警告] 目录中没有找到PDF文件: {pdf_dir}")
        return 0
    
    print(f"[信息] 找到 {len(pdf_files)} 个PDF文件")
    print()
    
    # 修改sys.argv并调用pdf_to_markdown脚本
    sys.argv = [
        str(script_path),
        "--pdf-dir", str(pdf_dir),
        "--output-dir", str(output_dir)
    ]
    
    # 导入并执行pdf_to_markdown模块
    sys.path.insert(0, str(script_path.parent))
    
    try:
        import pdf_to_markdown
        pdf_to_markdown.main()
    except Exception as e:
        print(f"[错误] 执行转换时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("=" * 60)
    print(f"[成功] 批量转换完成!")
    print("=" * 60)
    print(f"\nMarkdown文件已保存到: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
