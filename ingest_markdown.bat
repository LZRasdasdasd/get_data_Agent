@echo off
chcp 65001 >nul
echo ========================================
echo 将 markdown_output_3001-4000 中的 Markdown 文件存入 Qdrant 数据库
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 设置 Python 脚本路径
set PYTHON_SCRIPT=deepagents_GDatas\libs\cli\deepagents_cli\pdf_qdrant_mvp\src\ingest_markdown.py
set MARKDOWN_DIR=markdown_output

REM 检查 Python 脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo [错误] 找不到 Python 脚本: %PYTHON_SCRIPT%
    echo 请确保 deepagents_GDatas 项目目录结构正确
    pause
    exit /b 1
)

REM 检查 Markdown 目录是否存在
if not exist "%MARKDOWN_DIR%" (
    echo [错误] 找不到 Markdown 目录: %MARKDOWN_DIR%
    echo 请确保 markdown_output 目录存在
    pause
    exit /b 1
)

REM 显示运行配置
echo [配置信息]
echo   Python 脚本: %PYTHON_SCRIPT%
echo   Markdown 目录: %MARKDOWN_DIR%
echo   块大小: 1000 字符
echo   块重叠: 200 字符
echo.

REM 询问是否继续
set /p CONFIRM="确认开始处理? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 用户取消操作
    pause
    exit /b 0
)

echo.
echo [开始处理]
echo.

REM 执行 Python 脚本
".conda\python.exe" "%PYTHON_SCRIPT%" --md-dir "%MARKDOWN_DIR%" --chunk-size 1000 --chunk-overlap 200 --no-title

REM 检查执行结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [成功] Markdown 文件已成功存入数据库
    echo ========================================
) else (
    echo.
    echo ========================================
    echo [错误] 处理过程中出现错误，错误码: %ERRORLEVEL%
    echo ========================================
)

echo.
pause
