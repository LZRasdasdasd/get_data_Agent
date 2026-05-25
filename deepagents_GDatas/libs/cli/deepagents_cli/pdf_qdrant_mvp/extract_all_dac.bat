@echo off
chcp 65001 >nul
echo ========================================
echo 从 Qdrant 所有集合中提取双原子催化剂数据
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 设置 Python 解释器和脚本路径
set PYTHON_EXE=..\..\..\..\..\.conda\python.exe
set PYTHON_SCRIPT=src\extract_all_collections_dac.py

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
echo   输出目录: queried_datas\
echo.

REM 询问是否继续
set /p CONFIRM="确认开始提取所有集合的双原子催化剂数据? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 用户取消操作
    pause
    exit /b 0
)

echo.
echo [开始提取]
echo.

REM 执行 Python 脚本
"%PYTHON_EXE%" "%PYTHON_SCRIPT%"

REM 检查执行结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [成功] 双原子催化剂数据提取完成
    echo ========================================
    echo.
    echo 提取结果已保存到 queried_datas\ 目录
    echo 请运行 extract_json_to_csv.bat 将结果转换为 CSV
) else (
    echo.
    echo ========================================
    echo [错误] 提取过程中出现错误，错误码: %ERRORLEVEL%
    echo ========================================
)

echo.
pause
