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
    
    if [ -f "dist/Business_Radar" ]; then
        echo "可执行文件位置: $(pwd)/dist/Business_Radar"
        echo "文件大小: $(du -h dist/Business_Radar | cut -f1)"
        
        # 使文件可执行
        chmod +x dist/Business_Radar
        
        # 复制必要的依赖文件到 dist 目录
        echo "复制依赖文件到 dist 目录..."
        
        # 复制配置文件
        echo "复制配置文件..."
        cp config.example.yaml dist/config.yaml
        
        # 复制静态文件目录
        echo "复制静态文件..."
        cp -r static dist/ 2>/dev/null || echo "警告: 静态文件目录不存在"
        
        # 复制driver目录（WebDriver和微信模块）
        echo "复制WebDriver和微信模块..."
        cp -r driver dist/ 2>/dev/null || echo "警告: driver目录不存在"
        
        # 确保数据库是干净的
        echo "准备数据目录..."
        mkdir -p dist/data/cache
        mkdir -p dist/data/files/avatars
        
        # 创建日志目录
        echo "创建日志目录..."
        mkdir -p dist/logs
        
        # 检查并复制干净的数据库
        if [ -f "data/db.db" ]; then
            echo "检查数据库状态..."
            python3 -c "
import sqlite3, sys
conn = sqlite3.connect('data/db.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
user_count = cursor.fetchone()[0]
if user_count <= 1:
    print('✅ 数据库状态良好，用户数:', user_count)
else:
    print('⚠️  数据库包含', user_count, '个用户，建议清理')
    sys.exit(1)
conn.close()
"
            if [ $? -eq 0 ]; then
                cp data/db.db dist/data/
                echo "✅ 复制干净的数据库"
            else
                echo "❌ 数据库需要清理，请先运行: python3 reset_database_final.py"
                exit 1
            fi
        else
            echo "⚠️  未找到数据库文件，将在首次运行时创建"
        fi
        
        # 复制许可证文件
        cp LICENSE README.md dist/ 2>/dev/null || true
        
        # 创建启动脚本
        echo "创建启动脚本..."
        cat > dist/start.sh << 'EOF'
#!/bin/bash

# Business Radar 启动脚本

echo "=============================="
echo "Business Radar 商业雷达订阅助手"
echo "=============================="

# 检查当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 确保数据目录存在
mkdir -p data/cache
mkdir -p data/files/avatars

# 检查可执行文件
if [ ! -f "Business_Radar" ]; then
    echo "错误: 找不到可执行文件 Business_Radar"
    exit 1
fi

# 设置可执行权限
chmod +x Business_Radar

echo "启动中..."
echo "访问地址: http://localhost:8001"
echo "默认登录: zkzc / wf2151328"
echo "按 Ctrl+C 停止服务"
echo "=============================="

# 启动应用
./Business_Radar -init True
EOF
        chmod +x dist/start.sh
        
        echo ""
        echo "✅ 完整分发包已创建在 dist/ 目录："
        echo "├── Business_Radar         # 主程序可执行文件"
        echo "├── start.sh               # 启动脚本"
        echo "├── config.yaml            # 配置文件"  
        echo "├── data/                  # 数据目录"
        echo "│   ├── db.db             # SQLite数据库"
        echo "│   ├── cache/            # 缓存目录"
        echo "│   └── files/            # 文件存储目录"
        echo "├── logs/                  # 日志目录"
        echo "├── static/               # 前端静态文件"
        echo "│   ├── assets/           # JS/CSS资源"
        echo "│   ├── index.html        # 前端入口"
        echo "│   └── logo.svg          # 图标文件"
        echo "└── driver/               # WebDriver和微信模块"
        echo "    ├── wx.py             # 微信API接口"
        echo "    ├── wxarticle.py      # 微信文章处理"
        echo "    └── driver/           # WebDriver可执行文件"
        echo ""
        echo "使用方法:"
        echo "  cd $(pwd)/dist"
        echo "  ./start.sh"
        echo ""
        echo "或直接运行:"
        echo "  cd $(pwd)/dist"
        echo "  ./Business_Radar"
        
    else
        echo "警告: 未找到生成的可执行文件 Business_Radar"
        echo "请检查 dist 目录内容:"
        ls -la dist/ 2>/dev/null || echo "dist 目录不存在"
    fi
else
    echo "错误: PyInstaller 构建失败"
    exit 1
fi

echo ""
echo "构建完成！"











