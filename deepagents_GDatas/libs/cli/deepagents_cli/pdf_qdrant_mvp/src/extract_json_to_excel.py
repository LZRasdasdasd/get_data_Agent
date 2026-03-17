# -*- coding: utf-8 -*-
"""
将JSON中的extraction.data提取到Excel表格中
"""

import json
import os
import re
import csv
from pathlib import Path


def parse_temperature(temp_str):
    """解析温度并转换为摄氏度"""
    if not temp_str or temp_str == "-" or temp_str == "not specified":
        return ""
    
    temp_str = str(temp_str).strip()
    
    # 尝试匹配开尔文温度
    kelvin_match = re.search(r'(\d+\.?\d*)\s*K', temp_str)
    if kelvin_match:
        kelvin = float(kelvin_match.group(1))
        celsius = kelvin - 273.15
        return f"{celsius:.2f}"
    
    # 尝试匹配摄氏度温度
    celsius_match = re.search(r'(\d+\.?\d*)\s*[℃°C]', temp_str)
    if celsius_match:
        return f"{float(celsius_match.group(1)):.2f}"
    
    # 尝试匹配纯数字
    number_match = re.search(r'(\d+\.?\d*)', temp_str)
    if number_match and "room" not in temp_str.lower():
        # 如果是纯数字,假设是开尔文
        kelvin = float(number_match.group(1))
        if kelvin > 273:  # 如果大于273,可能是开尔文
            celsius = kelvin - 273.15
            return f"{celsius:.2f}"
        else:
            return f"{kelvin:.2f}"
    
    return ""


def parse_time(time_str):
    """解析时间并转换为小时"""
    if not time_str or time_str == "-" or time_str == "not specified":
        return ""
    
    time_str = str(time_str).lower().strip()
    
    # 尝试提取小时
    hours_match = re.search(r'(\d+\.?\d*)\s*h\b', time_str)
    if hours_match:
        return f"{float(hours_match.group(1)):.2f}"
    
    # 尝试提取分钟
    minutes_match = re.search(r'(\d+\.?\d*)\s*min\b', time_str)
    if minutes_match:
        minutes = float(minutes_match.group(1))
        hours = minutes / 60
        return f"{hours:.2f}"
    
    # 尝试提取天数
    days_match = re.search(r'(\d+\.?\d*)\s*day\b', time_str)
    if days_match:
        days = float(days_match.group(1))
        hours = days * 24
        return f"{hours:.2f}"
    
    # 尝试提取简单的数字(假设是分钟)
    number_match = re.search(r'(\d+\.?\d*)', time_str)
    if number_match and "h" not in time_str:
        num = float(number_match.group(1))
        if num < 100:  # 如果数字小于100,可能是分钟
            hours = num / 60
            return f"{hours:.2f}"
    
    return ""


def extract_atmosphere(atmosphere_str):
    """提取气氛中的关键信息"""
    if not atmosphere_str or atmosphere_str == "-" or atmosphere_str == "not specified":
        return ""
    
    atmosphere_str = str(atmosphere_str).strip()
    
    # 提取气体类型(N2, Ar, H2, O2, air等)
    atmosphere_match = re.search(r'(N2|Ar|H2|O2|air|N₂|Ar|He|CO|CO2|NH3)', atmosphere_str, re.IGNORECASE)
    if atmosphere_match:
        return atmosphere_match.group(1).upper()
    
    return ""


def determine_step_type(step_data, total_steps):
    """判断步骤类型:是否是最后一步(热解步骤)"""
    # 简单判断:如果是最后一步,通常是热解步骤
    # 但需要根据温度和时间来判断
    temp = step_data.get('temperature', '')
    time_val = step_data.get('reaction_time', '')
    
    # 如果温度很高(>500K)或者时间较长,可能是热解步骤
    if temp:
        temp_num = re.search(r'(\d+)', temp)
        if temp_num and int(temp_num.group(1)) > 500:
            return 'pyrolysis'
    
    return 'dissolution'


def extract_json_data(json_file_path):
    """从单个JSON文件中提取数据"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extraction_data = data.get('extraction', {}).get('data', {})
        if not extraction_data:
            return None
        
        file_name = os.path.basename(json_file_path)
        
        # 获取反应步骤数
        reaction_steps = extraction_data.get('reaction_steps', 1)
        try:
            reaction_steps = int(reaction_steps)
        except (ValueError, TypeError):
            reaction_steps = 1
        
        # 获取active_site信息
        active_site_data = extraction_data.get('double_atom_catalyst_active_site', {})
        # 获取active_site信息
        active_site_data = extraction_data.get('double_atom_catalyst_active_site', {})
        
        # 初始化所有变量
        active_site = ''
        metal_metal_distance = ''
        coordinationtypeA = ''
        coordinationtypeB = ''
        coordinationtypeC = ''
        numbersA = ''
        numbersB = ''
        numbersC = ''
        
        if active_site_data and isinstance(active_site_data, dict):
            active_site = active_site_data.get('active_site', '')
            metal_metal_distance = active_site_data.get('metal_metal_distance', '')
            
            # 解析active_site字符串,提取coordination类型和数量
            if active_site:
                # 步骤1: 移除括号内的注释内容并规范化分隔符
                active_site = re.sub(r'\s*\([^)]*\)', '', active_site).strip()
                # 将常见连字符或分隔符替换为空格，避免把元素连在一起
                active_site = re.sub(r'[\-–—/·]', ' ', active_site)

                # 定义coordination元素(常见非金属元素)
                coordination_elements = [
                    'C', 'N', 'O', 'P', 'S', 'H', 'Cl', 'F', 'Se', 'B',
                    'Si', 'Br', 'I', 'He', 'Ne', 'Ar'
                ]

                # Unicode下标字符映射表（扩展）
                subscript_map = {
                    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
                    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
                }

                # 步骤2: 将Unicode下标字符转换为普通数字
                for sub_char, digit in subscript_map.items():
                    active_site = active_site.replace(sub_char, digit)

                # 压缩连续空格
                active_site = re.sub(r'\s+', ' ', active_site).strip()

                # 初始化coordination字段，默认numbers为'0'（表示无非金属）
                coordinationtypeA = ''
                coordinationtypeB = ''
                coordinationtypeC = ''
                numbersA = '0'
                numbersB = '0'
                numbersC = '0'

                # 使用正则表达式匹配化学式中的元素及其数量
                # 格式: 元素符号(大写字母开头,可选小写) + 可选数字
                element_pattern = r'([A-Z][a-z]?)(\d*)'
                matches = re.findall(element_pattern, active_site)

                # 遍历匹配结果,提取coordination元素及其数量
                coord_index = 0  # 标记coordination字段的序号(A, B, C)
                for element, count in matches:
                    # 检查是否为coordination元素(非金属)
                    if element in coordination_elements:
                        if coord_index == 0:
                            coordinationtypeA = element
                            numbersA = count if count else '1'
                        elif coord_index == 1:
                            coordinationtypeB = element
                            numbersB = count if count else '1'
                        elif coord_index == 2:
                            coordinationtypeC = element
                            numbersC = count if count else '1'
                        coord_index += 1
                        if coord_index >= 3:
                            break

                # 如果没有找到任何coordination元素,保持 numbers 为 '0'（已初始化）
            
            # 尝试从JSON中读取coordination字段(如果存在)
            if not coordinationtypeA:
                coordinationtypeA = active_site_data.get('coordinationtypeA', '')
            if not coordinationtypeB:
                coordinationtypeB = active_site_data.get('coordinationtypeB', '')
            if not coordinationtypeC:
                coordinationtypeC = active_site_data.get('coordinationtypeC', '')
            if not numbersA:
                numbersA = active_site_data.get('numbersA', '')
            if not numbersB:
                numbersB = active_site_data.get('numbersB', '')
            if not numbersC:
                numbersC = active_site_data.get('numbersC', '')
        
        results = []
        
        # 遍历所有步骤
        for step_num in range(1, reaction_steps + 1):
            step_key = f'step_{step_num}'
            step_data = extraction_data.get(step_key, {})
            
            if not step_data:
                continue
            
            # 获取反应物
            reactants = step_data.get('reactants', [])
            
            # 初始化反应物和用量
            reactant_list = [''] * 6  # A, B, C, D, E, F
            amount_list = [''] * 6
            
            for idx, reactant_info in enumerate(reactants[:6]):  # 最多6个反应物
                if isinstance(reactant_info, dict):
                    reactant_list[idx] = str(reactant_info.get('reactant', ''))
                    amount_list[idx] = str(reactant_info.get('amount', ''))
            
            # 判断步骤类型
            step_type = determine_step_type(step_data, reaction_steps)
            
            # 获取温度和时间
            temperature = step_data.get('temperature', '')
            reaction_time = step_data.get('reaction_time', '')
            
            # 如果是最后一步,temperature是热解温度,否则是stir_temperature
            if step_num == reaction_steps:
                final_temperature = parse_temperature(temperature)
                final_time = parse_time(reaction_time)
                stir_temperature = ""
            else:
                final_temperature = ""
                final_time = ""
                stir_temperature = parse_temperature(temperature)
            
            # 获取中间产物
            intermediate = step_data.get('product', '')
            
            # 获取气氛
            atmosphere = extract_atmosphere(step_data.get('atmosphere', ''))
            
            # 判断是否搅拌
            stir = ""
            stir_time = ""
            if reaction_time and "stir" in reaction_time.lower():
                stir = "yes"
                stir_time = parse_time(reaction_time)
            
            # 组装数据行
            row_data = {
                'step_i': step_num,
                'ReactantA': reactant_list[0],
                'amountA': amount_list[0],
                'ReactantB': reactant_list[1],
                'amountB': amount_list[1],
                'ReactantC': reactant_list[2],
                'amountC': amount_list[2],
                'ReactantD': reactant_list[3],
                'amountD': amount_list[3],
                'ReactantE': reactant_list[4],
                'amountE': amount_list[4],
                'ReactantF': reactant_list[5],
                'amountF': amount_list[5],
                'Intermediate': intermediate,
                'temperature': final_temperature,
                'time': final_time,
                'atmosphere': atmosphere,
                'active_site': active_site,
                'metal_metal_distance': metal_metal_distance,
                'FileName': file_name,
                'coordinationtypeA': coordinationtypeA,
                'numbersA': numbersA,
                'coordinationtypeB': coordinationtypeB,
                'numbersB': numbersB,
                'coordinationtypeC': coordinationtypeC,
                'numbersC': numbersC,
                'stir': stir,
                'stir_time': stir_time,
                'stir_temperature': stir_temperature
            }
            
            results.append(row_data)
        
        return results
    
    except Exception as e:
        print(f"处理文件 {json_file_path} 时出错: {e}")
        return None


def process_all_json_files(json_dir, output_dir):
    """处理目录中的所有JSON文件"""
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取所有JSON文件
    json_files = list(Path(json_dir).glob('*.json'))
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    all_results = []
    processed_count = 0
    
    for json_file in json_files:
        # 跳过batch summary文件
        if 'batch_summary' in json_file.name:
            continue
        
        print(f"正在处理: {json_file.name}")
        results = extract_json_data(json_file)
        if results:
            all_results.extend(results)
            processed_count += 1
        else:
            print(f"  跳过文件: {json_file.name} (无有效数据)")
    
    if not all_results:
        print("没有提取到任何数据")
        return
    
    # 创建CSV文件
    if all_results:
        # 定义列顺序
        fieldnames = [
            'step_i', 'ReactantA', 'amountA', 'ReactantB', 'amountB',
            'ReactantC', 'amountC', 'ReactantD', 'amountD',
            'ReactantE', 'amountE', 'ReactantF', 'amountF',
            'Intermediate', 'temperature', 'time', 'atmosphere',
            'active_site', 'metal_metal_distance', 'FileName',
            'coordinationtypeA', 'numbersA', 'coordinationtypeB', 'numbersB',
            'coordinationtypeC', 'numbersC', 'stir', 'stir_time', 'stir_temperature'
        ]
        
        output_file = output_path / 'synthesis_data_updated.csv'
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # 逐行写入数据
            for row_data in all_results:
                writer.writerow(row_data)
        
        print(f"\n数据已成功导出到: {output_file}")
        print(f"总共处理了 {len(all_results)} 行数据,来自 {processed_count} 个有效文件")


if __name__ == '__main__':
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 定义输入和输出目录
    json_dir = current_dir.parent / 'queried_datas'
    output_dir = current_dir / 'excel_datas'
    
    print(f"输入目录: {json_dir}")
    print(f"输出目录: {output_dir}\n")
    
    # 处理所有JSON文件
    process_all_json_files(json_dir, output_dir)
