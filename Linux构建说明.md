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

