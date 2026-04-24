@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 设置文档目录路径（支持 PDF / DOCX / DOC）
set "DOC_DIR=E:\418\新建文件夹"

:: 设置输出目录(将在当前工作目录下创建)
set "OUTPUT_DIR=markdown_output"

:: 设置脚本路径
set "SCRIPT_PATH=deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\pdf_to_markdown.py"

echo ========================================
echo 文档批量转换为Markdown工具
echo 支持 PDF / DOCX / DOC 格式
echo ========================================
echo.
echo 文档源目录: %DOC_DIR%
echo 输出目录: %OUTPUT_DIR%
echo 脚本路径: %SCRIPT_PATH%
echo.

:: 检查Python是否可用
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python,请先安装Python并添加到PATH环境变量中
    pause
    exit /b 1
)

:: 检查文档目录是否存在
if not exist "%DOC_DIR%" (
    echo [错误] 文档目录不存在: %DOC_DIR%
    pause
    exit /b 1
)

:: 检查文档目录下是否有支持的文档文件（PDF、DOCX、DOC）
set "doc_count=0"
for %%f in ("%DOC_DIR%\*.pdf") do (
    set /a "doc_count+=1"
)
for %%f in ("%DOC_DIR%\*.docx") do (
    set /a "doc_count+=1"
)
for %%f in ("%DOC_DIR%\*.doc") do (
    set /a "doc_count+=1"
)

if %doc_count% equ 0 (
    echo [警告] 目录中没有找到支持的文档文件: %DOC_DIR%
    echo [提示] 支持的格式: .pdf, .docx, .doc
    pause
    exit /b 1
)

echo [信息] 找到 %doc_count% 个文档文件（PDF + DOCX + DOC）
echo.

:: 检查脚本文件是否存在
if not exist "%SCRIPT_PATH%" (
    echo [错误] 脚本文件不存在: %SCRIPT_PATH%
    pause
    exit /b 1
)

:: 检查并安装所需的依赖项
echo [信息] 检查Python依赖项...
python -c "import pdfplumber" > nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装所需的依赖项(pdfplumber、rich、python-docx等)...
    pip install pdfplumber rich python-docx > nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 依赖项安装失败,请手动安装: pip install pdfplumber rich python-docx
        pause
        exit /b 1
    )
    echo [成功] 依赖项安装完成
) else (
    echo [成功] 所需依赖项已安装
)
echo.

:: 开始转换
echo ========================================
echo 开始批量转换文档文件...
echo ========================================
echo.

:: 调用Python脚本进行批量转换（使用 --input-dir 参数以支持所有格式）
python "%SCRIPT_PATH%" --input-dir "%DOC_DIR%" --output-dir "%OUTPUT_DIR%" --overwrite

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [成功] 批量转换完成!
    echo ========================================
    echo.
    echo Markdown文件已保存到: %OUTPUT_DIR%
    echo.
) else (
    echo.
    echo ========================================
    echo [失败] 批量转换过程中出现错误
    echo ========================================
    echo.
)

pause
