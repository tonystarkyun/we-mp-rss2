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
        
        # 设置 Playwright 浏览器路径
        playwright_dir = os.path.join(bundle_dir, 'playwright')
        if os.path.exists(playwright_dir):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = playwright_dir
            print(f"Runtime Hook: 设置 PLAYWRIGHT_BROWSERS_PATH = {playwright_dir}")
        
        # 设置 Firefox 浏览器路径（Linux专用）
        if system == "linux":
            # 检查打包的Firefox路径
            firefox_paths = [
                os.path.join(playwright_dir, 'firefox-1490', 'firefox', 'firefox'),  # Playwright Firefox
                os.path.join(bundle_dir, 'firefox', 'firefox'),  # 自定义Firefox打包路径
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
        
        elif system == "windows":
            # Windows Firefox 路径设置
            firefox_path = os.path.join(playwright_dir, 'firefox-1490', 'firefox', 'firefox.exe')
            if os.path.exists(firefox_path):
                os.environ['PLAYWRIGHT_FIREFOX_EXECUTABLE_PATH'] = firefox_path
                print(f"Runtime Hook: 设置 PLAYWRIGHT_FIREFOX_EXECUTABLE_PATH = {firefox_path}")
        
        # 设置 Chromium 浏览器路径（跨平台）
        if system == "linux":
            chromium_path = os.path.join(playwright_dir, 'chromium-1187', 'chrome-linux', 'chrome')
        else:
            chromium_path = os.path.join(playwright_dir, 'chromium-1187', 'chrome-win', 'chrome.exe')
        
        if os.path.exists(chromium_path):
            os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = chromium_path
            print(f"Runtime Hook: 设置 PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = {chromium_path}")
        
        # 设置ChromeDriver路径
        chromedriver_path = os.path.join(bundle_dir, "chromedriver")
        if os.path.exists(chromedriver_path):
            # 查找实际的chromedriver可执行文件
            for root, dirs, files in os.walk(chromedriver_path):
                for file in files:
                    if file == 'chromedriver' and not file.endswith('.zip'):
                        actual_path = os.path.join(root, file)
                        if os.access(actual_path, os.X_OK):
                            os.environ['CHROMEDRIVER_PATH'] = actual_path
                            print(f"Runtime Hook: 设置 CHROMEDRIVER_PATH = {actual_path}")
                            return
            # 如果没找到可执行文件，设置目录路径让chrome_driver.py去处理
            os.environ['CHROMEDRIVER_PATH'] = chromedriver_path
            print(f"Runtime Hook: 设置 CHROMEDRIVER_PATH = {chromedriver_path}")
            
        # 设置WDM缓存路径  
        wdm_path = os.path.join(bundle_dir, "wdm")
        if os.path.exists(wdm_path):
            os.environ['WDM_LOCAL'] = wdm_path
            print(f"Runtime Hook: 设置 WDM_LOCAL = {wdm_path}")
            
        # 设置系统浏览器路径
        if system == "linux":
            system_chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]
            for path in system_chrome_paths:
                if os.path.exists(path):
                    os.environ['CHROME_BINARY'] = path
                    print(f"Runtime Hook: 使用系统Chrome = {path}")
                    break

# 立即执行设置
try:
    setup_browser_paths()
    print("Runtime Hook: 浏览器路径设置完成")
except Exception as e:
    print(f"Runtime Hook 警告: 浏览器路径设置失败 - {e}")