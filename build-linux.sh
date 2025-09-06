#!/bin/bash

# WeRSS Linux 构建脚本
# 这个脚本将构建前端并使用 PyInstaller 创建 Linux 可执行文件

set -e  # 出错时退出

echo "=============================="
echo "WeRSS Linux 构建脚本"
echo "=============================="

# 检查必要的命令
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "错误: 未找到命令 '$1'，请确保已安装"
        exit 1
    fi
}

echo "检查依赖..."
check_command python3
check_command pip3

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "检测到虚拟环境: $VIRTUAL_ENV"
else
    echo "警告: 建议在虚拟环境中运行构建脚本"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "当前工作目录: $(pwd)"

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 构建前端
echo "构建前端项目..."
if [ -d "web_ui" ]; then
    cd web_ui
    chmod +x build.sh
    ./build.sh
    
    if [ $? -ne 0 ]; then
        echo "错误: 前端构建失败"
        exit 1
    fi
    
    # 复制构建结果到 static 目录
    if [ -d "dist" ]; then
        echo "复制前端构建文件到 static 目录..."
        rm -rf ../static/assets 2>/dev/null || true
        cp -r dist/* ../static/
        echo "前端文件复制完成"
    else
        echo "警告: 前端构建目录 dist 不存在"
    fi
    
    cd ..
else
    echo "警告: 未找到 web_ui 目录，跳过前端构建"
fi

# 清理之前的构建
echo "清理之前的构建文件..."
rm -rf dist build 2>/dev/null || true

# 使用 PyInstaller 构建
echo "使用 PyInstaller 构建可执行文件..."
python3 -m PyInstaller WeRSS-Linux.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo "=============================="
    echo "构建成功！"
    echo "=============================="
    
    if [ -f "dist/we-rss-linux" ]; then
        echo "可执行文件位置: $(pwd)/dist/we-rss-linux"
        echo "文件大小: $(du -h dist/we-rss-linux | cut -f1)"
        
        # 使文件可执行
        chmod +x dist/we-rss-linux
        
        echo ""
        echo "使用方法:"
        echo "  cd $(pwd)/dist"
        echo "  ./we-rss-linux"
        echo ""
        echo "或者可以移动到系统路径:"
        echo "  sudo cp dist/we-rss-linux /usr/local/bin/"
        echo "  we-rss-linux"
        
    else
        echo "警告: 未找到生成的可执行文件"
        echo "请检查 dist 目录内容:"
        ls -la dist/ 2>/dev/null || echo "dist 目录不存在"
    fi
else
    echo "错误: PyInstaller 构建失败"
    exit 1
fi

echo ""
echo "构建完成！"











