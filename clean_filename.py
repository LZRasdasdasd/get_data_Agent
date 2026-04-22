# -*- coding: utf-8 -*-
import pandas as pd
import re

# 读取Excel文件
file_path = r'C:\Users\lenovo\Desktop\有效双原子论文\data_修改版本.xlsx'
df = pd.read_excel(file_path)

# 时间戳格式: _20260317_142111_ (以_开头，后面是8位日期 + 6位时间 + _)
pattern = r'^_\d{8}_\d{6}_'

# 记录修改数量
modified_count = 0

# 处理FileName列
for idx in range(len(df)):
    filename = df.loc[idx, 'FileName']
    if pd.notna(filename):
        filename_str = str(filename)
        # 检查是否匹配时间戳前缀模式
        match = re.match(pattern, filename_str)
        if match:
            # 删除时间戳前缀
            new_filename = filename_str[match.end():]
            df.loc[idx, 'FileName'] = new_filename
            modified_count += 1

print(f"总共修改了 {modified_count} 条记录")

# 保存修改后的文件到新文件
output_path = r'C:\Users\lenovo\Desktop\有效双原子论文\data_修改版本_已清理.xlsx'
df.to_excel(output_path, index=False)
print(f"\n文件已保存到: {output_path}")

# 验证结果
print("\n=== 验证：修改后的FileName列样例 ===")
print(df['FileName'].head(20))