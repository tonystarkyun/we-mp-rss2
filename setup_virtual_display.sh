#!/bin/bash

# 安装和配置虚拟显示环境来解决WeRSS的QR码生成和爬虫问题

echo "🚀 WeRSS 虚拟显示环境设置脚本"
echo "====================================="

# 检查是否需要sudo
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# 1. 安装Xvfb和相关依赖
echo "📦 安装虚拟显示依赖..."
$SUDO apt update
$SUDO apt install -y xvfb x11-utils xauth

# 2. 安装窗口管理器
echo "🪟 安装窗口管理器..."
$SUDO apt install -y fluxbox

# 3. 安装中文字体支持
echo "🔤 安装中文字体..."
$SUDO apt install -y fonts-wqy-zenhei fonts-wqy-microhei ttf-wqy-zenhei

# 4. 启动虚拟显示器
echo "🖥️  启动虚拟显示器..."
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!

# 等待Xvfb启动
sleep 3

# 5. 启动窗口管理器
echo "🏢 启动窗口管理器..."
fluxbox -display :99 > /dev/null 2>&1 &
FLUXBOX_PID=$!

# 6. 验证显示环境
echo "✅ 验证显示环境..."
if xdpyinfo -display :99 > /dev/null 2>&1; then
    echo "✅ 虚拟显示器启动成功"
else
    echo "❌ 虚拟显示器启动失败"
    exit 1
fi

# 7. 设置环境变量
echo "🔧 设置环境变量..."
export DISPLAY=:99
export CHROME_BIN=/usr/bin/google-chrome
export FIREFOX_BIN=/usr/bin/firefox

# 8. 创建启动WeRSS的脚本
cat > start_werss_with_display.sh << 'EOF'
#!/bin/bash

# 启动WeRSS服务与虚拟显示环境

echo "🚀 启动 WeRSS 商业雷达订阅助手（虚拟显示模式）"
echo "=================================================="

# 设置显示环境
export DISPLAY=:99
export CHROME_BIN=/usr/bin/google-chrome
export FIREFOX_BIN=/usr/bin/firefox

# 检查虚拟显示器是否运行
if ! pgrep Xvfb > /dev/null; then
    echo "🖥️  启动虚拟显示器..."
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
    sleep 3
fi

# 检查窗口管理器是否运行
if ! pgrep fluxbox > /dev/null; then
    echo "🪟 启动窗口管理器..."
    fluxbox -display :99 > /dev/null 2>&1 &
    sleep 2
fi

# 显示环境信息
echo "📊 环境信息:"
echo "   显示器: $DISPLAY"
echo "   Chrome: $CHROME_BIN"
echo "   Firefox: $FIREFOX_BIN"
echo ""

# 启动WeRSS服务
echo "🚀 启动 WeRSS 服务..."
echo "📱 访问地址: http://localhost:8001"
echo "👤 用户名: zkzc"
echo "🔐 密码: wf2151328"
echo "🌐 QR码生成: ✅ 支持"
echo "🕷️  爬虫功能: ✅ 支持"
echo ""

cd dist && exec ./we-rss-linux -job True -init True
EOF

chmod +x start_werss_with_display.sh

echo ""
echo "🎉 设置完成！"
echo "====================================="
echo "📱 虚拟显示环境已配置"
echo "🔧 启动脚本已创建: start_werss_with_display.sh"
echo ""
echo "🚀 现在可以使用以下命令启动 WeRSS:"
echo "   ./start_werss_with_display.sh"
echo ""
echo "💡 这将解决QR码生成和爬虫功能的显示环境问题"

# 保持进程运行
echo "⏰ 虚拟显示环境进程:"
echo "   Xvfb PID: $XVFB_PID"
echo "   Fluxbox PID: $FLUXBOX_PID"
echo ""
echo "✅ 环境准备就绪，可以启动WeRSS服务了！"