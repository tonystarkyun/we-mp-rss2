# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook for WeRSS
设置 Playwright 和 Firefox 浏览器路径 (跨平台支持)
"""
import os
import sys
import platform

def setup_browser_paths():
    """设置浏览器路径 - 跨平台支持"""
    if hasattr(sys, '_MEIPASS'):
        # 在 PyInstaller 打包环境中
        bundle_dir = sys._MEIPASS
        system = platform.system().lower()
        
        # 正确设置 Playwright 浏览器路径
        playwright_dir = os.path.join(bundle_dir, 'playwright')
        if os.path.exists(playwright_dir):
            # 设置正确的 PLAYWRIGHT_BROWSERS_PATH
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = playwright_dir
            print(f"Runtime Hook: 设置 PLAYWRIGHT_BROWSERS_PATH = {playwright_dir}")
            
            # 验证浏览器文件是否存在
            chromium_path = os.path.join(playwright_dir, 'chromium-1187', 'chrome-linux', 'chrome')
            if os.path.exists(chromium_path):
                print(f"Runtime Hook: 发现Chromium浏览器: {chromium_path}")
            else:
                print(f"Runtime Hook: 警告 - Chromium浏览器不存在: {chromium_path}")
                
        # 设置 Firefox 浏览器路径（Linux专用）
        if system == "linux":
            # 检查打包的Firefox路径
            firefox_paths = [
                os.path.join(playwright_dir, 'firefox-1490', 'firefox', 'firefox'),  # Playwright Firefox
                os.path.join(bundle_dir, 'firefox-native', 'firefox'),  # 自定义Firefox打包路径
            ]
            
            for firefox_path in firefox_paths:
                if os.path.exists(firefox_path):
                    os.environ['FIREFOX_BINARY'] = firefox_path
                    print(f"Runtime Hook: 设置 FIREFOX_BINARY = {firefox_path}")
                    break
            else:
                # 未找到打包的Firefox，设置系统路径优先级
                system_firefox_paths = ["/usr/bin/firefox", "/usr/bin/firefox-esr"]
                for path in system_firefox_paths:
                    if os.path.exists(path):
                        os.environ['FIREFOX_BINARY'] = path
                        print(f"Runtime Hook: 使用系统Firefox = {path}")
                        break
        
        # 设置 Chromium 浏览器路径（跨平台）
        if system == "linux":
            chromium_path = os.path.join(playwright_dir, 'chromium-1187', 'chrome-linux', 'chrome')
        else:
            chromium_path = os.path.join(playwright_dir, 'chromium-1187', 'chrome-win', 'chrome.exe')
        
        if os.path.exists(chromium_path):
            os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = chromium_path
            print(f"Runtime Hook: 设置 PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = {chromium_path}")

# 立即执行设置
try:
    setup_browser_paths()
    print("Runtime Hook: 浏览器路径设置完成")
except Exception as e:
    print(f"Runtime Hook 警告: 浏览器路径设置失败 - {e}")
