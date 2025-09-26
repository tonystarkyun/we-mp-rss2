# WeRSS Linux构建说明

本文档记录了WeRSS项目在Linux系统下的构建和打包过程，包括遇到的问题及解决方案。

## 系统要求

- **操作系统**: Linux (测试环境: Linux 6.2.0-36-generic)
- **Python版本**: Python 3.8+（测试版本: Python 3.10.12）
- **Node.js**: 用于前端构建
- **系统权限**: 需要安装pip和相关依赖的权限

## 构建步骤

### 1. 安装系统依赖

```bash
# 安装pip（如果系统没有）
sudo apt update && sudo apt install -y python3-pip

# 进入项目目录
cd /home/uadmin/Downloads/tonyCode/we-mp-rss2
```

### 2. 安装Python依赖

```bash
# 安装项目依赖
pip3 install -r requirements.txt

# 安装PyInstaller打包工具
pip3 install pyinstaller
```

**注意**: 安装过程中可能出现PATH警告，这不会影响构建：
```
WARNING: The script xxx is installed in '/home/uadmin/.local/bin' which is not on PATH.
```
这些警告可以忽略，依赖已正确安装。

### 3. 修复前端构建问题

在执行前端构建前，需要修复文件导入路径的大小写问题：

```bash
cd web_ui

# 检查问题（应该显示 import from '@/api/sysinfo'）
grep -n "sysinfo" src/App.vue

# 修复大小写问题
sed -i 's/sysinfo/sysInfo/g' src/App.vue

# 验证修复（应该显示 import from '@/api/sysInfo'）
grep -n "sysInfo" src/App.vue
```

### 4. 构建前端

```bash
# 在web_ui目录下
npm run build
cd ..
```

构建成功标志：
- 生成 `web_ui/dist` 目录
- 文件被复制到 `static/` 目录
- 看到 "前端构建完成！" 消息

### 5. 执行Linux打包

```bash
# 确保构建脚本可执行
chmod +x build-linux.sh

# 运行构建脚本（需要确认继续）
echo "y" | ./build-linux.sh
```

## 构建结果

成功构建后将生成：

- **可执行文件路径**: `dist/we-rss-linux`
- **文件大小**: 约92MB
- **文件类型**: ELF 64-bit LSB executable, x86-64

## 运行应用

### 直接运行
```bash
cd dist
./we-rss-linux
```

### 系统安装
```bash
sudo cp dist/we-rss-linux /usr/local/bin/
we-rss-linux
```

## 常见问题及解决方案

### 1. pip3命令不存在
**错误**: `错误: 未找到命令 'pip3'，请确保已安装`

**解决方案**:
```bash
sudo apt update && sudo apt install -y python3-pip
```

### 2. 前端构建失败 - sysinfo文件不存在
**错误**: `Could not load /path/to/web_ui/src/api/sysinfo: ENOENT: no such file or directory`

**原因**: 文件导入路径大小写不匹配（导入`sysinfo`，实际文件名是`sysInfo.ts`）

**解决方案**:
```bash
cd web_ui
sed -i 's/sysinfo/sysInfo/g' src/App.vue
```

### 3. 虚拟环境警告
**警告**: `警告: 建议在虚拟环境中运行构建脚本`

**解决方案**: 
- 可以忽略，直接输入 `y` 继续
- 或使用虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
# 然后重新安装依赖和构建
```

### 4. PATH警告
**警告**: 各种工具脚本安装到`/home/user/.local/bin`但不在PATH中

**解决方案**: 这些警告不影响构建，可以忽略。如果需要直接使用这些命令，可以：
```bash
export PATH=$PATH:/home/uadmin/.local/bin
```

## 构建架构说明

构建过程包含以下主要步骤：

1. **依赖检查**: 验证python3、pip等工具
2. **Python依赖安装**: 安装requirements.txt中的所有依赖
3. **前端构建**: Vue.js项目构建并复制到static目录
4. **PyInstaller打包**: 使用WeRSS-Linux.spec配置文件打包
5. **可执行文件生成**: 在dist目录生成单一可执行文件

## 项目文件结构

构建相关的关键文件：
- `build-linux.sh`: Linux构建脚本
- `WeRSS-Linux.spec`: PyInstaller配置文件
- `requirements.txt`: Python依赖清单
- `web_ui/build.sh`: 前端构建脚本
- `web_ui/package.json`: 前端依赖和构建配置

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **前端**: Vue.js 3 + TypeScript + Vite
- **打包工具**: PyInstaller
- **构建工具**: npm/yarn + Vite

## 注意事项

1. 构建过程需要较长时间（约1-2分钟），请耐心等待
2. 生成的可执行文件较大（90MB+），包含完整的Python运行时和所有依赖
3. 首次构建可能需要下载较多依赖，建议在网络良好的环境下进行
4. 构建成功后，可执行文件可以在没有Python环境的Linux系统上独立运行

## 更新历史

- 2025-09-03: 初始版本，记录完整构建流程和问题解决方案
- 2025-09-03: 添加浏览器支持和爬虫功能修复说明，解决Playwright浏览器打包和系统浏览器检测问题


## 浏览器支持和爬虫功能

### 系统浏览器检测

打包的应用支持自动检测和使用系统已安装的浏览器：

**Linux支持的浏览器路径：**
- **Google Chrome**: `/usr/bin/google-chrome`, `/usr/bin/google-chrome-stable`, `/opt/google/chrome/chrome`
- **Chromium**: `/snap/bin/chromium`, `/usr/bin/chromium`, `/usr/bin/chromium-browser`  
- **Firefox**: `/usr/bin/firefox`, `/opt/firefox/firefox`, `/snap/bin/firefox`

**浏览器优先级：**
1. **系统浏览器优先**：如果检测到系统安装的Chrome、Chromium或Firefox，优先使用
2. **内置浏览器备选**：如果没有系统浏览器，使用打包的Playwright Chromium浏览器
3. **智能启动**：根据浏览器类型选择合适的Playwright引擎（Firefox用firefox.launch，Chrome用chromium.launch）

### Playwright浏览器打包

为确保爬虫功能在没有系统浏览器的环境中正常工作，构建过程会：

1. **自动下载Playwright浏览器**：
```bash
python3 -m playwright install chromium
```

2. **打包浏览器文件**：PyInstaller配置自动将`~/.cache/ms-playwright/chromium-1187`打包到可执行文件中

3. **Runtime Hook设置**：创建了`runtime_hook_playwright.py`来设置正确的浏览器路径

**注意**：包含Playwright浏览器后，可执行文件大小会从~92MB增加到~147MB。

### 微信二维码功能

微信公众号扫码登录功能需要：
- **Firefox浏览器**：用于打开微信公众平台
- **Geckodriver**：Selenium WebDriver for Firefox
- **相关文件**：`driver/driver/geckodriver`（已包含在打包中）

## 完整部署包结构

成功构建后的部署包应包含以下文件：

```
dist/
├── we-rss-linux          # 主要可执行文件（147MB，包含Playwright浏览器）
├── config.yaml           # 应用配置文件
├── data/                 # 数据库存储目录
├── static/               # 前端静态文件目录
│   ├── index.html
│   ├── assets/
│   └── ...
└── driver/               # 微信驱动目录
    ├── driver/
    │   ├── geckodriver   # Firefox WebDriver
    │   └── geckodriver.exe
    ├── wx.py
    └── ...
```

## 构建脚本增强

为支持浏览器功能，构建脚本需要执行以下步骤：

1. **安装Playwright浏览器**（如果需要）：
```bash
python3 -m playwright install chromium
```

2. **修复前端构建问题**：
```bash
cd web_ui
sed -i 's/sysinfo/sysInfo/g' src/App.vue
```

3. **PyInstaller配置文件增强**：
   - 添加了Playwright浏览器文件打包
   - 添加了runtime hook支持
   - 包含了完整的driver目录

## 已知问题及解决方案

### 微信二维码生成失败问题

**问题描述**：
微信公众平台扫码登录功能失败，QR code generation fails due to Firefox WebDriver timeouts.

**错误现象**：
```
错误发生: HTTPConnectionPool(host='127.0.0.1', port=43393): Read timed out. (read timeout=30)
可能的原因:
1. 请确保已安装Firefox浏览器
2. 请确保geckodriver已下载并配置到PATH中
3. 检查网络连接是否可以访问微信公众平台
```

**问题分析**：
- Firefox浏览器已正确安装（版本 142.0.1）
- Geckodriver已正确下载并配置（版本 0.36.0，位于 `/home/uadmin/Downloads/tonyCode/we-mp-rss2/driver/driver/geckodriver`）
- 网络连接正常，可访问微信公众平台
- **根本原因**：Firefox WebDriver在连接过程中持续超时，可能是Firefox与Selenium WebDriver版本兼容性问题

**当前状态**：
- 爬虫功能：✅ 正常工作（使用系统Chrome浏览器）
- Web界面：✅ 正常访问 (http://localhost:8001)
- 数据库初始化：✅ 成功
- **微信二维码生成**：❌ 失败（主要功能）

**计划解决方案**：
1. 尝试使用Chrome WebDriver替代Firefox WebDriver
2. 创建基于Chrome的微信登录实现
3. 验证Chrome WebDriver在WeChat QR code生成中的稳定性

**临时工作方案**：
- 优先确保爬虫功能正常（已完成）
- 微信功能暂时不可用，待Chrome WebDriver方案验证后修复

**记录时间**：2025-09-03
**优先级**：HIGH（用户明确表示"微信扫码也是主要功能"）

## 部署包结构和依赖文件

### 完整的部署文件清单

成功构建后，`dist/` 目录包含运行WeRSS所需的所有文件：

```
dist/
├── we-rss-linux          # 主可执行文件（约147MB）
├── config.yaml           # 应用配置文件（必需）
├── data/                 # 数据存储目录（自动创建）
│   ├── cache/           # 缓存文件目录
│   ├── db.db            # SQLite数据库文件
│   ├── files/           # 用户文件存储
│   │   └── avatars/     # 头像文件存储
│   └── wx.lic           # 微信授权文件
├── driver/              # 微信驱动和浏览器驱动（必需）
│   ├── __init__.py
│   ├── auth.py          # 认证模块
│   ├── cookies.py       # Cookie管理
│   ├── driver/          # WebDriver文件
│   │   ├── geckodriver  # Firefox WebDriver（Linux）
│   │   └── geckodriver.exe # Firefox WebDriver（Windows）
│   ├── extdata/         # 扩展数据
│   ├── firefox_driver.py # Firefox驱动实现
│   ├── wx.py           # 微信登录驱动
│   ├── wxarticle.py    # 微信文章处理
│   └── ...             # 其他驱动相关文件
└── static/             # 前端静态文件（必需）
    ├── index.html      # 主页面
    ├── assets/         # 前端资源文件
    │   ├── *.js        # JavaScript文件
    │   ├── *.css       # 样式文件
    │   └── *.jpg       # 图片资源
    ├── default-avatar.png # 默认头像
    └── logo.svg        # 应用图标
```

### 自动拷贝依赖文件的构建命令

构建脚本 `build-linux.sh` 自动执行以下文件拷贝操作：

#### 1. 前端文件拷贝
```bash
# 构建前端项目（在web_ui目录下执行）
cd web_ui
./build.sh                    # 执行前端构建

# 拷贝前端构建结果到static目录
rm -rf ../static/assets       # 清理旧文件
cp -r dist/* ../static/       # 复制新构建的文件
```

#### 2. PyInstaller打包配置
在 `WeRSS-Linux.spec` 文件中定义的数据文件拷贝：
```python
datas=[
    ('config.example.yaml', '.'),        # 配置文件模板
    ('static', 'static'),                # 静态文件目录
    ('web.py', '.'),                     # Web服务模块
    ('init_sys.py', '.'),               # 系统初始化脚本
    ('data_sync.py', '.'),              # 数据同步脚本
    ('driver', 'driver'),               # 微信和浏览器驱动目录
    ('web_ui/dist', 'static'),          # 前端构建文件（如果存在）
]
```

#### 3. 运行时依赖文件生成
应用运行时会自动生成以下文件：
```bash
# 数据库初始化（首次运行）
./we-rss-linux                 # 自动创建 data/db.db

# 配置文件初始化
# 如果不存在config.yaml，自动从config.example.yaml复制
```

### 手动部署拷贝命令

如果需要手动准备部署包，可执行以下命令：

#### 从源码目录拷贝到部署目录
```bash
# 创建部署目录
mkdir -p /path/to/deployment/

# 拷贝必需文件
cp dist/we-rss-linux /path/to/deployment/          # 主执行文件
cp config.yaml /path/to/deployment/                # 配置文件
cp -r static /path/to/deployment/                  # 静态文件
cp -r driver /path/to/deployment/                  # 驱动文件

# 创建数据目录（可选，运行时自动创建）
mkdir -p /path/to/deployment/data/{cache,files/avatars}
```

#### 系统安装命令
```bash
# 安装到系统路径（可选）
sudo cp dist/we-rss-linux /usr/local/bin/werss
sudo chmod +x /usr/local/bin/werss

# 创建应用数据目录
mkdir -p ~/.werss/
cp config.yaml ~/.werss/
cp -r static ~/.werss/
cp -r driver ~/.werss/
```

### 最小运行依赖

**绝对必需的文件**（缺少任何一个都无法运行）：
- `we-rss-linux` - 主可执行文件
- `config.yaml` - 应用配置
- `static/` - 前端文件目录（包含index.html和assets/）
- `driver/` - 微信驱动目录（包含geckodriver和相关Python文件）

**自动生成的文件**（首次运行创建）：
- `data/db.db` - 数据库文件
- `data/cache/` - 缓存目录
- `data/files/` - 用户文件目录

### 部署验证命令

部署完成后，使用以下命令验证：
```bash
# 检查主执行文件
ls -la we-rss-linux                    # 应显示可执行权限

# 检查必需目录
ls -la static/ driver/                 # 应显示目录内容

# 检查配置文件
cat config.yaml | head -5              # 应显示YAML配置内容

# 测试运行
./we-rss-linux --help                  # 测试应用是否可启动
```



