# Linux系统完整修复总结

## 概述

本文档记录了WeRSS项目在Linux系统下完整打包和功能修复的全过程，包括WeChat扫码功能、爬虫功能、单文件打包配置等。

## 主要问题与解决方案

### 1. WeChat扫码功能修复

**问题**: Firefox WebDriver在Linux下频繁超时，导致二维码生成失败

**解决方案**: 实现Chrome WebDriver支持，双浏览器自动切换机制

#### 1.1 创建Chrome WebDriver控制器

创建文件 `driver/chrome_driver.py`:
- 检测Linux系统Chrome安装路径
- 使用webdriver_manager自动下载ChromeDriver
- 支持Chrome、Chromium、系统浏览器检测

#### 1.2 修改WeChat认证逻辑

修改文件 `driver/wx.py`:
- 添加 `_get_browser_controller()` 方法
- 优先使用Chrome，Firefox作为备选
- 自动切换机制，提高成功率

### 2. Playwright爬虫功能修复

**问题**: 打包后Playwright浏览器缺失，导致爬虫功能异常

**解决方案**: 
```bash
playwright install
```

**依赖位置**:
- `~/.cache/ms-playwright/chromium-1187/`
- `~/.cache/ms-playwright/firefox-1490/` 
- `~/.cache/ms-playwright/webkit-xxxx/`

### 3. 单文件打包配置

**目标**: 将所有依赖打包到单个可执行文件中

#### 3.1 修改PyInstaller配置

文件 `WeRSS-Linux.spec`:
```python
exe = EXE(
    onefile=True,  # 启用单文件打包
)

datas=[
    # ChromeDriver依赖
    ('~/.wdm/drivers/chromedriver', 'chromedriver'),
    # webdriver-manager缓存
    ('~/.wdm', 'wdm'),
    # Playwright浏览器
    ('~/.cache/ms-playwright', 'playwright'),
]

hiddenimports=[
    'driver.chrome_driver',
    'webdriver_manager', 'webdriver_manager.chrome',
]
```

### 4. 数据库初始化保护机制

**问题**: 每次使用`-init True`启动都会清空数据库

**解决方案**: 修改 `main.py` 初始化逻辑

```python
def main():
    db_path = cfg.get("db", "data/db.db")
    if cfg.args.init=="True" and not os.path.exists(db_path):
        # 只在数据库不存在时初始化
        import init_sys as init
        init.init()
```

**启动参数**:
- `./we-rss-linux -init True` - 仅在数据库不存在时初始化
- `./we-rss-linux -init force` - 强制重新初始化
- `./we-rss-linux` - 正常启动

### 5. 用户凭证与应用名称

**登录凭证** (文件 `init_sys.py`):
- 用户名: `zkzc`
- 密码: `wf2151328`

**应用标题修改**:
- `static/index.html`: 商业雷达订阅助手
- `config.example.yaml`: web_name 改为商业雷达订阅助手

## 完整构建流程

### 开发环境
```bash
pip3 install -r requirements.txt
playwright install
python3 main.py -init True  # 首次
python3 main.py             # 后续
```

### 生产打包
```bash
cd web_ui && yarn build
pip3 install -r requirements.txt
playwright install
./build-linux.sh
```

## 功能验证

### WeChat扫码
1. 访问 http://localhost:8001
2. 登录: zkzc / wf2151328
3. 微信授权 - 正常生成QR码

### 爬虫功能  
1. 行业动态 → 测试爬虫
2. 应该正常抓取，无Playwright错误

## 依赖路径总结

- ChromeDriver: `~/.wdm/drivers/chromedriver/`
- Playwright: `~/.cache/ms-playwright/`
- 系统Chrome: `/usr/bin/google-chrome`

