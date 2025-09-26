# WeRSS Linux 分发部署指南

## 分发文件清单

将整个 `dist` 文件夹打包分发，包含以下文件：

```
dist/
├── we-rss-linux          # 主可执行文件 (614MB)
├── config.yaml           # 配置文件
├── data/                 # 数据目录
│   ├── db.db            # SQLite数据库
│   ├── cache/           # 缓存目录
│   └── files/           # 用户文件目录
└── static/              # 前端静态文件
    ├── assets/          # JS/CSS资源
    ├── index.html       # 前端入口
    └── logo.svg         # 图标文件
```

## 目标系统要求

### 必需条件

1. **系统架构**: x86_64 (64位)
2. **内核版本**: GNU/Linux 3.2.0 或更高
3. **基础库**: 
   - glibc 2.31+ (通常Ubuntu 20.04+、CentOS 8+、Debian 10+都满足)
   - libdl.so.2, libz.so.1, libpthread.so.0, libc.so.6

### 推荐条件

1. **显示环境**: 
   - X11 或 Wayland (用于二维码生成)
   - 支持 `$DISPLAY` 环境变量
2. **内存**: 建议 2GB+ RAM  
3. **磁盘空间**: 1GB+ 可用空间
4. **网络**: 外网访问权限（用于爬虫功能）

### 浏览器依赖说明

**✅ 无需安装浏览器！** 

本打包文件已内置所有必要的浏览器：
- **Firefox 1490** (用于二维码生成)
- **Chromium 1187** (用于网页爬虫)
- **ChromeDriver** (用于Selenium自动化)

即使目标机器完全没有安装Firefox、Chrome或Chromium，应用也能正常工作。

## 兼容性测试

### 已测试兼容的系统
- ✅ Ubuntu 22.04 LTS (开发环境)
- ✅ Ubuntu 20.04 LTS (理论兼容)

### 可能兼容的系统
- 🟡 Debian 10/11/12
- 🟡 CentOS 8/Rocky Linux 8+
- 🟡 RHEL 8+
- 🟡 openSUSE Leap 15+
- 🟡 Arch Linux (最新)

### 不兼容的系统
- ❌ CentOS 7 (glibc版本过低)
- ❌ Ubuntu 18.04 (glibc可能过低)
- ❌ 32位系统
- ❌ ARM架构 (需要重新编译)

## 部署步骤

### 1. 传输文件
```bash
# 打包dist目录
tar -czf we-rss-linux.tar.gz dist/

# 传输到目标服务器
scp we-rss-linux.tar.gz user@target-server:~/

# 在目标服务器解压
tar -xzf we-rss-linux.tar.gz
cd dist/
```

### 2. 检查依赖
```bash
# 检查可执行文件依赖
ldd we-rss-linux

# 检查是否有缺失的库
ldd we-rss-linux | grep "not found"
```

### 3. 设置权限
```bash
# 确保可执行权限
chmod +x we-rss-linux

# 检查是否能正常启动
./we-rss-linux --version
```

### 4. 启动服务
```bash
# 初始化启动（首次运行）
./we-rss-linux -init True

# 后续启动
./we-rss-linux

# 后台运行
nohup ./we-rss-linux > app.log 2>&1 &
```

## 配置说明

### 端口配置
默认端口: `8001`
如需修改，编辑 `config.yaml`:
```yaml
port: 8080  # 修改为目标端口
```

### 数据库路径
默认使用相对路径 `data/db.db`，会自动在当前目录创建数据文件

### 访问地址
```
http://服务器IP:8001
```

## 常见问题解决

### 0. 目标机器没有浏览器
**不用担心！** 应用已内置所有必要的浏览器，包括：
- Firefox 1490 (22MB+，用于二维码生成)
- Chromium 1187 (100MB+，用于网页爬虫)  
- ChromeDriver (用于自动化)

无论目标机器是否安装了Firefox、Chrome或其他浏览器，都不会影响功能。

### 1. 权限问题
```bash
# 如果提示权限不够
chmod +x we-rss-linux
chmod -R 755 data/
```

### 2. 端口占用
```bash
# 检查端口占用
netstat -tulpn | grep 8001

# 修改config.yaml中的端口号
```

### 3. 依赖库缺失
```bash
# Ubuntu/Debian 安装基础库
sudo apt-get update
sudo apt-get install libc6-dev libssl-dev

# CentOS/RHEL 安装基础库
sudo yum install glibc-devel openssl-devel
```

### 4. 显示环境问题 (无GUI环境)
如果是纯命令行服务器，需要安装虚拟显示：
```bash
# 安装xvfb
sudo apt-get install xvfb  # Ubuntu/Debian
sudo yum install xorg-x11-server-Xvfb  # CentOS/RHEL

# 启动虚拟显示
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# 然后启动应用
./we-rss-linux -init True
```

## 系统服务配置 (可选)

创建systemd服务文件 `/etc/systemd/system/we-rss.service`:

```ini
[Unit]
Description=WeRSS Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/dist
ExecStart=/path/to/dist/we-rss-linux
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable we-rss
sudo systemctl start we-rss
sudo systemctl status we-rss
```

## 安全建议

1. **防火墙配置**: 只开放必要端口 (如8001)
2. **反向代理**: 建议使用nginx做反向代理并启用HTTPS
3. **用户权限**: 不要使用root用户运行应用
4. **定期备份**: 备份 `data/` 目录中的数据库和文件

## 验证清单

部署完成后，请验证以下功能：

- [ ] 应用能正常启动并监听指定端口
- [ ] 能通过浏览器访问Web界面
- [ ] 能正常登录 (zkzc/wf2151328)
- [ ] 二维码生成功能正常
- [ ] 爬虫功能正常（在有网络的环境下）
- [ ] 数据库读写正常

---

**注意**: 此可执行文件包含了完整的Python运行时和所有依赖，但仍需要系统提供基础的共享库支持。如果在某些特定系统上遇到兼容性问题，可能需要在目标系统上重新编译打包。