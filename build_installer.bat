@echo off
chcp 65001 >nul
echo 正在构建 WeRSS 安装包...

:: 清理旧的构建文件
if exist "dist-complete" rmdir /s /q "dist-complete"
if exist "dist-installer" rmdir /s /q "dist-installer"
if exist "build" rmdir /s /q "build"

:: 创建目录
mkdir "dist-complete"
mkdir "dist-installer"

:: 构建前端
echo 正在构建前端...
cd web_ui
call yarn build
if %ERRORLEVEL% neq 0 (
    echo 前端构建失败！
    pause
    exit /b 1
)
cd ..

:: 使用 PyInstaller 构建可执行文件
echo 正在构建可执行文件...
pyinstaller WeRSS-Standalone.spec --clean --noconfirm
if %ERRORLEVEL% neq 0 (
    echo PyInstaller 构建失败！
    pause
    exit /b 1
)

:: 复制可执行文件到 dist-complete
copy "dist\WeRSS-Standalone.exe" "dist-complete\"

:: 使用 Inno Setup 构建安装包
echo 正在构建安装包...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
if %ERRORLEVEL% neq 0 (
    echo Inno Setup 构建失败！请确保已安装 Inno Setup 6
    pause
    exit /b 1
)

echo 构建完成！
echo 可执行文件位于: dist-complete\WeRSS-Standalone.exe
echo 安装包位于: dist-installer\WeRSS-Setup.exe

pause