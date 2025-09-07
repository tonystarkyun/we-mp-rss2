# WeRSS 打包依赖下载指南

> 本文档记录了 WeRSS 项目打包所需的外部依赖文件下载和配置方法，用于新同事环境搭建。

## 概述

WeRSS 项目使用 Playwright 进行网页爬虫功能，打包时需要包含完整的浏览器依赖。为了避免将大型二进制文件推送到 Git 仓库，这些依赖需要单独下载和配置。

## 必需依赖列表

### 1. Playwright 浏览器依赖 (~500MB)
- **路径**: `~/.cache/ms-playwright/`
- **用途**: Playwright 自动化浏览器依赖
- **包含**: Firefox, Chromium 等浏览器完整文件

### 2. WebDriver Manager 缓存 (~50MB)
- **路径**: `~/.wdm/`
- **用途**: Selenium WebDriver 管理器缓存
- **包含**: ChromeDriver, GeckoDriver 等

### 3. 原生 Firefox 浏览器 (可选, ~100MB)
- **路径**: `~/firefox-native/firefox/`
- **用途**: 备用 Firefox 浏览器
- **包含**: 完整的 Firefox 安装目录

## 依赖下载步骤

### 第一步: 安装 Python 依赖
```bash
# 确保在项目根目录下
cd /path/to/we-mp-rss2

# 安装 Python 包依赖
pip install -r requirements.txt
```

### 第二步: 安装 Playwright 浏览器
```bash
# 安装 Playwright 浏览器依赖
playwright install

# 验证安装结果
ls -la ~/.cache/ms-playwright/
```

**预期输出结构**:
```
~/.cache/ms-playwright/
├── chromium-1187/
│   └── chrome-linux/
│       └── chrome
├── firefox-1490/
│   └── firefox/
│       └── firefox
└── webkit-1944/
    └── ...
```

### 第三步: 初始化 WebDriver Manager
```bash
# 运行一次程序，自动下载 WebDriver 依赖
python -c "
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

print('下载 ChromeDriver...')
ChromeDriverManager().install()

print('下载 GeckoDriver...')
GeckoDriverManager().install()

print('WebDriver 依赖安装完成')
"
```

**验证安装**:
```bash
ls -la ~/.wdm/drivers/
```

### 第四步: 下载原生 Firefox (可选)
```bash
# 创建 Firefox 原生目录
mkdir -p ~/firefox-native

# 下载 Firefox (Linux x64)
cd ~/firefox-native
wget "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=zh-CN" -O firefox.tar.bz2

# 解压
tar -xjf firefox.tar.bz2

# 验证
ls -la ~/firefox-native/firefox/firefox
```

## 验证依赖完整性

### 检查脚本
创建并运行以下检查脚本：

```bash
# 创建检查脚本
cat > check_dependencies.py << 'END'
#!/usr/bin/env python3
import os

def check_dependency(path, name):
    if os.path.exists(path):
        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                   for dirpath, dirnames, filenames in os.walk(path)
                   for filename in filenames) / (1024*1024)
        print(f"✅ {name}: {path} ({size:.1f}MB)")
        return True
    else:
        print(f"❌ {name}: {path} (未找到)")
        return False

print("=== WeRSS 打包依赖检查 ===")
dependencies = [
    (os.path.expanduser("~/.cache/ms-playwright"), "Playwright 浏览器"),
    (os.path.expanduser("~/.wdm"), "WebDriver Manager"),
    (os.path.expanduser("~/firefox-native/firefox"), "原生 Firefox (可选)")
]

all_ok = True
for path, name in dependencies:
    if not check_dependency(path, name):
        all_ok = False

if all_ok:
    print("\n🎉 所有必需依赖已就绪，可以进行打包！")
else:
    print("\n⚠️  部分依赖缺失，请按照文档安装")
END

# 运行检查
python check_dependencies.py
```

### 预期输出
```
=== WeRSS 打包依赖检查 ===
✅ Playwright 浏览器: /home/user/.cache/ms-playwright (485.2MB)
✅ WebDriver Manager: /home/user/.wdm (52.8MB)
✅ 原生 Firefox (可选): /home/user/firefox-native/firefox (98.4MB)

🎉 所有必需依赖已就绪，可以进行打包！
```

## 测试依赖功能

### 测试 Playwright
```bash
# 测试 Playwright 浏览器
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://www.baidu.com')
        title = await page.title()
        print(f'页面标题: {title}')
        await browser.close()
        print('✅ Playwright Firefox 测试成功')

asyncio.run(test())
"
```

### 测试 WebDriver
```bash
# 测试 WebDriver 功能
python -c "
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

options = Options()
options.add_argument('--headless')

driver = webdriver.Firefox(
    executable_path=GeckoDriverManager().install(),
    options=options
)

driver.get('https://www.baidu.com')
print(f'页面标题: {driver.title}')
driver.quit()
print('✅ Selenium Firefox 测试成功')
"
```

## 打包流程

依赖安装完成后，执行标准打包流程：

```bash
# 清理之前的构建
rm -rf build/ dist/we-rss-linux

# 打包 (确保依赖已正确安装)
pyinstaller WeRSS-Linux.spec --clean

# 验证打包结果
ls -lh dist/we-rss-linux  # 应该约为 615MB
```

## 故障排除

### 常见问题

1. **Playwright 浏览器下载失败**
   ```bash
   # 手动指定下载源
   PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net playwright install
   ```

2. **权限问题**
   ```bash
   # 确保目录权限
   chmod -R 755 ~/.cache/ms-playwright
   chmod -R 755 ~/.wdm
   ```

3. **磁盘空间不足**
   ```bash
   # 检查可用空间 (至少需要 2GB)
   df -h ~
   ```

4. **网络连接问题**
   ```bash
   # 使用代理下载 (如果需要)
   export HTTP_PROXY=http://proxy:port
   export HTTPS_PROXY=http://proxy:port
   playwright install
   ```

### 清理缓存
如果需要重新下载依赖：

```bash
# 清理 Playwright 缓存
rm -rf ~/.cache/ms-playwright

# 清理 WebDriver 缓存
rm -rf ~/.wdm

# 清理原生 Firefox
rm -rf ~/firefox-native

# 重新执行安装步骤
```

## 团队协作说明

### 新同事环境搭建
1. 克隆代码仓库
2. 按照本文档安装所有依赖
3. 运行检查脚本验证环境
4. 执行测试确认功能正常
5. 进行打包测试

### 版本管理
- **不要**将 `~/.cache/ms-playwright` 添加到 Git
- **不要**将 `~/.wdm` 添加到 Git  
- **不要**将 `~/firefox-native` 添加到 Git
- **确保** `.gitignore` 包含这些路径

### 持续集成 (CI/CD)
如果使用 CI/CD，在构建脚本中添加：

```bash
# CI 环境依赖安装
pip install -r requirements.txt
playwright install
python check_dependencies.py
```

## 依赖版本记录

当前测试通过的版本：
- **Playwright**: 1.40.0+
- **Firefox**: 120.0+
- **Chromium**: 119.0+
- **Python**: 3.8+
- **PyInstaller**: 5.0+

## 总结

按照本文档正确安装所有依赖后，WeRSS 项目可以成功打包为约 615MB 的独立可执行文件，包含完整的浏览器自动化功能。新同事只需要按照步骤执行即可快速搭建开发和打包环境。
