"""
PDF 转 Markdown 转换脚本

将 PDF 文件转换为 Markdown 格式并保存到指定文件夹。
使用 pdfplumber 的字符级提取功能，更精确地保留下标/上标格式。

使用方法:
    python src/pdf_to_markdown.py --pdf-dir <PDF目录> --output-dir <输出目录>
    python src/pdf_to_markdown.py --pdf-file <PDF文件路径> --output-dir <输出目录>
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from config import config
from pdf_tools import get_pdf_files

# 初始化控制台
console = Console()


# 下标和上标字符映射
SUBSCRIPT_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
    'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
    'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
    'v': 'ᵥ', 'x': 'ₓ',
}

SUPERSCRIPT_MAP = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    'n': 'ⁿ', 'i': 'ⁱ',
}

# 化学元素符号集合（用于上下文判断）
CHEMICAL_ELEMENTS = {
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
    'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
    'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
    'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
    'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
    'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm'
}

# 常见单位（后面跟数字通常是上标，如 min⁻¹）
UNIT_KEYWORDS = {
    'min', 'h', 's', 'ms', 'cm', 'mm', 'm', 'km', 'g', 'kg', 'mg',
    'mol', 'M', 'mM', 'μM', 'L', 'mL', 'μL', 'C', 'K', 'J', 'kJ',
    'eV', 'V', 'mV', 'A', 'W', 'Hz', 'kHz', 'MHz', 'GHz', 'Pa', 'kPa',
    'rpm', 'rpm', 'wt', 'vol'
}

# 特殊字符映射
SPECIAL_CHAR_MAP = {
    '': '*',
    '−': '-',
    '–': '-',
    '—': '--',
    ''': "'",
    ''': "'",
    '"': '"',
    '"': '"',
    '…': '...',
    '': '×',
    '⨉': '×',
    '✕': '×',
    '': 'μ',
    'µ': 'μ',
}


def convert_to_subscript(text: str) -> str:
    """将文本转换为下标形式"""
    result = []
    for char in text:
        result.append(SUBSCRIPT_MAP.get(char, char))
    return ''.join(result)


def convert_to_superscript(text: str) -> str:
    """将文本转换为上标形式"""
    result = []
    for char in text:
        result.append(SUPERSCRIPT_MAP.get(char, char))
    return ''.join(result)


def normalize_special_chars(text: str) -> str:
    """规范化特殊字符"""
    for old, new in SPECIAL_CHAR_MAP.items():
        text = text.replace(old, new)
    return text


class PDFToMarkdownConverter:
    """PDF 转 Markdown 转换器"""
    
    def __init__(self, pdf_path: str):
        """初始化转换器"""
        self.pdf_path = pdf_path
        self.pages = []
        self.main_font_size = None
        
    def convert(self) -> Dict[str, Any]:
        """执行转换"""
        import pdfplumber
        
        result = {
            "success": False,
            "text": "",
            "pages": 0,
            "char_count": 0,
            "error": None
        }
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                result["pages"] = len(pdf.pages)
                all_text = []
                
                for i, page in enumerate(pdf.pages):
                    page_text = self._process_page(page, i + 1)
                    all_text.append(page_text)
                
                result["text"] = "\n\n".join(all_text)
                result["char_count"] = len(result["text"])
                result["success"] = True
                
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def _process_page(self, page, page_num: int) -> str:
        """处理单页PDF"""
        # 1. 提取表格
        tables = page.find_tables()
        table_bboxes = [t.bbox for t in tables]
        
        # 2. 提取字符信息
        chars = page.chars
        
        if not chars:
            return ""
        
        # 3. 分析主字体大小
        self._analyze_font_sizes(chars)
        
        # 4. 按行组织字符
        lines = self._organize_chars_to_lines(chars, table_bboxes)
        
        # 5. 转换为文本
        text = self._lines_to_text(lines, tables, table_bboxes)
        
        return text
    
    def _analyze_font_sizes(self, chars: List[Dict]) -> None:
        """分析页面中的主要字体大小"""
        from collections import Counter
        
        sizes = [round(c.get('size', 12), 1) for c in chars if c.get('size')]
        if sizes:
            size_counter = Counter(sizes)
            # 取出现次数最多的作为主字体大小
            self.main_font_size = size_counter.most_common(1)[0][0]
    
    def _organize_chars_to_lines(self, chars: List[Dict], table_bboxes: List[Tuple]) -> List[List[Dict]]:
        """将字符组织成行，同时标记下标/上标"""
        if not chars:
            return []
        
        # 首先找出主字体大小
        from collections import Counter
        sizes = [c.get('size', 12) for c in chars]
        size_counter = Counter([round(s, 1) for s in sizes])
        main_size = size_counter.most_common(1)[0][0] if size_counter else 12
        
        # 过滤掉表格内的字符
        non_table_chars = []
        for char in chars:
            char_top = char.get('top', 0)
            in_table = False
            for bbox in table_bboxes:
                if (bbox[0] <= char.get('x0', 0) <= bbox[2] and
                    bbox[1] <= char_top <= bbox[3]):
                    in_table = True
                    break
            if not in_table:
                non_table_chars.append(char)
        
        # 按位置排序
        sorted_chars = sorted(non_table_chars, key=lambda c: (c.get('top', 0), c.get('x0', 0)))
        
        # 使用更智能的行分组策略
        lines = []
        current_line = []
        current_baseline = None  # 使用基准线而非简单的 top
        
        for char in sorted_chars:
            char_top = char.get('top', 0)
            char_size = char.get('size', 12)
            char_text = char.get('text', '')
            
            # 判断是否是小字体（可能是下标/上标）
            size_ratio = char_size / main_size if main_size > 0 else 1
            is_small_font = size_ratio < 0.85
            
            if current_baseline is None:
                # 第一个字符
                current_line = [char.copy()]
                if not is_small_font:
                    current_baseline = char_top
                else:
                    current_baseline = char_top  # 暂时使用当前位置
            else:
                # 检查是否应该归入当前行
                # 1. 对于正常字体字符：top 位置接近
                # 2. 对于小字体字符：x 位置紧接在前一个字符后面，且 y 位置在合理范围内
                
                should_join = False
                
                if not is_small_font:
                    # 正常字体：使用标准容差判断
                    tolerance = max(2, main_size * 0.15)
                    if abs(char_top - current_baseline) <= tolerance:
                        should_join = True
                        # 更新基准线
                        current_baseline = char_top
                else:
                    # 小字体：检查是否紧接在前一个字符后面
                    if current_line:
                        last_char = current_line[-1]
                        last_x1 = last_char.get('x1', 0)
                        last_top = last_char.get('top', 0)
                        last_size = last_char.get('size', 12)
                        
                        curr_x0 = char.get('x0', 0)
                        
                        # 水平距离：字符应该紧接或略有间隙
                        gap = curr_x0 - last_x1
                        max_gap = max(last_size, char_size) * 0.5  # 允许半个字符宽度的间隙
                        
                        # 垂直范围：应该在基准线上下一定范围内
                        # 下标在基准线下方，上标在基准线上方
                        vertical_range = main_size * 1.2  # 允许1.2个主字体高度的偏移
                        
                        if gap <= max_gap and abs(char_top - current_baseline) <= vertical_range:
                            should_join = True
                
                if should_join:
                    current_line.append(char.copy())
                else:
                    # 开始新行
                    if current_line:
                        lines.append(current_line)
                    current_line = [char.copy()]
                    if not is_small_font:
                        current_baseline = char_top
                    else:
                        # 小字体开始新行时，基准线暂定为该位置
                        current_baseline = char_top
        
        if current_line:
            lines.append(current_line)
        
        # 标记每行中的下标/上标
        self._mark_subscripts_superscripts(lines)
        
        return lines
    
    def _get_context_before(self, line: List[Dict], idx: int, max_chars: int = 10) -> str:
        """获取当前字符前面的上下文文本"""
        context = []
        for i in range(max(0, idx - max_chars), idx):
            text = line[i].get('text', '')
            if text and not line[i].get('is_subscript') and not line[i].get('is_superscript'):
                context.append(text)
        return ''.join(context)
    
    def _determine_script_type_by_context(self, context: str, char_text: str) -> tuple:
        """
        根据上下文判断字符应该是上标还是下标
        
        Returns:
            tuple: (is_subscript, is_superscript)
        """
        if not context:
            return (False, False)
        
        context_stripped = context.rstrip()
        
        # 1. 检查是否跟在单位后面（上标情况）
        # 如 min⁻¹, cm⁻², mol⁻¹, C mol⁻¹
        for unit in UNIT_KEYWORDS:
            if context_stripped.endswith(unit):
                # 如果是数字或负号，通常是上标（如 -1, -2, 2）
                if re.match(r'^[-−]?\d+$', char_text) or char_text in ['-', '−']:
                    return (False, True)
        
        # 2. 检查是否跟在 10 后面（科学计数法，上标）
        # 如 10⁻⁵, 10⁺³
        if context_stripped.endswith('10'):
            if re.match(r'^[-−+＋]?\d+$', char_text) or char_text in ['-', '−', '+', '＋']:
                return (False, True)
        
        # 3. 检查是否是负号后面跟数字（单位上标的延续）
        # 例如：min 后面已经跟了负号，现在来数字 1
        if re.search(r'(min|h|s|cm|mm|mol|L|mL|C)\s*[-−]$', context_stripped, re.IGNORECASE):
            if re.match(r'^\d+$', char_text):
                return (False, True)
        
        # 4. 检查是否跟在化学元素后面（下标情况）
        # 如 H₂O, N₂O₃, Fe₂
        for elem in CHEMICAL_ELEMENTS:
            if context_stripped.endswith(elem):
                # 元素后面跟数字，通常是下标
                if re.match(r'^\d+$', char_text):
                    return (True, False)
        
        # 5. 检查是否跟在常见化学基团后面（下标情况）
        # 如 NH₃, NO₂, CO₂, SO₄, OH⁻
        chem_groups = ['NH', 'NO', 'CO', 'SO', 'PO', 'OH', 'CH', 'H ']
        for group in chem_groups:
            if context_stripped.endswith(group):
                if re.match(r'^\d+$', char_text):
                    return (True, False)
        
        # 6. 检查是否跟在右括号后面（可能是化学式如 Zn(NO₃)₂）
        if context_stripped.endswith(')'):
            if re.match(r'^\d+$', char_text):
                return (True, False)
        
        # 7. 检查是否跟在 @NG 等催化剂标记后面（下标，如 Fe₂@NG）
        if re.search(r'@\w*$', context_stripped) or re.search(r'Fe\s*$', context_stripped):
            if re.match(r'^\d+$', char_text):
                return (True, False)
        
        # 8. 单独的负号：检查上下文是否有单位特征
        if char_text in ['-', '−']:
            # 如果前面的单词看起来像单位，则判断为上标
            for unit in UNIT_KEYWORDS:
                if context_stripped.endswith(unit):
                    return (False, True)
        
        # 默认无法确定
        return (False, False)
    
    def _mark_subscripts_superscripts(self, lines: List[List[Dict]]) -> None:
        """标记下标和上标字符"""
        from collections import Counter
        
        for line in lines:
            if not line:
                continue
            
            # 计算行的基准线位置（使用大多数字符的top值）
            tops = [c.get('top', 0) for c in line]
            top_counter = Counter([round(t, 0) for t in tops])
            baseline_top = top_counter.most_common(1)[0][0] if top_counter else 0
            
            # 找出主字体大小（使用最大频率的字体大小）
            sizes = [c.get('size', 12) for c in line]
            size_counter = Counter([round(s, 1) for s in sizes])
            main_size = size_counter.most_common(1)[0][0] if size_counter else 12
            
            # 按x坐标排序，确保处理顺序正确
            sorted_line = sorted(enumerate(line), key=lambda x: x[1].get('x0', 0))
            
            for orig_idx, char in sorted_line:
                char_text = char.get('text', '')
                char_size = char.get('size', 12)
                char_top = char.get('top', 0)
                
                # 字体明显较小（相对于主字体）
                size_ratio = char_size / main_size if main_size > 0 else 1
                
                if size_ratio < 0.85:  # 放宽阈值
                    # 获取前面的上下文
                    context = self._get_context_before(line, orig_idx, max_chars=15)
                    
                    # 优先使用上下文判断（对于单位后面的负号等情况更准确）
                    is_sub, is_sup = self._determine_script_type_by_context(context, char_text)
                    
                    if is_sup:
                        # 上下文明确指示是上标（如 min⁻¹）
                        char['is_subscript'] = False
                        char['is_superscript'] = True
                    elif is_sub:
                        # 上下文明确指示是下标（如 H₂O）
                        char['is_subscript'] = True
                        char['is_superscript'] = False
                    else:
                        # 上下文无法确定，使用位置判断
                        position_diff = char_top - baseline_top
                        
                        if position_diff > 1.0:  # 位置明显较低，下标
                            char['is_subscript'] = True
                            char['is_superscript'] = False
                        elif position_diff < -1.0:  # 位置明显较高，上标
                            char['is_subscript'] = False
                            char['is_superscript'] = True
                        else:
                            # 位置也不明显，检查字符内容
                            # 负号通常出现在上标中（如 ⁻¹）
                            if char_text in ['-', '−', '+']:
                                # 检查是否跟在单位或10后面
                                if any(context.rstrip().endswith(u) for u in UNIT_KEYWORDS) or context.rstrip().endswith('10'):
                                    char['is_subscript'] = False
                                    char['is_superscript'] = True
                                else:
                                    # 默认为下标（化学式中的电荷）
                                    char['is_subscript'] = True
                                    char['is_superscript'] = False
                            else:
                                # 无法确定，默认为下标
                                char['is_subscript'] = True
                                char['is_superscript'] = False
    
    def _lines_to_text(self, lines: List[List[Dict]], tables: List, table_bboxes: List[Tuple]) -> str:
        """将行转换为文本"""
        result_parts = []
        
        # 处理非表格区域
        for line in lines:
            line_text = self._process_line(line)
            if line_text.strip():
                result_parts.append(line_text)
        
        # 处理表格
        for table in tables:
            table_text = self._process_table(table)
            if table_text.strip():
                result_parts.append(table_text)
        
        return '\n'.join(result_parts)
    
    def _process_line(self, line: List[Dict]) -> str:
        """处理单行字符"""
        if not line:
            return ""
        
        # 按x坐标排序
        sorted_chars = sorted(line, key=lambda c: c.get('x0', 0))
        
        result = []
        prev_char = None
        current_subscript = ""
        current_superscript = ""
        
        for char in sorted_chars:
            text = char.get('text', '')
            
            # 规范化特殊字符
            text = normalize_special_chars(text)
            
            # 处理空格检测
            if prev_char:
                prev_x1 = prev_char.get('x1', 0)
                curr_x0 = char.get('x0', 0)
                gap = curr_x0 - prev_x1
                
                # 如果间隙较大，添加空格
                prev_size = prev_char.get('size', 12)
                if gap > prev_size * 0.3:
                    # 先处理累积的下标/上标
                    if current_subscript:
                        result.append(convert_to_subscript(current_subscript))
                        current_subscript = ""
                    if current_superscript:
                        result.append(convert_to_superscript(current_superscript))
                        current_superscript = ""
                    result.append(' ')
            
            # 检查下标/上标
            is_sub = char.get('is_subscript', False)
            is_sup = char.get('is_superscript', False)
            
            # 处理状态转换
            if is_sub:
                if current_superscript:
                    result.append(convert_to_superscript(current_superscript))
                    current_superscript = ""
                current_subscript += text
            elif is_sup:
                if current_subscript:
                    result.append(convert_to_subscript(current_subscript))
                    current_subscript = ""
                current_superscript += text
            else:
                # 正常文本
                if current_subscript:
                    result.append(convert_to_subscript(current_subscript))
                    current_subscript = ""
                if current_superscript:
                    result.append(convert_to_superscript(current_superscript))
                    current_superscript = ""
                result.append(text)
            
            prev_char = char
        
        # 处理末尾的下标/上标
        if current_subscript:
            result.append(convert_to_subscript(current_subscript))
        if current_superscript:
            result.append(convert_to_superscript(current_superscript))
        
        return ''.join(result)
    
    def _process_table(self, table) -> str:
        """处理表格"""
        try:
            table_data = table.extract()
            if not table_data or len(table_data) < 2:
                return ""
            
            # 格式化为 Markdown 表格
            result = []
            max_cols = max(len(row) for row in table_data)
            
            for i, row in enumerate(table_data):
                # 处理每个单元格
                cells = []
                for cell in row:
                    cell_text = str(cell) if cell else ''
                    # 清理和格式化单元格文本
                    cell_text = normalize_special_chars(cell_text)
                    cell_text = self._post_process_text(cell_text)
                    cells.append(cell_text.strip())
                
                # 填充空单元格
                while len(cells) < max_cols:
                    cells.append('')
                
                result.append('| ' + ' | '.join(cells) + ' |')
                
                # 第一行后添加分隔线
                if i == 0:
                    result.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
            
            return '\n'.join(result)
            
        except Exception:
            return ""
    
    def _post_process_text(self, text: str) -> str:
        """后处理文本"""
        # 处理科学计数法
        text = self._process_scientific_notation(text)
        
        # 处理化学式中的普通数字下标（作为后备）
        text = self._process_chemical_subscripts(text)
        
        return text
    
    def _process_scientific_notation(self, text: str) -> str:
        """处理科学计数法"""
        def replace_exp(match):
            sign = match.group(2)
            exp = match.group(3)
            return match.group(1) + convert_to_superscript(sign + exp)
        
        # 匹配 10-5, 10+3 等格式
        pattern = r'(10)([-+])(\d+)'
        return re.sub(pattern, replace_exp, text)
    
    def _process_chemical_subscripts(self, text: str) -> str:
        """处理化学式中的数字下标（后备方案）"""
        def replace_formula(match):
            return match.group(1) + convert_to_subscript(match.group(2))
        
        # 匹配元素符号后跟数字（排除常见单词）
        # 这个正则更保守，避免误匹配
        pattern = r'\b([A-Z][a-z]?)(\d{1,2})(?![a-zA-Z0-9])'
        
        # 只有在看起来像化学式的上下文中才替换
        # 检查是否包含化学相关关键词
        chem_keywords = ['mol', 'M', 'mM', 'μM', 'g-', 'g-', 'N-', 'C-']
        if any(kw in text for kw in chem_keywords):
            return re.sub(pattern, replace_formula, text)
        
        return text


def merge_broken_chemical_lines(text: str) -> str:
    """
    合并被错误分割的化学式行和单位上标行
    
    PDF 提取时常见问题：
    - 化学式下标被提取到单独的行
    - 例如: "N O" 后面跟着 "2 3" 应该合并为 "N₂O₃"
    - 单位上标被提取到单独的行
    - 例如: "mL min" 后面跟着 "-1" 应该合并为 "mL min⁻¹"
    """
    lines = text.split('\n')
    merged_lines = []
    
    # 化学元素符号集合
    elements = CHEMICAL_ELEMENTS
    
    # 常见化学式前缀（后面通常跟数字下标）
    chem_prefixes = [
        'NH', 'NO', 'CO', 'OH', 'SO', 'PO', 'CH', 'FeN', 'TM',
        'Zn(NO', 'Fe(NO', 'H SO', 'Na SO', 'N O', 'N ORR',
        'N O-saturated', 'H O', 'Fe @NG', 'Fe ', 'N ', 'DAC',
        # 新增更多化学前缀
        'Fe₂@NG', 'V @NG', 'Cr @NG', 'Mn @NG', 'Co @NG', 'Ni @NG', 'Cu @NG',
        'FeN SAC', 'FeN', 'N₂ORR', 'N ORR', 'H O',
        # 单元素结尾的情况
        ' @NG', '@NG', ' DAC', 'DAC', ' SAC', 'SAC',
        # 化学式中的空格分离情况
        'Na SO', 'H SO', 'Tris-HCl',
        # 催化剂相关
        '₂@NG', '₂@NG DAC',
    ]
    
    # 单位后缀模式（后面跟的数字应该是上标）
    unit_suffixes = ['min', 'h', 's', 'ms', 'cm', 'mm', 'm', 'km', 'g', 'kg', 'mg',
                     'mol', 'M', 'mM', 'L', 'mL', 'μL', 'C', 'K', 'J', 'kJ',
                     'eV', 'V', 'mV', 'A', 'W', 'Hz', 'Pa', 'kPa', 'rpm', 'wt',
                     'μB', 'Å', 'nm', 'pm']
    
    def ends_with_element_or_prefix(line: str) -> bool:
        """检查行是否以元素或化学前缀结尾"""
        line = line.rstrip()
        if not line:
            return False
        
        # 检查是否以元素结尾
        for elem in elements:
            if line.endswith(elem) or re.search(rf'\b{elem}\s*$', line):
                return True
        
        # 检查是否以化学前缀结尾
        for prefix in chem_prefixes:
            if line.endswith(prefix) or re.search(rf'{re.escape(prefix)}\s*$', line):
                return True
        
        # 检查最后一个单词是否像元素符号
        words = line.split()
        if words:
            last_word = words[-1]
            # 单个大写字母或大写+小写字母
            if re.match(r'^[A-Z][a-z]?$', last_word):
                return True
            # 以大写字母结尾的单词
            if last_word and last_word[-1].isupper():
                return True
            # 以空格+元素结尾的情况（如 "Fe " 或 "N "）
            if re.search(r'\s[A-Z][a-z]?\s*$', line):
                return True
        
        return False
    
    def ends_with_unit(line: str) -> bool:
        """检查行是否以单位结尾（后面应该跟上标）"""
        line = line.rstrip()
        if not line:
            return False
        
        for unit in unit_suffixes:
            if line.endswith(unit) or re.search(rf'\b{unit}\s*$', line):
                return True
        return False
    
    def ends_with_incomplete_formula(line: str) -> bool:
        """
        检查行是否以不完整的化学式结尾
        例如: "6H O" 应该是 "6H₂O"
        """
        line = line.rstrip()
        if not line:
            return False
        
        # 检查是否以 "数字+元素+空格" 结尾（如 "6H " 在 "6H₂O" 中）
        if re.search(r'\d+[A-Z][a-z]?\s*$', line):
            return True
        
        # 检查是否是化学式中间被断开的情况
        # 例如 "N O" 后面应该跟数字
        if re.search(r'\b[A-Z][a-z]?\s+[A-Z][a-z]?\s*$', line):
            return True
        
        return False
    
    def process_number_line(numbers_str: str, is_unit_context: bool = False) -> str:
        """
        处理数字行，根据上下文决定是上标还是下标
        
        Args:
            numbers_str: 数字字符串（可能包含空格）
            is_unit_context: 是否是单位上下文（True则使用上标）
        """
        numbers = re.findall(r'-?\d+', numbers_str)
        if is_unit_context:
            return ''.join(convert_to_superscript(n) for n in numbers)
        else:
            return ''.join(convert_to_subscript(n) for n in numbers)
    
    def distribute_subscripts_to_formula(formula_prefix: str, numbers_str: str) -> str:
        """
        将数字分配到化学式的正确位置
        
        例如: "N O" + "2 3" → "N₂O₃"
              "Na SO" + "2 4" → "Na₂SO₄"
        """
        # 提取数字
        numbers = re.findall(r'\d+', numbers_str)
        if not numbers:
            return formula_prefix + process_number_line(numbers_str, is_unit_context=False)
        
        # 找到化学式中的元素位置
        # 匹配元素符号（大写字母+可选小写字母）
        element_positions = []
        for match in re.finditer(r'([A-Z][a-z]?)', formula_prefix):
            element_positions.append(match.start())
        
        # 如果数字数量等于元素数量，逐个分配
        if len(numbers) == len(element_positions):
            result = list(formula_prefix)
            # 从后往前插入，避免位置偏移
            for i in range(len(numbers) - 1, -1, -1):
                pos = element_positions[i]
                # 找到该元素符号的结束位置
                elem_match = re.match(r'[A-Z][a-z]?', formula_prefix[pos:])
                if elem_match:
                    insert_pos = pos + elem_match.end()
                    result.insert(insert_pos, convert_to_subscript(numbers[i]))
            return ''.join(result)
        
        # 如果只有一个数字，追加到末尾
        if len(numbers) == 1:
            return formula_prefix + convert_to_subscript(numbers[0])
        
        # 默认：将所有数字转换为下标并追加
        return formula_prefix + ''.join(convert_to_subscript(n) for n in numbers)
    
    i = 0
    while i < len(lines):
        current_line = lines[i].strip()
        
        # 检查是否需要与下一行合并
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # 情况1: 下一行是纯数字和空格（可能是下标或上标）
            if next_line and re.match(r'^[-−]?[\d\s]+$', next_line):
                # 判断是化学式上下文还是单位上下文
                is_unit = ends_with_unit(current_line)
                is_chem = ends_with_element_or_prefix(current_line)
                is_incomplete = ends_with_incomplete_formula(current_line)
                
                if is_chem or is_unit or is_incomplete:
                    # 检查是否包含负号（单位通常是负数上标如 ⁻¹）
                    has_minus = '-' in next_line or '−' in next_line
                    
                    if is_unit or has_minus:
                        # 单位上下文：使用上标
                        merged_line = current_line.rstrip() + process_number_line(next_line, is_unit_context=True)
                    elif is_incomplete and ' ' in current_line.rstrip().split()[-1] if current_line.rstrip().split() else False:
                        # 化学式中间有空格的情况，需要智能分配下标
                        merged_line = distribute_subscripts_to_formula(current_line.rstrip(), next_line)
                    else:
                        # 化学式上下文：使用下标
                        merged_line = current_line.rstrip() + process_number_line(next_line, is_unit_context=False)
                    
                    merged_lines.append(merged_line)
                    i += 2
                    continue
            
            # 情况2: 下一行是 "-1", "-2" 等单个负数（单位上标）
            if re.match(r'^[-−]\d+$', next_line):
                if ends_with_unit(current_line):
                    merged_line = current_line.rstrip() + convert_to_superscript(next_line.replace('−', '-'))
                    merged_lines.append(merged_line)
                    i += 2
                    continue
            
            # 情况3: 下一行是单个短字符（可能是下标字母或数字）
            if len(next_line) <= 3 and next_line and not re.search(r'[.!?。！？]$', next_line):
                # 检查当前行是否以特定模式结尾
                if ends_with_element_or_prefix(current_line):
                    # 如果是数字，转换为下标
                    if re.match(r'^\d+$', next_line):
                        merged_line = current_line.rstrip() + convert_to_subscript(next_line)
                    else:
                        merged_line = current_line.rstrip() + convert_to_subscript(next_line)
                    merged_lines.append(merged_line)
                    i += 2
                    continue
        
        merged_lines.append(current_line)
        i += 1
    
    return '\n'.join(merged_lines)


def post_process_chemical_formulas(text: str) -> str:
    """
    后处理化学式
    
    处理在文本中仍然以普通数字形式出现的下标，以及常见的错误模式
    """
    # 化学元素符号集合（用于匹配）
    elements_pattern = r'(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm)'
    
    def replace_chemical_subscript(match):
        """替换化学式中的数字为下标"""
        elem = match.group(1)
        num = match.group(2)
        return elem + convert_to_subscript(num)
    
    # 匹配元素符号后跟1-2位数字的模式
    pattern = rf'({elements_pattern})(\d{{1,2}})(?![a-zA-Z0-9])'
    text = re.sub(pattern, replace_chemical_subscript, text)
    
    # 处理常见化学式前缀
    chem_prefix_patterns = [
        (r'(NH)(\d+)(?![a-zA-Z])', 'NH₃'),
        (r'(NO)(\d+)(?![a-zA-Z])', 'NO₂'),
        (r'(CO)(\d+)(?![a-zA-Z])', 'CO₂'),
        (r'(SO)(\d+)(?![a-zA-Z])', 'SO₄'),
        (r'(PO)(\d+)(?![a-zA-Z])', 'PO₄'),
        (r'(OH)(\d*)(?![a-zA-Z])', 'OH'),
    ]
    
    for pattern, _ in chem_prefix_patterns:
        text = re.sub(pattern, replace_chemical_subscript, text)
    
    # 修复常见的错误模式
    
    # 1. 修复 "N²O" → "N₂O" (上标误用为下标)
    text = re.sub(r'N²O', 'N₂O', text)
    text = re.sub(r'N³', 'N₃', text)
    
    # 2. 修复 "NH³" → "NH₃" (上标误用为下标)
    text = re.sub(r'NH³', 'NH₃', text)
    
    # 3. 修复 "H²O" → "H₂O"
    text = re.sub(r'H²O', 'H₂O', text)
    text = re.sub(r'H²SO', 'H₂SO', text)
    
    # 4. 修复 "Fe²@NG" → "Fe₂@NG" (元素后跟数字应该是下标)
    text = re.sub(r'([A-Z][a-z]?)²@NG', r'\1₂@NG', text)
    text = re.sub(r'([A-Z][a-z]?)³@NG', r'\1₃@NG', text)
    
    # 5. 修复 "TM²" → "TM₂" (过渡金属后跟数字)
    text = re.sub(r'TM²', 'TM₂', text)
    text = re.sub(r'TM³', 'TM₃', text)
    
    # 6. 修复 " @NG" 后面跟着数字的情况
    # 例如 "Fe @NG" + "2" 应该是 "Fe₂@NG"
    text = re.sub(r'([A-Z][a-z]?) @NG', r'\1₂@NG', text)
    
    # 7. 修复电荷符号
    text = re.sub(r'NH₄\+', 'NH₄⁺', text)
    text = re.sub(r'NO₂\-', 'NO₂⁻', text)
    text = re.sub(r'NO₃\-', 'NO₃⁻', text)
    text = re.sub(r'OH\-', 'OH⁻', text)
    
    # 8. 修复 "N ORR₂" → "N₂ORR" 模式
    text = re.sub(r'N ORR₂', 'N₂ORR', text)
    text = re.sub(r'N ₂ORR', 'N₂ORR', text)
    
    # 9. 修复 "Fe₂@NG" 中的空格问题
    text = re.sub(r'Fe\s+₂\s*@\s*NG', 'Fe₂@NG', text)
    text = re.sub(r'([A-Z][a-z]?)\s+₂\s*@\s*NG', r'\1₂@NG', text)
    
    # 10. 修复 "6H O" → "6H₂O" 类型的问题
    text = re.sub(r'(\d+)H O\b', r'\1H₂O', text)
    text = re.sub(r'(\d+)H₂ O\b', r'\1H₂O', text)
    
    # 11. 修复 Na₂SO₄, H₂SO₄ 等硫酸盐
    text = re.sub(r'Na\s*₂\s*SO\s*₄', 'Na₂SO₄', text)
    text = re.sub(r'H\s*₂\s*SO\s*₄', 'H₂SO₄', text)
    
    # 12. 修复科学计数法中的上标
    # 10⁻⁵ 应该保持为上标
    text = re.sub(r'10\s*[-−]\s*(\d+)', lambda m: '10' + convert_to_superscript('-' + m.group(1)), text)
    
    # ===== 新增的修复规则 =====
    
    # 13. 修复 TM₂@NG DACs 后面单独跟着 "2" 的情况
    # 例如 "TM₂@NG DACs, where the" 后面跟着 "2" 应该删除
    # 注意： 这些复杂的跨行正则可能不工作，已简化
    
    # 14. 修复 TM₂@NG₂ → TM₂@NG (错误的上标)
    text = re.sub(r'TM₂@NG₂', 'TM₂@NG', text)
    
    # 15. 修复 "ΔG(*N O)" → "ΔG(*N₂O)"
    text = re.sub(r'\*N O\)', '*N₂O)', text)
    
    # 16. 修复 "d-band center (ε )" → "d-band center (εd)"
    text = re.sub(r'\(ε \)', '(εd)', text)
    text = re.sub(r'ε d\b', 'εd', text)
    
    # 17. 处理单独一行的数字与上一行化学式的合并
    # 分行处理
    lines = text.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是单独的数字行（1-9，常见的下标/上标数字）
        if re.match(r'^[1-9]$', stripped):
            # 检查上一行是否以特定模式结尾
            if new_lines:
                prev_line = new_lines[-1]
                # 如果上一行以以下模式结尾，跳过这个数字行（这些是误识别的独立数字）
                skip_patterns = [
                    r'(DACs|@NG|DAC\.|DAC)$',           # DACs 或 DAC. 或 DAC 结尾
                    r'(active center|studied)$',        # 特定词汇结尾
                    r'(TM₂@NG|Fe₂@NG|Cr₂@NG|Mn₂@NG|Co₂@NG|V₂@NG)$',  # 双原子催化剂结尾
                    r'(the|where the)$',                # 常见的连接词结尾
                    r'(TM₂|Fe₂|Cr₂|Mn₂|Co₂|V₂)\s*$',   # 过渡金属下标结尾
                    r'\)$',                             # 右括号结尾
                    r'(εd|ΔG)$',                        # 科学符号结尾
                    r'(ΔG\(\*N₂O\)|ΔG\(\*NH)',          # 吉布斯自由能符号
                    r'(SAC|SAC\.)$',                    # SAC 结尾
                    r'(FeN₄|FeN)\s*$',                  # FeN4 等结尾
                    r'(products|product)$',             # products 结尾
                    r'NH\s*$',                          # NH 结尾（后面应该是下标）
                    r'Fe₂@NG\s*$',                      # Fe₂@NG 结尾
                    r'(NH₃|NH|N₂|N)\s+products',        # NH products 等结尾
                    r'(flow cell|H cell)$',             # cell 结尾
                    r'(rather than N|rather than|than N|than)\s*$',  # than 结尾
                    r'due to the$',                     # due to the 结尾
                    r'(Fig\.|Figure|Table)\s*S[_\d]',   # 图/表编号后的误识别
                    r'(Fig\.|Figure|Table)\s*[_\d]',    # 图/表编号后的误识别
                    r'DACs\.$',                         # DACs. 结尾
                    r'NG DACs$',                        # NG DACs 结尾
                    r'(S-\d+)$',                        # S-1, S-2 等章节号
                    r'(center|site|sites)$',            # center/site 等词结尾
                    r'\b(DAC|DACs)\s*$',                # DAC/DACs 结尾
                ]
                matched = False
                for pattern in skip_patterns:
                    if re.search(pattern, prev_line, re.IGNORECASE):
                        matched = True
                        break
                
                if matched:
                    # 特殊处理：如果上一行以 "NH " 结尾，这个数字应该是下标
                    if re.search(r'NH\s*$', prev_line):
                        new_lines[-1] = prev_line.rstrip() + '₃'
                        continue
                    # 如果上一行以 "FeN " 结尾，这个数字应该是下标
                    if re.search(r'FeN\s*$', prev_line):
                        new_lines[-1] = prev_line.rstrip() + '₄'
                        continue
                    # 如果上一行以 "N " 结尾（后面跟着 products），这个数字应该是下标
                    if re.search(r'(?<!N)N\s*$', prev_line) and not re.search(r'N[₂₃₄]\s*$', prev_line):
                        new_lines[-1] = prev_line.rstrip() + '₂'
                        continue
                    continue  # 跳过这个单独的数字行
        
        new_lines.append(line)
    
    text = '\n'.join(new_lines)
    
    # 18. 修复 NO  and NO ₋ 模式 (离子符号被分开)
    text = re.sub(r'NO\s+(\d+)', r'NO\1', text)
    text = re.sub(r'NO\s*₋', 'NO⁻', text)
    
    # 19. 修复 "NH₄ /NO /NO ₋" 模式
    text = re.sub(r'NH₄\s*/NO\s*/NO\s*₋', 'NH₄⁺/NO₂⁻/NO₃⁻', text)
    
    # 20. 修复单独的 "+" 或 "-" 在行首表示离子电荷
    lines = text.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是单独的 "+" 或 "-" 行
        if stripped in ['+', '-']:
            # 检查上一行是否以化学物质结尾
            if new_lines:
                prev_line = new_lines[-1].rstrip()
                # 如果上一行以 NH₄, NO₂, NO₃ 等结尾，合并为电荷符号
                if re.search(r'(NH₄|NO₂|NO₃|OH)$', prev_line):
                    if stripped == '+':
                        new_lines[-1] = prev_line + '⁺'
                    else:
                        new_lines[-1] = prev_line + '⁻'
                    continue
        
        new_lines.append(line)
    
    text = '\n'.join(new_lines)
    
    # 21. 修复 "NH " 后跟 "3" 的模式
    text = re.sub(r'NH\s+(\d+)\b', lambda m: 'NH' + convert_to_subscript(m.group(1)), text)
    
    # 22. 修复 "N O" 后跟 "2" 的模式 (中间有空格的化学式)
    text = re.sub(r'N\s+O\b', 'N₂O', text)  # 简单情况
    text = re.sub(r'N\s+(\d+)\s*O\s*(\d*)\b', lambda m: 'N' + convert_to_subscript(m.group(1)) + 'O' + (convert_to_subscript(m.group(2)) if m.group(2) else ''), text)
    
    # 23. 修复 Fe₂@NG 后面多余的数字
    text = re.sub(r'(Fe₂@NG[^.\n]*?)(?:\s*\n\s*2\s*\n)', r'\1', text)
    
    # 24. 修复 "V₂@NG DAC" 后面多余的 "2"
    text = re.sub(r'(V₂@NG DAC[^.\n]*?)(?:\s*\n\s*2\s*\n)', r'\1', text)
    text = re.sub(r'(Cr₂@NG DAC[^.\n]*?)(?:\s*\n\s*2\s*\n)', r'\1', text)
    text = re.sub(r'(Mn₂@NG DAC[^.\n]*?)(?:\s*\n\s*2\s*\n)', r'\1', text)
    text = re.sub(r'(Co₂@NG DAC[^.\n]*?)(?:\s*\n\s*2\s*\n)', r'\1', text)
    
    # 25. 修复图标题后的独立数字（如 Fig. S₅ 后面的 "2"）
    # 匹配 Fig. S 后跟数字，然后下一行是单独的数字
    text = re.sub(r'(Fig\. S[_\d][^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    text = re.sub(r'(Fig\. S[_\d][^\n]*?)\s*\n\s*\d\s*\n', r'\1\n', text)
    
    # 26. 修复 Figure 标题后的独立数字
    text = re.sub(r'(Figure\s+\S+[^\n]*?)\s*\n\s*\d\s*\n', r'\1\n', text)
    
    # 27. 修复 Table 标题后的独立数字
    text = re.sub(r'(Table\s+S[_\d][^\n]*?)\s*\n\s*\d\s*\n', r'\1\n', text)
    
    # 28. 清理连续的多个空行（保留最多两个）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 29. 修复 "TM₂@NG DACs" 后面多余的 "2"
    text = re.sub(r'(TM₂@NG DACs[^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 30. 修复 "active center" 后面多余的 "2"
    text = re.sub(r'(active center[^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 31. 修复 "DAC" 或 "DAC." 后面多余的 "2"（如 "V₂@NG DAC" 后面）
    text = re.sub(r'([VCrMnFeCoNiCu]₂@NG\s+DAC[^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 32. 修复 "The cyan highlights" 后面多余的 "2"
    text = re.sub(r'(The cyan highlights[^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 33. 修复 "PDS" 后面多余的 "2"
    text = re.sub(r'(PDS[^\n]*?)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 34. 修复 " Enabled" 后面多余的数字（标题行）
    text = re.sub(r'(NH\s+Enabled)\s*\n\s*2\s*\n\s*3\s*\n', r'\1\n', text)
    
    # 35. 修复化学式中的独立数字（如 "Zn(NO₃)₂·6H₂O and 30 mg" 后面的 "2"）
    text = re.sub(r'(cetyltrimethylammonium bromide)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 36. 修复 "bromide" 后面的 "2"
    text = re.sub(r'(bromide)\s*\n\s*2\s*\n', r'\1\n', text)
    
    # 37. 修复 "d-band center" 后面独立的 "d" 字母
    text = re.sub(r'(d-band center \(εd\) of the)\s*\n\s*d\s*\n', r'\1\n', text)
    
    # 38. 修复 "of the" 后面独立的 "d" 字母（通用规则）
    text = re.sub(r'(of the)\s*\n\s*d\s*\n', r'\1\n', text)
    
    return text


def smart_format_text(text: str) -> str:
    """
    智能格式化文本
    
    处理段落合并、标题检测等
    """
    # 先合并被分开的化学式行
    text = merge_broken_chemical_lines(text)
    
    # 后处理化学式
    text = post_process_chemical_formulas(text)
    
    lines = text.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            # 保留空行作为段落分隔
            if result and result[-1] != '':
                result.append('')
        else:
            # 检测可能的标题
            if _is_likely_heading(stripped):
                if result and result[-1] != '':
                    result.append('')
                # 如果不是已有 markdown 格式，添加标题标记
                if not stripped.startswith('#'):
                    stripped = '## ' + stripped
                result.append(stripped)
                result.append('')
            else:
                result.append(stripped)
    
    # 清理多余空行
    final_text = '\n'.join(result)
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)
    
    return final_text.strip()


def _is_likely_heading(line: str) -> bool:
    """判断是否可能是标题"""
    if not line:
        return False
    
    # 已有 markdown 标题格式
    if line.startswith('#'):
        return False  # 已经是标题格式，不需要再处理
    
    # 常见章节模式
    section_patterns = [
        r'^S-\d+$',  # S-1, S-2
        r'^\d+\.\s+[A-Z]',  # 1. Introduction
        r'^(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|References)',
        r'^(Experimental|Theoretical|Computational)\s+\w+',
        r'^(Table|Figure|Fig\.)\s+\d+',
        r'^Synthesis\s+of',
        r'^Characterizations?$',
    ]
    
    for pattern in section_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    
    # 短行且全大写
    if len(line) < 50 and line.isupper() and len(line.split()) <= 5:
        return True
    
    return False


def convert_pdf_to_markdown(pdf_path: str, output_dir: str, overwrite: bool = False) -> dict:
    """
    将单个 PDF 文件转换为 Markdown 格式
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        dict: 转换结果
    """
    result = {
        "success": False,
        "input_file": pdf_path,
        "output_file": None,
        "char_count": 0,
        "pages": 0,
        "error": None
    }
    
    try:
        # 获取文件名（无扩展名）
        pdf_name = Path(pdf_path).stem
        output_file = Path(output_dir) / f"{pdf_name}.md"
        
        # 检查文件是否已存在
        if output_file.exists() and not overwrite:
            result["output_file"] = str(output_file)
            result["error"] = "文件已存在，跳过（使用 --overwrite 覆盖）"
            return result
        
        # 使用转换器
        converter = PDFToMarkdownConverter(pdf_path)
        pdf_result = converter.convert()
        
        if not pdf_result["success"]:
            result["error"] = f"提取失败: {pdf_result.get('error')}"
            return result
        
        # 智能格式化
        formatted_text = smart_format_text(pdf_result["text"])
        
        # 构建 Markdown 内容
        markdown_lines = [
            f"# {pdf_name}",
            "",
            f"> **Source**: {pdf_path}",
            f"> **Pages**: {pdf_result['pages']}",
            f"> **Characters**: {pdf_result['char_count']}",
            f"> **Converted**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            formatted_text,
        ]
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        result["success"] = True
        result["output_file"] = str(output_file)
        result["char_count"] = pdf_result["char_count"]
        result["pages"] = pdf_result["pages"]
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF 转 Markdown 工具 - 将 PDF 文件转换为 Markdown 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--pdf-dir", "-d",
        type=str,
        default=None,
        help="PDF 文件目录路径 (默认使用 .env 中的配置)"
    )
    
    parser.add_argument(
        "--pdf-file", "-f",
        type=str,
        default=None,
        help="单个 PDF 文件路径 (优先于 --pdf-dir)"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="markdown_docs",
        help="Markdown 输出目录路径 (默认: markdown_docs)"
    )
    
    parser.add_argument(
        "--overwrite", "-w",
        action="store_true",
        help="覆盖已存在的文件"
    )
    
    args = parser.parse_args()
    
    # 显示配置信息
    console.print(Panel.fit(
        "[bold cyan]PDF 转 Markdown 工具[/bold cyan]\n"
        "[dim]使用字符级提取，精确保留下标/上标格式[/dim]",
        border_style="cyan"
    ))
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]输出目录已创建/确认: {output_dir}[/green]")
    
    # 确定要处理的 PDF 文件列表
    pdf_files = []
    
    if args.pdf_file:
        # 处理单个 PDF 文件
        pdf_path = Path(args.pdf_file)
        if not pdf_path.exists():
            console.print(f"[red]PDF 文件不存在: {args.pdf_file}[/red]")
            sys.exit(1)
        if not pdf_path.suffix.lower() == '.pdf':
            console.print(f"[red]不是有效的 PDF 文件: {args.pdf_file}[/red]")
            sys.exit(1)
        
        pdf_files.append({
            "path": str(pdf_path),
            "name": pdf_path.name,
            "size_kb": pdf_path.stat().st_size / 1024
        })
        console.print(f"PDF 文件: {args.pdf_file}")
    else:
        # 处理目录中的所有 PDF 文件
        if args.pdf_dir:
            config.pdf_dir = args.pdf_dir
        
        if not config.validate():
            console.print("[red]配置验证失败![/red]")
            console.print(config)
            sys.exit(1)
        
        console.print(f"PDF 目录: {config.pdf_dir}")
        pdf_files = get_pdf_files(config.pdf_dir)
        
        if not pdf_files:
            console.print(f"[red]未找到 PDF 文件: {config.pdf_dir}[/red]")
            sys.exit(1)
    
    console.print(f"输出目录: {args.output_dir}")
    console.print(f"\n[bold]找到 {len(pdf_files)} 个 PDF 文件[/bold]")
    
    # 转换统计
    stats = {
        "total": len(pdf_files),
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "total_chars": 0,
        "files": []
    }
    
    # 使用进度条
    with Progress(console=console) as progress:
        overall_task = progress.add_task(
            "[cyan]转换 PDF 文件...",
            total=len(pdf_files)
        )
        
        for i in range(len(pdf_files)):
            pdf_file = pdf_files[i]
            progress.update(overall_task, advance=1)
            
            console.print(f"\n[{i+1}/{len(pdf_files)}] 处理: {pdf_file['name']}")
            
            # 转换 PDF
            result = convert_pdf_to_markdown(
                pdf_file["path"],
                args.output_dir,
                args.overwrite
            )
            
            if result["success"]:
                stats["success"] += 1
                stats["total_chars"] += result["char_count"]
                stats["files"].append({
                    "name": pdf_file["name"],
                    "output": result["output_file"],
                    "chars": result["char_count"],
                    "pages": result["pages"]
                })
                console.print(f"  [green]成功: {result['output_file']}[/green]")
                console.print(f"  字符数: {result['char_count']}, 页数: {result['pages']}")
            elif "已存在" in str(result.get("error", "")):
                stats["skipped"] += 1
                console.print(f"  [yellow]跳过: {result['error']}[/yellow]")
            else:
                stats["failed"] += 1
                console.print(f"  [red]失败: {result.get('error')}[/red]")
    
    # 显示统计
    console.print("\n")
    console.print("=" * 60)
    console.print(Panel.fit(
        "[bold green]转换完成统计[/bold green]",
        border_style="green"
    ))
    
    console.print(f"总文件数: {stats['total']}")
    console.print(f"成功: {stats['success']}")
    console.print(f"跳过: {stats['skipped']}")
    console.print(f"失败: {stats['failed']}")
    console.print(f"总字符数: {stats['total_chars']}")
    
    # 显示生成的文件列表
    if stats["files"]:
        console.print("\n[bold]生成的 Markdown 文件:[/bold]")
        for f in stats["files"]:
            console.print(f"  - {f['output']}: {f['chars']} 字符, {f['pages']} 页")
    
    # 提示下一步
    console.print("\n")
    console.print(Panel(
        "[bold yellow]下一步操作[/bold yellow]\n\n"
        "Markdown 文件已生成，可以使用 MCP RAG 工具添加到 RAG 系统:\n"
        "  - 使用 add_document 工具添加完整文档\n"
        "  - 使用 search_documents 工具搜索文档\n\n"
        f"输出目录: {output_dir.absolute()}",
        border_style="yellow"
    ))


if __name__ == "__main__":
    main()
