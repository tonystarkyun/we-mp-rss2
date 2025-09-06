# WeRSS Docker 部署方案

## 🎯 解决问题

使用Docker部署 **完美解决了二维码生成和爬虫功能的问题**：

- ✅ **二维码生成问题**：提供完整的图形环境支持
- ✅ **爬虫功能问题**：集成Chrome + Firefox浏览器
- ✅ **环境依赖问题**：所有依赖都在容器中预配置
- ✅ **跨平台部署**：在任何支持Docker的系统上运行

## 🚀 快速开始

### 1. 确保已完成打包
```bash
./build-linux.sh
```

### 2. 一键部署
```bash
./docker-build-and-run.sh
```

### 3. 访问服务
- **Web界面**: http://localhost:8001
- **用户名**: zkzc
- **密码**: wf2151328

## 📋 功能支持

| 功能 | 原生部署 | Docker部署 | 说明 |
|------|----------|-----------|------|
| 基础Web服务 | ✅ | ✅ | 完全支持 |
| 用户认证 | ✅ | ✅ | 完全支持 |
| 二维码生成 | ❌ | ✅ | Docker提供图形环境 |
| 网站爬虫 | ❌ | ✅ | Docker提供浏览器环境 |
| 微信登录 | ❌ | ✅ | 支持Chrome/Firefox |
| RSS管理 | ✅ | ✅ | 完全支持 |

## 🛠️ 技术架构

### 容器环境配置
- **基础镜像**: Ubuntu 22.04
- **图形环境**: Xvfb虚拟显示器 + Fluxbox窗口管理器
- **浏览器**: Google Chrome + Firefox
- **字体支持**: 中文字体完整支持
- **Python环境**: Python 3.10 + 所有依赖

### 核心特性
```dockerfile
# 虚拟显示器
ENV DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24

# 浏览器支持  
google-chrome-stable
firefox

# 中文字体
fonts-wqy-zenhei
ttf-wqy-microhei
```

## 🔧 管理命令

### 基础操作
```bash
# 查看服务状态
docker-compose -f docker-compose.browser.yml ps

# 查看服务日志
docker-compose -f docker-compose.browser.yml logs -f

# 停止服务
docker-compose -f docker-compose.browser.yml down

# 重启服务
docker-compose -f docker-compose.browser.yml restart
```

### 调试模式
```bash
# 启动VNC服务（可视化调试）
docker-compose -f docker-compose.browser.yml --profile debug up -d

# 访问VNC界面查看浏览器
# URL: http://localhost:6901
# 密码: werss123
```

## 📊 性能配置

### 资源限制
- **内存限制**: 2GB
- **CPU限制**: 1核心
- **最小预留**: 1GB内存 + 0.5核心

### 数据持久化
- **配置文件**: `./config.yaml` -> `/app/config.yaml`
- **数据库**: `./data` -> `/app/data`
- **静态文件**: Docker卷管理
- **缓存**: Docker卷管理

## 🌟 优势对比

### vs 原生部署
| 对比项 | 原生部署 | Docker部署 |
|-------|---------|-----------|
| 部署复杂度 | 高 | 低 |
| 环境依赖 | 复杂 | 简单 |
| 浏览器支持 | 受限 | 完整 |
| 系统兼容性 | 受限 | 通用 |
| 维护成本 | 高 | 低 |

### 解决的核心问题
1. **X11 Display问题** → 虚拟显示器
2. **浏览器依赖问题** → 预装完整浏览器
3. **字体渲染问题** → 中文字体支持
4. **GPU访问问题** → 软件渲染模式

## 🔒 安全考虑

- 容器化隔离运行
- 非root用户权限
- 网络访问控制
- 数据卷权限管理

## 📈 扩展性

- 支持集群部署
- 负载均衡配置
- 监控和日志收集
- 自动扩缩容

---

**推荐使用Docker部署方案**，可以完美解决二维码生成和爬虫功能的所有问题！