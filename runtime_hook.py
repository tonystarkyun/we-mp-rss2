# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook for WeRSS-Standalone
设置 Playwright 和 Firefox 浏览器路径
"""
import os
import sys

def setup_browser_paths():
    """设置浏览器环境变量"""
    if hasattr(sys, '_MEIPASS'):
        # 在 PyInstaller 打包环境中
        bundle_dir = sys._MEIPASS
        
        # 设置 Playwright 浏览器路径
        playwright_browsers_path = os.path.join(bundle_dir, 'ms-playwright')
        if os.path.exists(playwright_browsers_path):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = playwright_browsers_path
            
        # 设置 Firefox 浏览器可执行文件路径
        firefox_path = os.path.join(playwright_browsers_path, 'firefox-1490', 'firefox', 'firefox.exe')
        if os.path.exists(firefox_path):
            os.environ['PLAYWRIGHT_FIREFOX_EXECUTABLE_PATH'] = firefox_path
        
        # 设置 Chromium 浏览器路径
        chromium_path = os.path.join(playwright_browsers_path, 'chromium-1187', 'chrome-win', 'chrome.exe')
        if os.path.exists(chromium_path):
            os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = chromium_path

# 立即执行设置
setup_browser_paths()