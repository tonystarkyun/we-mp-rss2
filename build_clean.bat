@echo off
echo ========================================
echo      WeRSS 清理构建脚本
echo ========================================
echo.

echo 正在清理旧的构建文件...
call clean_build.bat

echo.
echo 开始构建WeRSS安装包版本...
pyinstaller WeRSS-Standalone.spec --clean --noconfirm --distpath dist-installer

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo          构建成功！
    echo ========================================
    echo 可执行文件位置: dist-installer\WeRSS-Standalone.exe
    echo 请使用Inno Setup编译 installer.iss 生成安装包
) else (
    echo.
    echo ========================================
    echo          构建失败！
    echo ========================================
    echo 请检查错误信息并重试
)

echo.
pause