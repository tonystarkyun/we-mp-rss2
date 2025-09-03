# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        ('config.example.yaml', '.'), 
        ('static', 'static'), 
        ('web.py', '.'), 
        ('init_sys.py', '.'), 
        ('data_sync.py', '.'),
        ('driver', 'driver'),  # 包含微信公众号和浏览器驱动
        ('web_ui/dist', 'static') if os.path.exists('web_ui/dist') else ('static', 'static'),  # 前端构建文件
        # 包含Playwright浏览器（如果存在）
    ] + ([
        (os.path.expanduser('~/.cache/ms-playwright/chromium-1187'), 'playwright/chromium-1187')
    ] if os.path.exists(os.path.expanduser('~/.cache/ms-playwright/chromium-1187')) else []) + [
    ],
    hiddenimports=[
        'apis', 'core', 'jobs', 'web', 'main', 'init_sys', 'data_sync',
        'core.models', 'core.models.user', 'core.models.links', 'core.models.article',
        'core.models.message_task', 'core.models.patents', 'core.models.industries',
        'core.models.feed', 'core.models.tags', 'core.models.link_articles',
        'core.models.patent_articles', 'core.models.industry_articles',
        'core.models.config_management', 'core.models.base',
        'core.auth', 'core.db', 'core.config', 'core.crawler', 'core.database',
        'core.content_format', 'core.file', 'core.log', 'core.print', 'core.resource',
        'core.rss', 'core.thread', 'core.ver',
        'core.lax', 'core.lax.template_parser',
        'core.notice', 'core.notice.custom', 'core.notice.dingtalk', 'core.notice.feishu', 'core.notice.wechat',
        'core.queue', 'core.queue.queue',
        'core.res', 'core.res.avatar',
        'core.task', 'core.task.task',
        'core.webhook', 'core.webhook.hook', 'core.webhook.parse',
        'core.wx', 'core.wx.base', 'core.wx.cfg', 'core.wx.wx', 'core.wx.wx1', 'core.wx.wx2', 'core.wx.wx3',
        'core.yaml_db', 'core.yaml_db.store_config',
        'apis.auth', 'apis.user', 'apis.links', 'apis.patents', 'apis.industries',
        'apis.article', 'apis.mps', 'apis.base', 'apis.config_management',
        'apis.export', 'apis.message_task', 'apis.res', 'apis.rss', 'apis.sys_info',
        'apis.tags', 'apis.ver',
        'jobs', 'jobs.article', 'jobs.failauth', 'jobs.fetch_no_article',
        'jobs.mps', 'jobs.notice', 'jobs.taskmsg', 'jobs.webhook',
        'uvicorn', 'fastapi', 'sqlite3', 'colorama',
        # 爬虫模块依赖
        'playwright', 'playwright.async_api', 'playwright._impl',
        # 微信公众号模块依赖
        'driver', 'driver.wx', 'driver.auth', 'driver.success', 'driver.store', 
        'driver.cookies', 'driver.firefox_driver', 'driver.wxarticle',
        'selenium', 'selenium.webdriver', 'selenium.webdriver.firefox',
        'selenium.webdriver.common.by', 'selenium.webdriver.support',
        'selenium.webdriver.support.ui', 'selenium.webdriver.support.expected_conditions',
        # 核心依赖
        'asyncio', 'urllib.parse', 'logging', 'PIL', 'PIL.Image',
        'bcrypt', 'passlib', 'passlib.hash', 'passlib.context',
        'sqlalchemy', 'sqlalchemy.dialects', 'sqlalchemy.dialects.sqlite',
        'pydantic', 'pydantic_core',
        'yaml', 'requests', 'bs4', 'beautifulsoup4',
        'schedule', 'apscheduler', 'psutil',
        'markdownify', 'reportlab'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py', 'runtime_hook_playwright.py'] if os.path.exists('runtime_hook.py') else ['runtime_hook_playwright.py'],
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
    name='we-rss-linux',
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





