@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo 启动失败，请检查 Python 是否已安装
    pause
)
