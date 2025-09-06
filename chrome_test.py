#!/usr/bin/env python3
"""
Chrome崩溃最小复现测试
用于快速判断是系统环境问题还是业务代码问题
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import sys

def test_chrome_basic():
    """基础Chrome测试"""
    print("=== Chrome基础测试 ===")
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage") 
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-features=Translate,BackForwardCache,AutomationControlled")
    opts.add_argument("--enable-logging")
    opts.add_argument("--log-level=1")
    
    try:
        driver = webdriver.Chrome(options=opts)
        driver.get("https://www.baidu.com")
        print(f"✅ 基础测试成功: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ 基础测试失败: {e}")
        return False

def test_chrome_wechat():
    """微信公众平台测试"""  
    print("=== 微信公众平台测试 ===")
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--headless=new") 
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--no-first-run")
    opts.add_argument("--disable-features=Translate,BackForwardCache,AutomationControlled")
    opts.add_argument("--enable-logging")
    opts.add_argument("--log-level=1")
    
    try:
        driver = webdriver.Chrome(options=opts)
        driver.get("https://mp.weixin.qq.com/")
        print(f"✅ 微信平台测试成功: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ 微信平台测试失败: {e}")
        return False

if __name__ == "__main__":
    print("Chrome崩溃诊断测试开始...")
    
    # 显示Chrome版本
    try:
        chrome_version = os.popen("/usr/bin/google-chrome --version").read().strip()
        print(f"Chrome版本: {chrome_version}")
    except:
        print("❌ 无法获取Chrome版本")
    
    # 测试1：基础网站
    basic_ok = test_chrome_basic()
    
    # 测试2：微信公众平台  
    if basic_ok:
        wechat_ok = test_chrome_wechat()
        if wechat_ok:
            print("🎉 Chrome工作正常，问题可能在业务代码中")
        else:
            print("⚠️ Chrome可以访问普通网站，但无法访问微信公众平台")
    else:
        print("💥 Chrome基础功能就有问题，需要系统环境修复")
        
    print("诊断完成.")