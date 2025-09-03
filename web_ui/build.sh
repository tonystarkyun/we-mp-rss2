#!/bin/bash

# 前端构建脚本
echo "开始构建前端项目..."

# 检查是否安装了 Node.js 和 npm
if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js，请先安装 Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "错误: 未安装 npm，请先安装 npm"
    exit 1
fi

# 进入前端目录
cd "$(dirname "$0")"

# 安装依赖
echo "安装前端依赖..."
if command -v yarn &> /dev/null; then
    echo "使用 yarn 安装依赖..."
    yarn install
    if [ $? -ne 0 ]; then
        echo "错误: yarn install 失败"
        exit 1
    fi
    echo "使用 yarn 构建前端..."
    yarn build
else
    echo "使用 npm 安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "错误: npm install 失败"
        exit 1
    fi
    echo "使用 npm 构建前端..."
    npm run build
fi

if [ $? -eq 0 ]; then
    echo "前端构建完成！"
    echo "构建文件位于: $(pwd)/dist"
else
    echo "错误: 前端构建失败"
    exit 1
fi