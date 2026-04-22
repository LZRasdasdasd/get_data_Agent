# -*- coding: utf-8 -*-
import pandas as pd
import re

# 读取Excel文件
file_path = r'C:\Users\lenovo\Desktop\有效双原子论文\data_修改版本.xlsx'
df = pd.read_excel(file_path)

# 检查FileName列中是否有以时间戳开头的文件
print("=== 查找以时间戳开头的FileName ===\n")

# 时间戳格式: _20260317_142111_ 这样的模式
pattern = r'^_\d{8}_\d{6}_'

count = 0
for idx, filename in enumerate(df['FileName']):
    if pd.notna(filename):
        if re.match(pattern, str(filename)):
            count += 1
            print(f"行 {idx+2}: {filename}")

print(f"\n总共找到 {count} 条需要处理的记录")

# 显示所有FileName
print("\n=== 所有FileName内容 ===")
for idx, filename in enumerate(df['FileName']):
    if pd.notna(filename):
        print(f"行 {idx+2}: {filename}")