#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小复现测试：验证Chrome headless是否能访问微信公众平台
用于区分是"系统问题"还是"项目代码问题"
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chrome_headless():
    print("=== Chrome Headless 最小复现测试 ===")
    
    # 打印环境信息
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"DISPLAY: {os.environ.get('DISPLAY', '未设置')}")
    print(f"XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', '未设置')}")
    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', '未设置')[:100]}...")
    print()
    
    # 设置Chrome选项
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage") 
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    # 添加Wayland支持
    opts.add_argument("--ozone-platform-hint=auto")
    # 添加调试信息
    opts.add_argument("--enable-logging")
    opts.add_argument("--log-level=1")
    opts.add_argument("--disable-web-security")
    
    try:
        print("正在启动Chrome...")
        driver = webdriver.Chrome(options=opts)
        print("✅ Chrome启动成功")
        
        print("正在访问微信公众平台...")
        driver.get("https://mp.weixin.qq.com/")
        print(f"✅ 页面加载成功")
        print(f"页面标题: {driver.title}")
        print(f"当前URL: {driver.current_url}")
        
        driver.quit()
        print("✅ 测试完成，Chrome正常工作")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print(f"异常类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_chrome_headless()
    sys.exit(0 if success else 1)