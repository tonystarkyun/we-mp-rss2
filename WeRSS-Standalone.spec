# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['standalone_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.yaml', '.'), 
        ('static', 'static'), 
        ('web.py', '.'), 
        ('init_sys.py', '.'), 
        ('data_sync.py', '.'),
        ('driver', 'driver'),  # 包含微信公众号和浏览器驱动
        # Playwright 浏览器二进制文件
        (r'C:\Users\Administrator\AppData\Local\ms-playwright', 'ms-playwright')
    ],
    hiddenimports=[
        'apis', 'core', 'jobs', 'web', 'main', 'init_sys', 'data_sync',
        'core.models', 'core.models.user', 'core.models.links', 'core.models.article',
        'core.models.message_task', 'core.models.patents', 'core.models.industries',
        'core.models.feed', 'core.models.tags', 'core.models.link_articles',
        'core.models.patent_articles', 'core.models.industry_articles',
        'core.auth', 'core.db', 'core.config', 'core.crawler',
        'apis.auth', 'apis.user', 'apis.links', 'apis.patents', 'apis.industries',
        'apis.article', 'apis.mps', 'uvicorn', 'fastapi', 'sqlite3', 'colorama',
        # 爬虫模块依赖
        'playwright', 'playwright.async_api', 'playwright._impl',
        # 微信公众号模块依赖
        'driver', 'driver.wx', 'driver.auth', 'driver.success', 'driver.store', 
        'driver.cookies', 'driver.firefox_driver', 'driver.wxarticle',
        'selenium', 'selenium.webdriver', 'selenium.webdriver.firefox',
        'selenium.webdriver.common.by', 'selenium.webdriver.support',
        'selenium.webdriver.support.ui', 'selenium.webdriver.support.expected_conditions',
        # 核心依赖
        'asyncio', 'urllib.parse', 'logging', 'PIL', 'PIL.Image'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WeRSS-Standalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
