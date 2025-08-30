@echo off
chcp 65001 > nul
SETLOCAL

:: WeRSS 单用户版本打包脚本
echo ================================================
echo           WeRSS 单用户版本打包工具
echo ================================================
echo.

:: 设置变量
set "VENV_DIR=venv"
set "BUILD_DIR=build-standalone" 
set "DIST_DIR=dist-standalone"
set "APP_NAME=WeRSS-Standalone"
set "VERSION=1.0.0"

:: 清理旧的构建文件
echo [1/6] 清理旧构建文件...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "*.spec" del "*.spec" 2>nul

:: 创建目录
mkdir "%BUILD_DIR%" 2>nul
mkdir "%DIST_DIR%" 2>nul

:: 检查虚拟环境
echo [2/6] 检查Python环境...
if not exist "%VENV_DIR%" (
    echo 错误：未找到虚拟环境，请先运行 build.bat 创建环境
    pause
    exit /b 1
)

:: 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"

:: 安装额外依赖
echo [3/6] 安装打包依赖...
pip install pyinstaller requests winshell --quiet

:: 构建前端（如果需要）
echo [4/6] 构建前端资源...
if exist "web_ui\package.json" (
    cd web_ui
    if exist "node_modules" (
        call npm run build
    ) else (
        echo 前端依赖未安装，跳过前端构建
    )
    cd ..
)

:: 使用PyInstaller打包
echo [5/6] 打包应用程序...
pyinstaller ^
    --name="%APP_NAME%" ^
    --onefile ^
    --noconsole ^
    --distpath="%DIST_DIR%" ^
    --workpath="%BUILD_DIR%" ^
    --add-data="config.example.yaml;." ^
    --add-data="static;static" ^
    --add-data="core;core" ^
    --add-data="apis;apis" ^
    --add-data="jobs;jobs" ^
    --add-data="driver;driver" ^
    --hidden-import="apis" ^
    --hidden-import="core" ^
    --hidden-import="core.models" ^
    --hidden-import="jobs" ^
    --hidden-import="pydantic" ^
    --hidden-import="fastapi" ^
    --hidden-import="uvicorn" ^
    --hidden-import="sqlite3" ^
    --hidden-import="bcrypt" ^
    --hidden-import="jwt" ^
    --exclude-module="tkinter" ^
    --exclude-module="matplotlib" ^
    --exclude-module="numpy" ^
    standalone_launcher.py

if %ERRORLEVEL% neq 0 (
    echo 错误：打包失败
    pause
    exit /b 1
)

:: 复制必要文件到发布目录
echo [6/6] 准备发布文件...
copy "README.md" "%DIST_DIR%\" 2>nul
copy "用户系统方案评估.md" "%DIST_DIR%\" 2>nul

:: 创建安装说明
echo 创建安装说明文件...
(
echo WeRSS 单用户独立版本
echo ===================
echo.
echo 安装说明：
echo 1. 双击 %APP_NAME%.exe 启动程序
echo 2. 程序会自动创建工作目录并打开浏览器
echo 3. 首次运行请使用默认账户登录：
echo    - 用户名：Administrator
echo    - 密码：admin@123
echo.
echo 注意事项：
echo - 程序数据保存在 %%USERPROFILE%%\WeRSS\ 目录下
echo - 如需卸载，删除该目录和本程序即可
echo - 支持Windows 7及以上系统
echo.
echo 技术支持：
echo - 项目主页：https://github.com/your-repo
echo - 版本：%VERSION%
echo - 构建时间：%date% %time%
) > "%DIST_DIR%\安装说明.txt"

:: 清理临时文件
echo 清理临时文件...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "__pycache__" rmdir /s /q "__pycache__"

:: 完成
echo.
echo ================================================
echo ✅ 单用户版本打包完成！
echo.
echo 📁 输出目录：%DIST_DIR%
echo 📦 主程序：%APP_NAME%.exe
echo 📋 文件大小：
for %%F in ("%DIST_DIR%\%APP_NAME%.exe") do echo    %%~zF 字节 ^(%%~F^)
echo.
echo 🚀 使用方法：
echo    双击 %APP_NAME%.exe 即可启动
echo.
echo ================================================
pause