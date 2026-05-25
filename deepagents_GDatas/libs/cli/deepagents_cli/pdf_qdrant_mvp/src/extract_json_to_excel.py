# -*- coding: utf-8 -*-
"""
将JSON中的extraction.data提取到CSV表格中
适配新的JSON格式（包含 paper_title, metal_coordination, catalytic_performance 等新字段）
"""

import json
import os
import re
import csv
from pathlib import Path


def parse_temperature(temp_str):
    """解析温度并转换为摄氏度"""
    if not temp_str or temp_str in ("-", "not specified", ""):
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
        kelvin = float(number_match.group(1))
        if kelvin > 273:
            celsius = kelvin - 273.15
            return f"{celsius:.2f}"
        else:
            return f"{kelvin:.2f}"
    
    return ""


def parse_time(time_str):
    """解析时间并转换为小时"""
    if not time_str or time_str in ("-", "not specified", ""):
        return ""
    
    time_str = str(time_str).lower().strip()
    
    hours_match = re.search(r'(\d+\.?\d*)\s*h\b', time_str)
    if hours_match:
        return f"{float(hours_match.group(1)):.2f}"
    
    minutes_match = re.search(r'(\d+\.?\d*)\s*min\b', time_str)
    if minutes_match:
        minutes = float(minutes_match.group(1))
        hours = minutes / 60
        return f"{hours:.2f}"
    
    days_match = re.search(r'(\d+\.?\d*)\s*day\b', time_str)
    if days_match:
        days = float(days_match.group(1))
        hours = days * 24
        return f"{hours:.2f}"
    
    number_match = re.search(r'(\d+\.?\d*)', time_str)
    if number_match and "h" not in time_str:
        num = float(number_match.group(1))
        if num < 100:
            hours = num / 60
            return f"{hours:.2f}"
    
    return ""


def extract_atmosphere(atmosphere_str):
    """提取气氛中的关键信息"""
    if not atmosphere_str or atmosphere_str in ("-", "not specified", ""):
        return ""
    
    atmosphere_str = str(atmosphere_str).strip()
    
    atmosphere_match = re.search(r'(N2|Ar|H2|O2|air|N₂|Ar|He|CO|CO2|NH3|vacuum)', atmosphere_str, re.IGNORECASE)
    if atmosphere_match:
        result = atmosphere_match.group(1).upper()
        if result == "VACUUM":
            return "vacuum"
        return result
    
    return ""


def extract_coordination_from_metal_coordination(metal_coordination):
    """
    从 metal_coordination 字典提取配位信息
    
    metal_coordination 格式：
    {
      "Mn": {"coordinating_elements": ["N"], "coordination_numbers": {"N": 4.0}},
      "Co": {"coordinating_elements": ["N"], "coordination_numbers": {"N": 4.0}}
    }
    
    返回：
    coordinationtypeA, numbersA = 第一个金属的配位元素和配位数
    coordinationtypeB, numbersB = 第二个金属的配位元素和配位数
    coordinationtypeC, numbersC = 额外配位信息（如果有混合配位）
    """
    coordinationtypeA = ''
    coordinationtypeB = ''
    coordinationtypeC = ''
    numbersA = ''
    numbersB = ''
    numbersC = ''
    
    if not metal_coordination or not isinstance(metal_coordination, dict):
        return coordinationtypeA, numbersA, coordinationtypeB, numbersB, coordinationtypeC, numbersC
    
    metal_list = list(metal_coordination.items())
    
    # 第一个金属
    if len(metal_list) >= 1:
        metal_name, coord_info = metal_list[0]
        if isinstance(coord_info, dict):
            coord_elems = coord_info.get('coordinating_elements', [])
            coord_nums = coord_info.get('coordination_numbers', {})
            if coord_elems:
                # 将配位元素列表合并为字符串（如 "N" 或 "N, O"）
                coordinationtypeA = ', '.join(coord_elems)
                # 将配位数合并
                num_parts = []
                for elem in coord_elems:
                    cn = coord_nums.get(elem, '')
                    if cn:
                        num_parts.append(str(cn))
                numbersA = ', '.join(num_parts) if num_parts else ''
    
    # 第二个金属
    if len(metal_list) >= 2:
        metal_name, coord_info = metal_list[1]
        if isinstance(coord_info, dict):
            coord_elems = coord_info.get('coordinating_elements', [])
            coord_nums = coord_info.get('coordination_numbers', {})
            if coord_elems:
                coordinationtypeB = ', '.join(coord_elems)
                num_parts = []
                for elem in coord_elems:
                    cn = coord_nums.get(elem, '')
                    if cn:
                        num_parts.append(str(cn))
                numbersB = ', '.join(num_parts) if num_parts else ''
    
    return coordinationtypeA, numbersA, coordinationtypeB, numbersB, coordinationtypeC, numbersC


def extract_json_data(json_file_path):
    """从单个JSON文件中提取数据（适配新JSON格式）"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extraction_data = data.get('extraction', {}).get('data', {})
        if not extraction_data:
            return None
        
        file_name = Path(json_file_path).stem
        
        # 获取反应步骤数
        reaction_steps = extraction_data.get('reaction_steps', 1)
        try:
            reaction_steps = int(reaction_steps)
        except (ValueError, TypeError):
            reaction_steps = 1
        
        # 获取 active_site 信息
        active_site_data = extraction_data.get('double_atom_catalyst_active_site', {})
        
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
            
            # 优先使用新的 metal_coordination 结构化字段
            metal_coordination = active_site_data.get('metal_coordination', {})
            if metal_coordination and isinstance(metal_coordination, dict):
                coordinationtypeA, numbersA, coordinationtypeB, numbersB, coordinationtypeC, numbersC = \
                    extract_coordination_from_metal_coordination(metal_coordination)
            else:
                # 向后兼容：从 active_site 字符串中解析
                if active_site:
                    clean_site = re.sub(r'\s*\([^)]*\)', '', active_site).strip()
                    clean_site = re.sub(r'[\-–—/·]', ' ', clean_site)
                    
                    coordination_elements = [
                        'C', 'N', 'O', 'P', 'S', 'H', 'Cl', 'F', 'Se', 'B',
                        'Si', 'Br', 'I', 'He', 'Ne', 'Ar'
                    ]
                    
                    subscript_map = {
                        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
                        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'
                    }
                    for sub_char, digit in subscript_map.items():
                        clean_site = clean_site.replace(sub_char, digit)
                    
                    clean_site = re.sub(r'\s+', ' ', clean_site).strip()
                    
                    element_pattern = r'([A-Z][a-z]?)(\d*)'
                    matches = re.findall(element_pattern, clean_site)
                    
                    coord_index = 0
                    for element, count in matches:
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
        
        results = []
        
        # 遍历所有步骤
        for step_num in range(1, reaction_steps + 1):
            step_key = f'step_{step_num}'
            step_data = extraction_data.get(step_key, {})
            
            if not step_data:
                continue
            
            # 获取反应物
            reactants = step_data.get('reactants', [])
            
            # 初始化反应物和用量（最多6个）
            reactant_list = [''] * 6
            amount_list = [''] * 6
            
            for idx, reactant_info in enumerate(reactants[:6]):
                if isinstance(reactant_info, dict):
                    reactant_list[idx] = str(reactant_info.get('reactant', ''))
                    amount_list[idx] = str(reactant_info.get('amount', ''))
            
            # 获取温度和时间
            temperature = step_data.get('temperature', '')
            reaction_time = step_data.get('reaction_time', '')
            
            # 判断是否最后一步（热解步骤）
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
            # 组装数据行（与项目现有CSV格式完全对应）
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
        import traceback
        traceback.print_exc()
        return None


def process_all_json_files(json_dir, output_dir):
    """处理目录中的所有JSON文件"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    json_files = list(Path(json_dir).glob('*.json'))
    
    print(f"找到 {len(json_files)} 个JSON文件")
    
    all_results = []
    processed_count = 0
    
    for json_file in json_files:
        # 跳过 summary 文件
        if 'summary' in json_file.name.lower():
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
    
    # 定义列顺序（与项目现有CSV格式完全一致）
    fieldnames = [
        'step_i',
        'ReactantA', 'amountA',
        'ReactantB', 'amountB',
        'ReactantC', 'amountC',
        'ReactantD', 'amountD',
        'ReactantE', 'amountE',
        'ReactantF', 'amountF',
        'Intermediate', 'temperature', 'time', 'atmosphere',
        'active_site', 'metal_metal_distance', 'FileName',
        'coordinationtypeA', 'numbersA',
        'coordinationtypeB', 'numbersB',
        'coordinationtypeC', 'numbersC',
        'stir', 'stir_time', 'stir_temperature'
    ]
    
    output_file = output_path / 'synthesis_data_updated.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row_data in all_results:
            writer.writerow(row_data)
    
    print(f"\n数据已成功导出到: {output_file}")
    print(f"\n数据已成功导出到: {output_file}")
    print(f"总共处理了 {len(all_results)} 行数据, 来自 {processed_count} 个有效文件")
    return output_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="将提取的JSON数据转换为CSV表格",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--json-dir", "-j",
        type=str,
        default=None,
        help="JSON文件目录 (默认: pdf_qdrant_mvp/queried_datas)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="输出CSV目录 (默认: pdf_qdrant_mvp/excel_datas)"
    )
    parser.add_argument(
        "--output-file", "-f",
        type=str,
        default="synthesis_data_updated.csv",
        help="输出CSV文件名 (默认: synthesis_data_updated.csv)"
    )

    args = parser.parse_args()

    current_dir = Path(__file__).parent

    json_dir = Path(args.json_dir) if args.json_dir else current_dir.parent / 'queried_datas'
    output_dir = Path(args.output_dir) if args.output_dir else current_dir.parent / 'excel_datas'

    print(f"输入目录: {json_dir}")
    print(f"输出目录: {output_dir}\n")

    process_all_json_files(json_dir, output_dir)
