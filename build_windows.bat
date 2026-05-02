@echo off
chcp 65001 >nul
echo ========================================
echo   Timer Video Generator - Windows 编译脚本
echo ========================================
echo.

:: 1. 克隆代码
if not exist timer_video_generator (
    echo [1/4] 克隆代码仓库...
    git clone https://github.com/gxg-uestc/timer_video_generator.git
    if errorlevel 1 (
        echo 错误：克隆失败，请检查网络连接和 GitHub 访问权限
        goto :error
    )
) else (
    echo [1/4] 代码目录已存在，跳过克隆
)

cd timer_video_generator

:: 2. 创建虚拟环境
if not exist venv (
    echo [2/4] 创建 Python 虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 错误：创建虚拟环境失败，请确保已安装 Python 3.8+
        echo 下载链接: https://www.python.org/downloads/
        goto :error
    )
) else (
    echo [2/4] 虚拟环境已存在，跳过创建
)

call venv\Scripts\activate.bat

:: 3. 安装依赖
echo [3/4] 安装依赖...
pip install pillow imageio-ffmpeg pyinstaller -q
if errorlevel 1 (
    echo 错误：依赖安装失败
    goto :error
)

:: 4. 编译 exe
echo [4/4] 编译 exe...
pyinstaller --onefile --console --name countdown_timer countdown_timer_win.py
if errorlevel 1 (
    echo 错误：编译失败
    goto :error
)

echo.
echo ========================================
echo   编译完成！
echo   exe 路径: dist\countdown_timer.exe
echo ========================================
echo.

:: 复制 ffmpeg.exe（如果存在）
if exist ffmpeg.exe (
    echo ffmpeg.exe 已就绪，请将其复制到 dist 目录与 exe 放在一起
) else (
    echo 提示：请从 https://ffmpeg.org/download.html 下载 ffmpeg.exe
    echo 并将其放在与 countdown_timer.exe 同一目录下
)

cd ..
pause
exit /b 0

:error
echo.
echo ========================================
echo   编译失败
echo ========================================
pause
exit /b 1
