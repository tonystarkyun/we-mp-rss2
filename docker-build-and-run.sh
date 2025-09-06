#!/bin/bash

# WeRSS Docker 构建和运行脚本
# 支持完整的浏览器环境（二维码生成 + 爬虫功能）

set -e

echo "🚀 WeRSS Docker 部署脚本"
echo "==============================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装Docker Compose"
    exit 1
fi

# 检查打包文件是否存在
if [ ! -f "dist/we-rss-linux" ]; then
    echo "❌ 打包文件 dist/we-rss-linux 不存在"
    echo "请先运行: ./build-linux.sh"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data
mkdir -p cache

# 复制配置文件
if [ ! -f "config.yaml" ]; then
    echo "📝 复制默认配置文件..."
    cp config.example.yaml config.yaml
fi

# 构建Docker镜像
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.browser.yml build

# 启动服务
echo "🚀 启动WeRSS服务..."
docker-compose -f docker-compose.browser.yml up -d

# 等待服务启动
echo "⏰ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f docker-compose.browser.yml ps

# 显示访问信息
echo ""
echo "✅ WeRSS 服务已启动！"
echo "==============================="
echo "🌐 访问地址: http://localhost:8001"
echo "👤 用户名: zkzc"
echo "🔐 密码: wf2151328"
echo ""
echo "🔧 管理命令:"
echo "  查看日志: docker-compose -f docker-compose.browser.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.browser.yml down"
echo "  重启服务: docker-compose -f docker-compose.browser.yml restart"
echo ""
echo "🕷️  功能支持:"
echo "  ✅ 二维码生成 (Chrome + Firefox)"
echo "  ✅ 网站爬虫功能"  
echo "  ✅ 微信公众号订阅"
echo "  ✅ RSS订阅管理"
echo ""
echo "🐞 调试模式（查看浏览器界面）:"
echo "  启动VNC: docker-compose -f docker-compose.browser.yml --profile debug up -d"
echo "  访问VNC: http://localhost:6901 (密码: werss123)"
