@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo 文档批量转换工具 - 目录3001-4000
echo 支持 PDF / DOCX / DOC 格式
echo ========================================
echo.

".conda\python.exe" deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\pdf_to_markdown.py --input-dir "E:\数据集\512" --output-dir "markdown_output"
echo.
echo ========================================
echo 转换完成!
echo ========================================
echo.
pause
