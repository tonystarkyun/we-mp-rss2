@echo off
chcp 65001 > nul
SETLOCAL

echo ================================================
echo     WeRSS 完整安装包构建工具
echo ================================================
echo.

:: 第一步：构建独立程序
echo [第一步] 构建独立应用程序...
call build-standalone.bat
if %ERRORLEVEL% neq 0 (
    echo 构建失败，终止安装包制作
    pause
    exit /b 1
)

:: 检查Inno Setup
echo.
echo [第二步] 检查Inno Setup编译器...
set "INNO_PATH="
for %%i in ("C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "C:\Program Files\Inno Setup 6\ISCC.exe") do (
    if exist "%%i" set "INNO_PATH=%%i"
)

if "%INNO_PATH%"=="" (
    echo 警告：未找到Inno Setup编译器
    echo 请从以下地址下载安装：https://jrsoftware.org/isinfo.php
    echo.
    echo 将跳过安装包制作，您可以直接使用 dist-standalone 目录中的程序
    pause
    exit /b 0
)

:: 创建许可证文件
echo [第三步] 准备安装文件...
if not exist "LICENSE.txt" (
    echo 创建许可证文件...
    (
    echo MIT License
    echo.
    echo Permission is hereby granted, free of charge, to any person obtaining a copy
    echo of this software and associated documentation files ^(the "Software"^), to deal
    echo in the Software without restriction, including without limitation the rights
    echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    echo copies of the Software, and to permit persons to whom the Software is
    echo furnished to do so, subject to the following conditions:
    echo.
    echo The above copyright notice and this permission notice shall be included in all
    echo copies or substantial portions of the Software.
    ) > LICENSE.txt
)

:: 编译安装程序
echo [第四步] 编译安装程序...
"%INNO_PATH%" "installer.iss"
if %ERRORLEVEL% neq 0 (
    echo 安装程序编译失败
    pause
    exit /b 1
)

:: 完成
echo.
echo ================================================
echo ✅ WeRSS 完整安装包构建完成！
echo.
echo 📁 文件位置：
echo    独立程序：dist-standalone\WeRSS-Standalone.exe
echo    安装包：  installer-output\WeRSS-Setup-v1.0.0.exe
echo.
echo 📦 文件信息：
if exist "dist-standalone\WeRSS-Standalone.exe" (
    for %%F in ("dist-standalone\WeRSS-Standalone.exe") do echo    独立程序：%%~zF 字节
)
if exist "installer-output\WeRSS-Setup-v1.0.0.exe" (
    for %%F in ("installer-output\WeRSS-Setup-v1.0.0.exe") do echo    安装包：  %%~zF 字节
)
echo.
echo 🚀 使用说明：
echo    方式1：直接运行独立程序 WeRSS-Standalone.exe
echo    方式2：使用安装包 WeRSS-Setup-v1.0.0.exe 进行标准安装
echo.
echo ================================================
pause