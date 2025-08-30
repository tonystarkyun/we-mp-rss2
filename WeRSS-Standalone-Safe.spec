"""
Safe build spec for WeRSS without bundled Playwright browsers.

This version excludes Playwright browsers to avoid decompression issues,
relying on system-installed browsers or separate browser installation.
"""

import os
import sys
import platform

# Base datas required by the app
base_datas = [
    ('config.example.yaml', '.'),
    ('static', 'static'),
    ('web.py', '.'),
    ('init_sys.py', '.'),
    ('data_sync.py', '.'),
]

# Bundle Selenium geckodriver and related extra data under driver/* if present
if os.path.isdir('driver/driver'):
    base_datas.append(('driver/driver', 'driver/driver'))
if os.path.isdir('driver/extdata'):
    base_datas.append(('driver/extdata', 'driver/extdata'))

# 注意：此版本不包含 Playwright 浏览器以避免解压缩问题
# 用户需要单独安装 Playwright 浏览器：playwright install firefox


a = Analysis(
    ['standalone_launcher.py'],
    pathex=[],
    binaries=[],
    datas=base_datas,
    hiddenimports=[
        'apis', 'core', 'jobs', 'web', 'main', 'init_sys', 'data_sync',
        'core.models', 'core.models.user', 'core.models.links', 'core.models.article',
        'core.models.message_task', 'core.models.patents', 'core.models.industries',
        'core.models.feed', 'core.models.tags', 'core.models.link_articles',
        'core.models.patent_articles', 'core.models.industry_articles',
        'core.auth', 'core.db', 'core.config', 'core.crawler',
        'apis.auth', 'apis.user', 'apis.links', 'apis.patents', 'apis.industries',
        'apis.article', 'apis.mps', 'uvicorn', 'fastapi', 'sqlite3', 'colorama'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],  # 不使用 runtime hook，避免 Playwright 路径问题
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
    name='WeRSS-Standalone-Safe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 