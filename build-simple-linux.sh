#!/bin/bash

# WeRSS Linux 简化构建脚本
# 适用于无法构建前端或遇到依赖问题的情况

set -e

echo "=============================="
echo "WeRSS Linux 简化构建脚本"
echo "=============================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "当前工作目录: $(pwd)"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 安装 PyInstaller
echo "安装 PyInstaller..."
pip3 install pyinstaller

# 清理之前的构建
echo "清理之前的构建文件..."
rm -rf dist build 2>/dev/null || true

# 使用简化的 spec 文件构建
echo "使用 PyInstaller 构建可执行文件（简化版）..."

# 创建简化的 spec 文件
cat > WeRSS-Simple-Linux.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.yaml', '.'),
        ('static', 'static'),
        ('web.py', '.'),
        ('init_sys.py', '.'),
    ],
    hiddenimports=[
        'apis', 'core', 'jobs', 'web', 'main', 'init_sys',
        'core.models', 'core.auth', 'core.db', 'core.config', 
        'apis.auth', 'apis.user', 'apis.article',
        'uvicorn', 'fastapi', 'sqlite3',
        'sqlalchemy', 'pydantic', 'yaml', 'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='we-rss-simple',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

python3 -m PyInstaller WeRSS-Simple-Linux.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo "=============================="
    echo "简化版构建成功！"
    echo "=============================="
    
    if [ -f "dist/we-rss-simple" ]; then
        chmod +x dist/we-rss-simple
        echo "可执行文件位置: $(pwd)/dist/we-rss-simple"
        echo "文件大小: $(du -h dist/we-rss-simple | cut -f1)"
        echo ""
        echo "使用方法:"
        echo "  cd $(pwd)/dist"
        echo "  ./we-rss-simple"
    else
        echo "错误: 未找到生成的可执行文件"
    fi
else
    echo "错误: 构建失败"
    exit 1
fi

echo ""
echo "简化版构建完成！"
