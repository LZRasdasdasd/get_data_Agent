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
from collections import Counter
from dataclasses import dataclass, field

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from qdrant_config import config

# 初始化控制台
console = Console()


# ========== 辅助函数 ==========

def get_pdf_files(directory: str) -> List[Dict[str, str]]:
    """获取目录中的所有 PDF 文件
    
    Args:
        directory: 目录路径
        
    Returns:
        包含 PDF 文件信息的列表，每个元素包含:
        - name: 文件名
        - path: 完整路径
        - collection_name: 集合名称（用于向量数据库）
    """
    import re
    from pathlib import Path
    
    pdf_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return pdf_files
    
    for pdf_file in sorted(dir_path.glob("*.pdf")):
        # 生成集合名称：将文件名转换为小写，替换特殊字符
        name = pdf_file.stem
        collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        collection_name = re.sub(r'_+', '_', collection_name).strip('_')
        
        pdf_files.append({
            "name": pdf_file.name,
            "path": str(pdf_file),
            "collection_name": collection_name
        })
    
    return pdf_files


# ========== 常量定义 ==========

@dataclass
class ScriptMaps:
    """下标和上标字符映射"""
    subscript: Dict[str, str] = field(default_factory=lambda: {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
        'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
        'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
        'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
        'v': 'ᵥ', 'x': 'ₓ',
    })
    superscript: Dict[str, str] = field(default_factory=lambda: {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
        'n': 'ⁿ', 'i': 'ⁱ',
    })


SCRIPT_MAPS = ScriptMaps()

# 化学元素符号集合
CHEMICAL_ELEMENTS = frozenset({
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
})

# 面积/体积单位（后面跟数字通常是上标，如 cm², mm³）
AREA_VOLUME_UNITS = frozenset({
    'cm', 'mm', 'm', 'km', 'μm', 'nm', 'pm', 'Å'
})

# 时间/速率单位（后面跟负数是上标，如 min⁻¹, s⁻¹）
RATE_UNITS = frozenset({
    'min', 'h', 's', 'ms', 'rpm'
})

# 其他常见单位
OTHER_UNITS = frozenset({
    'mol', 'M', 'mM', 'μM', 'L', 'mL', 'μL', 'C', 'K', 'J', 'kJ',
    'eV', 'V', 'mV', 'A', 'W', 'Hz', 'kHz', 'MHz', 'GHz', 'Pa', 'kPa',
    'wt', 'vol', 'g', 'kg', 'mg'
})

# 所有单位集合
ALL_UNITS = AREA_VOLUME_UNITS | RATE_UNITS | OTHER_UNITS

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

# 预编译正则表达式（性能优化）
RE_ELEMENT_NUMBER = re.compile(r'\b([A-Z][a-z]?)(\d{1,2})(?![a-zA-Z0-9])')
RE_SCIENTIFIC_NOTATION = re.compile(r'(10)([-+−])(\d+)')
RE_MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
RE_PURE_NUMBERS = re.compile(r'^[-−]?[\d\s]+$')
RE_SINGLE_DIGIT = re.compile(r'^[1-9]$')


# ========== 工具函数 ==========

def convert_to_subscript(text: str) -> str:
    """将文本转换为下标形式"""
    return ''.join(SCRIPT_MAPS.subscript.get(char, char) for char in text)


def convert_to_superscript(text: str) -> str:
    """将文本转换为上标形式"""
    return ''.join(SCRIPT_MAPS.superscript.get(char, char) for char in text)


def normalize_special_chars(text: str) -> str:
    """规范化特殊字符"""
    for old, new in SPECIAL_CHAR_MAP.items():
        text = text.replace(old, new)
    return text


def is_subscript_context(context: str) -> Tuple[bool, bool]:
    """
    根据上下文判断应该是下标还是上标
    
    Returns:
        Tuple[bool, bool]: (is_subscript, is_superscript)
    """
    if not context:
        return (False, False)
    
    context_stripped = context.rstrip()
    
    # 1. 面积/体积单位后面跟正数 → 上标 (cm², mm³)
    for unit in AREA_VOLUME_UNITS:
        if context_stripped.endswith(unit):
            return (False, True)
    
    # 2. 时间/速率单位后面跟负数 → 上标 (min⁻¹, s⁻¹)
    for unit in RATE_UNITS:
        if context_stripped.endswith(unit):
            return (False, True)
    
    # 3. 科学计数法 10⁻⁵, 10⁺³
    if context_stripped.endswith('10'):
        return (False, True)
    
    # 4. 化学元素后面跟数字 → 下标 (H₂O, Fe₂)
    for elem in CHEMICAL_ELEMENTS:
        if context_stripped.endswith(elem):
            return (True, False)
    
    # 5. 常见化学基团后面跟数字 → 下标 (NH₃, CO₂)
    chem_groups = ['NH', 'NO', 'CO', 'SO', 'PO', 'OH', 'CH', 'FeN', 'TM']
    for group in chem_groups:
        if context_stripped.endswith(group):
            return (True, False)
    
    # 6. 右括号后面跟数字（化学式如 Zn(NO₃)₂）
    if context_stripped.endswith(')'):
        return (True, False)
    
    return (False, False)


# ========== PDF 转换器类 ==========

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
        sizes = [round(c.get('size', 12), 1) for c in chars if c.get('size')]
        if sizes:
            size_counter = Counter(sizes)
            self.main_font_size = size_counter.most_common(1)[0][0]
    
    def _organize_chars_to_lines(self, chars: List[Dict], table_bboxes: List[Tuple]) -> List[List[Dict]]:
        """将字符组织成行，同时标记下标/上标"""
        if not chars:
            return []
        
        # 找出主字体大小
        sizes = [c.get('size', 12) for c in chars]
        size_counter = Counter([round(s, 1) for s in sizes])
        main_size = size_counter.most_common(1)[0][0] if size_counter else 12
        
        # 过滤掉表格内的字符
        non_table_chars = [
            char for char in chars
            if not self._is_char_in_table(char, table_bboxes)
        ]
        
        # 按位置排序
        sorted_chars = sorted(non_table_chars, key=lambda c: (c.get('top', 0), c.get('x0', 0)))
        
        # 行分组
        lines = self._group_chars_into_lines(sorted_chars, main_size)
        
        # 标记下标/上标
        self._mark_subscripts_superscripts(lines, main_size)
        
        return lines
    
    def _is_char_in_table(self, char: Dict, table_bboxes: List[Tuple]) -> bool:
        """检查字符是否在表格内"""
        char_top = char.get('top', 0)
        char_x0 = char.get('x0', 0)
        for bbox in table_bboxes:
            if bbox[0] <= char_x0 <= bbox[2] and bbox[1] <= char_top <= bbox[3]:
                return True
        return False
    
    def _group_chars_into_lines(self, chars: List[Dict], main_size: float) -> List[List[Dict]]:
        """将字符分组到行中"""
        lines = []
        current_line = []
        current_baseline = None
        
        tolerance = max(2, main_size * 0.2)
        
        for char in chars:
            char_top = char.get('top', 0)
            char_size = char.get('size', 12)
            size_ratio = char_size / main_size if main_size > 0 else 1
            
            # 判断是否是小字体
            is_small_font = size_ratio < 0.85
            
            if current_baseline is None:
                current_line = [char.copy()]
                current_baseline = char_top
            else:
                should_join = False
                
                if is_small_font:
                    # 小字体：检查是否紧接在前一个字符后面
                    if current_line:
                        last_char = current_line[-1]
                        gap = char.get('x0', 0) - last_char.get('x1', 0)
                        max_gap = max(last_char.get('size', 12), char_size) * 0.5
                        vertical_range = main_size * 1.2
                        
                        if gap <= max_gap and abs(char_top - current_baseline) <= vertical_range:
                            should_join = True
                else:
                    # 正常字体：使用标准容差判断
                    if abs(char_top - current_baseline) <= tolerance:
                        should_join = True
                        current_baseline = char_top
                
                if should_join:
                    current_line.append(char.copy())
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = [char.copy()]
                    current_baseline = char_top
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _mark_subscripts_superscripts(self, lines: List[List[Dict]], main_size: float) -> None:
        """标记下标和上标字符"""
        for line in lines:
            if not line:
                continue
            
            # 计算行的基准线位置
            tops = [c.get('top', 0) for c in line]
            top_counter = Counter([round(t, 0) for t in tops])
            baseline_top = top_counter.most_common(1)[0][0] if top_counter else 0
            
            # 按x坐标排序处理
            sorted_line = sorted(enumerate(line), key=lambda x: x[1].get('x0', 0))
            
            for orig_idx, char in sorted_line:
                char_text = char.get('text', '')
                char_size = char.get('size', 12)
                char_top = char.get('top', 0)
                
                size_ratio = char_size / main_size if main_size > 0 else 1
                
                if size_ratio < 0.85:
                    # 获取前面的上下文
                    context = self._get_context_before(line, orig_idx)
                    
                    # 使用上下文判断
                    is_sub, is_sup = is_subscript_context(context)
                    
                    if not is_sub and not is_sup:
                        # 上下文无法确定，使用位置判断
                        position_diff = char_top - baseline_top
                        
                        if position_diff > 1.0:
                            is_sub, is_sup = True, False
                        elif position_diff < -1.0:
                            is_sub, is_sup = False, True
                        else:
                            # 默认为下标
                            is_sub, is_sup = True, False
                    
                    char['is_subscript'] = is_sub
                    char['is_superscript'] = is_sup
    
    def _get_context_before(self, line: List[Dict], idx: int, max_chars: int = 15) -> str:
        """获取当前字符前面的上下文文本"""
        context = []
        for i in range(max(0, idx - max_chars), idx):
            text = line[i].get('text', '')
            if text and not line[i].get('is_subscript') and not line[i].get('is_superscript'):
                context.append(text)
        return ''.join(context)
    
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
        
        sorted_chars = sorted(line, key=lambda c: c.get('x0', 0))
        
        result = []
        prev_char = None
        current_subscript = ""
        current_superscript = ""
        
        for char in sorted_chars:
            text = char.get('text', '')
            text = normalize_special_chars(text)
            
            # 处理空格
            if prev_char:
                gap = char.get('x0', 0) - prev_char.get('x1', 0)
                prev_size = prev_char.get('size', 12)
                if gap > prev_size * 0.3:
                    if current_subscript:
                        result.append(convert_to_subscript(current_subscript))
                        current_subscript = ""
                    if current_superscript:
                        result.append(convert_to_superscript(current_superscript))
                        current_superscript = ""
                    result.append(' ')
            
            # 处理下标/上标
            is_sub = char.get('is_subscript', False)
            is_sup = char.get('is_superscript', False)
            
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
                if current_subscript:
                    result.append(convert_to_subscript(current_subscript))
                    current_subscript = ""
                if current_superscript:
                    result.append(convert_to_superscript(current_superscript))
                    current_superscript = ""
                result.append(text)
            
            prev_char = char
        
        # 处理末尾
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
            
            result = []
            max_cols = max(len(row) for row in table_data)
            
            for i, row in enumerate(table_data):
                cells = []
                for cell in row:
                    cell_text = str(cell) if cell else ''
                    cell_text = normalize_special_chars(cell_text)
                    cell_text = self._post_process_text(cell_text)
                    cells.append(cell_text.strip())
                
                while len(cells) < max_cols:
                    cells.append('')
                
                result.append('| ' + ' | '.join(cells) + ' |')
                
                if i == 0:
                    result.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
            
            return '\n'.join(result)
            
        except Exception:
            return ""
    
    def _post_process_text(self, text: str) -> str:
        """后处理文本"""
        # 处理科学计数法
        text = self._process_scientific_notation(text)
        return text
    
    def _process_scientific_notation(self, text: str) -> str:
        """处理科学计数法"""
        def replace_exp(match):
            sign = match.group(2)
            exp = match.group(3)
            return match.group(1) + convert_to_superscript(sign + exp)
        
        return RE_SCIENTIFIC_NOTATION.sub(replace_exp, text)


# ========== 后处理函数 ==========

def post_process_text(text: str) -> str:
    """
    后处理文本 - 修复常见的转换问题
    """
    # 1. 合并被分割的下标/上标行
    text = merge_broken_script_lines(text)
    
    # 2. 修复化学式中的数字下标
    text = fix_chemical_formulas(text)
    
    # 3. 修复单位中的上标
    text = fix_unit_superscripts(text)
    
    # 4. 清理多余的空行
    text = RE_MULTIPLE_NEWLINES.sub('\n\n', text)
    
    return text.strip()


def merge_broken_script_lines(text: str) -> str:
    """
    合并被错误分割的下标/上标行
    
    例如:
    "Fe @NG DAC." + "₂" → "Fe₂@NG DAC."
    "NH  Enabled" + "₂₃" → "NH₃ Enabled"
    """
    lines = text.split('\n')
    merged_lines = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].rstrip()
        
        # 检查下一行是否是纯下标/上标字符
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # 检测纯下标/上标行（只包含下标或上标字符）
            if next_line and is_pure_script_chars(next_line):
                # 合并到当前行
                # 找到当前行中应该插入下标的位置
                merged_line = insert_script_at_position(current_line, next_line)
                merged_lines.append(merged_line)
                i += 2
                continue
        
        merged_lines.append(current_line)
        i += 1
    
    return '\n'.join(merged_lines)


def is_pure_script_chars(text: str) -> bool:
    """检查文本是否只包含下标或上标字符"""
    if not text:
        return False
    
    # 下标字符范围
    subscript_chars = set('₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ')
    # 上标字符范围
    superscript_chars = set('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ')
    
    script_chars = subscript_chars | superscript_chars
    
    # 检查是否所有字符都是下标/上标
    return all(c in script_chars or c.isspace() for c in text)


def insert_script_at_position(line: str, script: str) -> str:
    """
    将下标/上标插入到行中正确的位置
    
    规则:
    1. 如果行以 "@NG" 结尾，下标插入到 @ 前面的元素后
    2. 如果行中有 "NH  rather" 模式，分配下标到空格前的元素
    3. 如果行以元素结尾，插入下标
    4. 否则追加到行末尾
    """
    script = script.strip()
    if not script:
        return line
    
    # 分配多个下标字符
    scripts = list(script)
    script_idx = 0
    
    def get_next_script():
        nonlocal script_idx
        if script_idx < len(scripts):
            s = scripts[script_idx]
            script_idx += 1
            return s
        return ''
    
    # 模式1: "Fe @NG DAC" + "₂" → "Fe₂@NG DAC"
    match = re.search(r'([A-Z][a-z]?)\s+@NG', line)
    if match:
        elem = match.group(1)
        s = get_next_script()
        return line.replace(f'{elem} @NG', f'{elem}{s}@NG', 1)
    
    # 模式2: "NH   rather  than  N" + "₂₃" → "NH₃ rather than N₂"
    # 检测行中有多个空格分隔的元素模式
    match = re.search(r'([A-Z][a-z]?)\s{2,}(rather|than|over|and|or)', line, re.IGNORECASE)
    if match:
        elem1 = match.group(1)
        s1 = get_next_script()
        result = re.sub(rf'{elem1}\s{{2,}}', f'{elem1}{s1} ', line, count=1)
        
        # 检查是否有第二个元素需要分配下标
        match2 = re.search(r'(than|over|and|or)\s+([A-Z][a-z]?)(\s*$|\s+[a-z])', result, re.IGNORECASE)
        if match2 and script_idx < len(scripts):
            elem2 = match2.group(2)
            s2 = get_next_script()
            result = re.sub(rf'(than|over|and|or)\s+{elem2}', rf'\1 {elem2}{s2}', result, count=1, flags=re.IGNORECASE)
        
        return result
    
    # 模式3: "N O" + "₂" → "N₂O"
    match = re.search(r'\b([A-Z][a-z]?)\s+([A-Z][a-z]?)\s*$', line)
    if match:
        elem1 = match.group(1)
        elem2 = match.group(2)
        s = get_next_script()
        return line.replace(f'{elem1} {elem2}', f'{elem1}{s}{elem2}', 1)
    
    # 模式4: 以元素结尾的行
    match = re.search(r'\b([A-Z][a-z]?)\s*$', line)
    if match:
        elem = match.group(1)
        s = get_next_script()
        return line[:match.end(1)] + s + line[match.end(1):]
    
    # 模式5: 行中有 "N synthesis" 这样的模式
    match = re.search(r'\b([A-Z][a-z]?)\s+(synthesis|production|formation|reaction)', line, re.IGNORECASE)
    if match:
        elem = match.group(1)
        s = get_next_script()
        return line.replace(f'{elem} {match.group(2)}', f'{elem}{s} {match.group(2)}', 1)
    
    # 模式6: "N   due" + "₂" → "N₂ due" (元素后面有多个空格)
    match = re.search(r'\b([A-Z][a-z]?)\s{2,}(due|than|over|from|in|on|at)', line, re.IGNORECASE)
    if match:
        elem = match.group(1)
        s = get_next_script()
        return re.sub(rf'\b{elem}\s{{2,}}{match.group(2)}', f'{elem}{s} {match.group(2)}', line, count=1, flags=re.IGNORECASE)
    
    # 模式7: 行以单个元素结尾，后面有多个空格
    match = re.search(r'\b([A-Z][a-z]?)\s{2,}$', line)
    if match:
        elem = match.group(1)
        s = get_next_script()
        return re.sub(rf'{elem}\s{{2,}}$', f'{elem}{s}', line)
    
    # 默认: 追加到末尾
    return line + ''.join(scripts[script_idx:])


def fix_chemical_formulas(text: str) -> str:
    """修复化学式中的数字"""
    def replace_formula(match):
        elem = match.group(1)
        num = match.group(2)
        return elem + convert_to_subscript(num)
    
    # 匹配元素符号后跟数字
    return RE_ELEMENT_NUMBER.sub(replace_formula, text)


def fix_unit_superscripts(text: str) -> str:
    """修复单位中的上标"""
    # 修复面积单位: cm2 → cm², mm2 → mm²
    for unit in AREA_VOLUME_UNITS:
        pattern = rf'({unit})(\d)(?![a-zA-Z0-9])'
        text = re.sub(pattern, lambda m: m.group(1) + convert_to_superscript(m.group(2)), text)
    
    # 修复速率单位负指数: min-1 → min⁻¹
    for unit in RATE_UNITS:
        pattern = rf'({unit})\s*[-−]?(\d)(?![a-zA-Z0-9])'
        text = re.sub(pattern, lambda m: m.group(1) + convert_to_superscript('⁻' + m.group(2) if m.group(0).count('-') or m.group(0).count('−') else m.group(2)), text)
    
    return text


def smart_format_text(text: str) -> str:
    """
    智能格式化文本
    """
    # 后处理
    text = post_process_text(text)
    
    lines = text.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            if result and result[-1] != '':
                result.append('')
        else:
            # 检测可能的标题
            if _is_likely_heading(stripped):
                if result and result[-1] != '':
                    result.append('')
                if not stripped.startswith('#'):
                    stripped = '## ' + stripped
                result.append(stripped)
                result.append('')
            else:
                result.append(stripped)
    
    final_text = '\n'.join(result)
    return RE_MULTIPLE_NEWLINES.sub('\n\n', final_text).strip()


def _is_likely_heading(line: str) -> bool:
    """判断是否可能是标题"""
    if not line or line.startswith('#'):
        return False
    
    section_patterns = [
        r'^S-\d+$',
        r'^\d+\.\s+[A-Z]',
        r'^(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|References)',
        r'^(Experimental|Theoretical|Computational)\s+\w+',
        r'^(Table|Figure|Fig\.)\s+\d+',
        r'^Synthesis\s+of',
        r'^Characterizations?$',
    ]
    
    for pattern in section_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    
    if len(line) < 50 and line.isupper() and len(line.split()) <= 5:
        return True
    
    return False


def convert_pdf_to_markdown(pdf_path: str, output_dir: str, overwrite: bool = False) -> dict:
    """
    将 PDF 文件转换为 Markdown 格式，保留化学式和科学符号格式。
    
    该工具用于从学术论文 PDF 中提取文本内容并转换为结构化的 Markdown 格式。
    支持保留化学式的上下标（如 H₂O、Fe²⁺）、科学计数法以及表格结构。
    
    Use this tool when you need to:
    - Extract text content from scientific paper PDF files
    - Convert PDF documents to Markdown format for further processing
    - Preserve chemical formulas with proper subscript/superscript formatting
    - Process academic papers containing tables and equations
    
    Args:
        pdf_path: PDF 文件的完整路径，必须是有效的 .pdf 文件路径
        output_dir: 输出 Markdown 文件的目录路径，如果不存在会自动创建
        overwrite: 是否覆盖已存在的同名 Markdown 文件，默认为 False（跳过已存在文件）
        
    Returns:
        dict: 包含转换结果的字典，结构如下：
            - success (bool): 转换是否成功
            - input_file (str): 输入的 PDF 文件路径
            - output_file (str): 生成的 Markdown 文件路径
            - char_count (int): 提取的字符总数
            - pages (int): PDF 总页数
            - error (str|None): 错误信息，成功时为 None
    
    Example:
        >>> result = convert_pdf_to_markdown("paper.pdf", "markdown_docs")
        >>> print(result["output_file"])  # "markdown_docs/paper.md"
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
        pdf_name = Path(pdf_path).stem
        output_file = Path(output_dir) / f"{pdf_name}.md"
        
        if output_file.exists() and not overwrite:
            result["output_file"] = str(output_file)
            result["error"] = "文件已存在，跳过（使用 --overwrite 覆盖）"
            return result
        
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
        "[dim]优化版本 - 精确保留下标/上标格式[/dim]",
        border_style="cyan"
    ))
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]输出目录已创建/确认: {output_dir}[/green]")
    
    # 确定要处理的 PDF 文件列表
    pdf_files = []
    
    if args.pdf_file:
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
    
    if stats["files"]:
        console.print("\n[bold]生成的 Markdown 文件:[/bold]")
        for f in stats["files"]:
            console.print(f"  - {f['output']}: {f['chars']} 字符, {f['pages']} 页")
    
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
