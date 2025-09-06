#!/usr/bin/env python3
"""
测试Firefox无代理启动
"""
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import os

def test_firefox():
    print("🔧 测试Firefox无代理启动...")
    
    # 查找Firefox和geckodriver路径
    firefox_path = None
    geckodriver_path = None
    
    # 检查原生Firefox
    native_firefox = os.path.expanduser("~/firefox-native/firefox/firefox")
    if os.path.exists(native_firefox):
        firefox_path = native_firefox
        print(f"✅ 找到原生Firefox: {firefox_path}")
    
    # 检查geckodriver
    geckodriver_paths = [
        "./driver/geckodriver",
        "/usr/local/bin/geckodriver",
        "/usr/bin/geckodriver"
    ]
    
    for path in geckodriver_paths:
        if os.path.exists(path):
            geckodriver_path = path
            print(f"✅ 找到geckodriver: {geckodriver_path}")
            break
    
    if not firefox_path or not geckodriver_path:
        print("❌ 缺少必要的浏览器组件")
        return False
    
    try:
        # 配置Firefox选项
        options = Options()
        options.headless = False  # 显示浏览器便于调试
        options.binary_location = firefox_path
        
        # 强制禁用代理
        options.set_preference("network.proxy.type", 0)  # 0 = 不使用代理
        options.set_preference("network.proxy.no_proxies_on", "localhost,127.0.0.1")
        options.set_preference("network.proxy.share_proxy_settings", False)
        options.set_preference("network.proxy.socks", "")
        options.set_preference("network.proxy.http", "")
        options.set_preference("network.proxy.ssl", "")
        
        # 启动Firefox
        service = Service(executable_path=geckodriver_path)
        driver = webdriver.Firefox(service=service, options=options)
        
        print("🚀 Firefox启动成功！")
        print("📝 尝试访问微信公众平台...")
        
        # 测试访问微信公众平台
        driver.get("https://mp.weixin.qq.com/")
        
        print("✅ 成功访问微信公众平台！")
        print("🔍 当前页面标题:", driver.title)
        
        input("按Enter键关闭浏览器...")
        driver.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_firefox()