@echo off
chcp 65001 >nul
echo ========================================
echo 将提取的 JSON 数据转换为 CSV 表格
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 设置 Python 解释器和脚本路径
set PYTHON_EXE=..\..\..\..\..\.conda\python.exe
set PYTHON_SCRIPT=src\extract_json_to_excel.py

REM 检查 Python 脚本是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo [错误] 找不到 Python 脚本: %PYTHON_SCRIPT%
    echo 请确保当前目录为 pdf_qdrant_mvp\
    pause
    exit /b 1
)

REM 显示运行配置
echo [配置信息]
echo   Python 脚本: %PYTHON_SCRIPT%
echo   输入目录: queried_datas\
echo   输出目录: excel_datas\
echo   输出文件: synthesis_data_updated.csv
echo.

REM 询问是否继续
set /p CONFIRM="确认开始转换 JSON 到 CSV? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 用户取消操作
    pause
    exit /b 0
)

echo.
echo [开始转换]
echo.

REM 执行 Python 脚本
"%PYTHON_EXE%" "%PYTHON_SCRIPT%"

REM 检查执行结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [成功] JSON 数据已成功转换为 CSV
    echo ========================================
    echo.
    echo CSV 文件已保存到 excel_datas\synthesis_data_updated.csv
) else (
    echo.
    echo ========================================
    echo [错误] 转换过程中出现错误，错误码: %ERRORLEVEL%
    echo ========================================
)

echo.
pause
