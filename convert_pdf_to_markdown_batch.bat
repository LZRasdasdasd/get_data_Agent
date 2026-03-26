@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 设置PDF目录路径
set "PDF_DIR=D:\数据集\论文分段存储0\pdf4001-5000"

:: 设置输出目录(将在当前工作目录下创建)
set "OUTPUT_DIR=markdown_output_4001-5000"

:: 设置脚本路径
set "SCRIPT_PATH=deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\pdf_to_markdown.py"

echo ========================================
echo PDF批量转换为Markdown工具
echo ========================================
echo.
echo PDF源目录: %PDF_DIR%
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

:: 检查PDF目录是否存在
if not exist "%PDF_DIR%" (
    echo [错误] PDF目录不存在: %PDF_DIR%
    pause
    exit /b 1
)

:: 检查PDF目录下是否有PDF文件
set "pdf_count=0"
for %%f in ("%PDF_DIR%\*.pdf") do (
    set /a "pdf_count+=1"
)

if %pdf_count% equ 0 (
    echo [警告] 目录中没有找到PDF文件: %PDF_DIR%
    pause
    exit /b 1
)

echo [信息] 找到 %pdf_count% 个PDF文件
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
    echo [提示] 正在安装所需的依赖项(pdfplumber、rich等)...
    pip install pdfplumber rich > nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 依赖项安装失败,请手动安装: pip install pdfplumber rich
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
echo 开始批量转换PDF文件...
echo ========================================
echo.

:: 调用Python脚本进行批量转换
python "%SCRIPT_PATH%" --pdf-dir "%PDF_DIR%" --output-dir "%OUTPUT_DIR%" --overwrite

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
