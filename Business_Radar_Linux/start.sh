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
./Business_Radar
