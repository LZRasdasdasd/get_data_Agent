"""
测试新的分块逻辑
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingest_markdown import chunk_markdown, is_heading, split_paragraph_at_period, merge_small_paragraphs

# 测试文本
test_text = """# Acid gas-induced fabrication of hydrophilic carbon nitride

## Abstract
This is a test paragraph. It has multiple sentences. Each sentence ends with a period.

## Introduction
Short intro line.

This is a longer paragraph that contains enough characters to be considered a valid chunk on its own. We will see how it gets processed by the new chunking algorithm.

## Experiment
The reaction temperature was controlled at 25 ◦C by condensing unit. After the photocatalytic reaction, the iodometry is used to determine the H2O2 concentration in filtered solution.
"""

print("=" * 60)
print("测试新的分块逻辑")
print("=" * 60)

# 测试分块
chunks = chunk_markdown(test_text, chunk_size=500, min_chunk_size=100)

print(f"\n总块数: {len(chunks)}")
print("=" * 60)

for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ({chunk['char_count']} chars) ---")
    text = chunk['text']
    if len(text) > 200:
        print(text[:200] + "...")
    else:
        print(text)

print("\n" + "=" * 60)
print("测试完成!")
