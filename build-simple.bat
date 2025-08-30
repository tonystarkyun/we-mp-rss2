@echo off
chcp 65001 > nul
SETLOCAL

echo ================================================
echo       WeRSS 单用户版本快速打包工具
echo ================================================
echo.

:: 设置变量
set "DIST_DIR=dist-standalone"
set "APP_NAME=WeRSS-Standalone"

:: 清理旧构建
echo [1/4] 清理旧构建文件...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "build" rmdir /s /q "build" 
if exist "*.spec" del "*.spec" 2>nul

:: 构建前端
echo [2/4] 准备静态文件...
if exist "web_ui\package.json" (
    echo 发现前端项目，检查构建状态...
    if not exist "static\index.html" (
        echo 需要先构建前端，请运行: cd web_ui && npm run build
        pause
        exit /b 1
    )
)

:: 打包应用
echo [3/4] 打包应用程序...
pyinstaller ^
    --name="%APP_NAME%" ^
    --onefile ^
    --noconsole ^
    --distpath="%DIST_DIR%" ^
    --add-data="config.example.yaml;." ^
    --add-data="static;static" ^
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
    standalone_launcher.py

if %ERRORLEVEL% neq 0 (
    echo 打包失败！
    pause
    exit /b 1
)

:: 创建说明文件
echo [4/4] 创建使用说明...
(
echo WeRSS 单用户独立版本 v1.0.0
echo ===============================
echo.
echo 🚀 快速开始：
echo 1. 双击 %APP_NAME%.exe 启动程序
echo 2. 程序会自动打开浏览器访问管理界面  
echo 3. 默认登录账户：Administrator / admin@123
echo.
echo 📁 数据存储：
echo 程序数据保存在：%%USERPROFILE%%\WeRSS\
echo.
echo 💡 功能特色：
echo • 文献查询 - 学术RSS订阅管理
echo • 专利检索 - 专利信息聚合
echo • 行业动态 - 行业资讯跟踪  
echo • 智能更新 - 自动内容抓取
echo.
echo 🔧 注意事项：
echo • 首次启动需要几分钟初始化时间
echo • 请确保防火墙允许程序访问网络
echo • 如遇问题，删除数据目录重新启动
echo.
echo ⭐ 项目地址：https://github.com/your-repo
echo 🐛 问题反馈：https://github.com/your-repo/issues
) > "%DIST_DIR%\使用说明.txt"

:: 完成
echo.
echo ================================================
echo ✅ 打包完成！
echo.
echo 📦 输出位置：%DIST_DIR%\%APP_NAME%.exe
echo 📋 文件大小：
for %%F in ("%DIST_DIR%\%APP_NAME%.exe") do echo    %%~zF 字节
echo.
echo 🎯 测试方法：
echo    cd %DIST_DIR%
echo    %APP_NAME%.exe
echo.
echo ================================================
pause