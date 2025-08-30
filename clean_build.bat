@echo off
echo ========================================
echo       WeRSS 构建文件清理工具
echo ========================================
echo.

echo [1/6] 清理PyInstaller构建文件...
if exist build rmdir /s /q build && echo ✓ 已删除build目录 || echo - build目录不存在

echo [2/6] 清理多余的输出目录...
if exist dist-test rmdir /s /q dist-test && echo ✓ 已删除dist-test目录
if exist dist-console rmdir /s /q dist-console && echo ✓ 已删除dist-console目录  
if exist dist-complete rmdir /s /q dist-complete && echo ✓ 已删除dist-complete目录

echo [3/6] 清理PyInstaller系统缓存...
if exist "%LOCALAPPDATA%\pyinstaller" (
    rmdir /s /q "%LOCALAPPDATA%\pyinstaller" && echo ✓ 已清理PyInstaller缓存
) else (
    echo - PyInstaller缓存不存在
)

echo [4/6] 清理Python字节码缓存...
for /r . %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i" >nul 2>&1
echo ✓ 已清理Python缓存目录

echo [5/6] 清理临时文件...
if exist *.pyc del /s /q *.pyc >nul 2>&1 && echo ✓ 已删除.pyc文件
if exist nul del nul && echo ✓ 已删除临时文件

echo [6/6] 清理yarn/npm缓存...
if exist web_ui\node_modules (
    echo - 发现node_modules目录 (可手动删除以释放更多空间)
)

echo.
echo ========================================
echo           清理完成！
echo ========================================
echo 建议每次构建前运行此脚本以释放磁盘空间。
echo.
pause