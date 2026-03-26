@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo PDF批量转换工具 - 目录3001-4000
echo ========================================
echo.

python deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\pdf_to_markdown.py --pdf-dir "D:\数据集\论文分段存储0\pdf3001-4000" --output-dir "markdown_output_3001-4000"

echo.
echo ========================================
echo 转换完成!
echo ========================================
echo.
pause
