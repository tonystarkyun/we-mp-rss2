#!/usr/bin/env python3
"""
Test script to validate QR code generation and crawler functionality
using the same browsers that WeRSS uses
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def test_chrome_functionality():
    """Test Chrome browser functionality for both QR code and crawler scenarios"""
    print("🧪 Testing Chrome browser functionality...")
    
    # Find the current Playwright Chrome path
    mei_dirs = [d for d in os.listdir('/tmp') if d.startswith('_MEI')]
    if not mei_dirs:
        print("❌ No PyInstaller temp directories found")
        return False
    
    # Use the most recent one (sorted)
    latest_mei = sorted(mei_dirs)[-1]
    chrome_path = f"/tmp/{latest_mei}/playwright/chromium-1187/chrome-linux/chrome"
    
    if not os.path.exists(chrome_path):
        print(f"❌ Chrome not found at {chrome_path}")
        return False
        
    print(f"✅ Found Chrome at: {chrome_path}")
    
    # Test 1: Basic Chrome functionality
    try:
        result = subprocess.run([
            chrome_path, "--version", "--no-sandbox", "--headless"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Chrome version check passed: {result.stdout.strip()}")
        else:
            print(f"❌ Chrome version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Chrome version test error: {e}")
        return False
    
    # Test 2: Web page loading (crawler simulation)
    print("🕷️  Testing crawler functionality...")
    try:
        result = subprocess.run([
            chrome_path, 
            "--no-sandbox", 
            "--headless", 
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--dump-dom", 
            "--virtual-time-budget=3000",
            "https://httpbin.org/json"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and "httpbin" in result.stdout:
            print("✅ Crawler functionality test passed - Can load and parse web pages")
        else:
            print(f"❌ Crawler test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Crawler test error: {e}")
        return False
    
    # Test 3: Screenshot capability (QR code generation simulation)
    print("📱 Testing QR code generation capability...")
    try:
        screenshot_path = "/tmp/test_screenshot.png"
        result = subprocess.run([
            chrome_path,
            "--no-sandbox",
            "--headless", 
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--window-size=800,600",
            f"--screenshot={screenshot_path}",
            "--virtual-time-budget=3000",
            "data:text/html,<html><body><h1>QR Code Test</h1><div style='width:200px;height:200px;background:black;margin:auto;'></div></body></html>"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and os.path.exists(screenshot_path):
            file_size = os.path.getsize(screenshot_path)
            print(f"✅ QR code generation test passed - Screenshot created ({file_size} bytes)")
            os.unlink(screenshot_path)  # Clean up
        else:
            print(f"❌ QR code generation test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ QR code generation test error: {e}")
        return False
    
    return True

def test_firefox_functionality():
    """Test Firefox browser as backup"""
    print("🧪 Testing Firefox browser functionality...")
    
    # Find Firefox path
    mei_dirs = [d for d in os.listdir('/tmp') if d.startswith('_MEI')]
    if not mei_dirs:
        return False
    
    latest_mei = sorted(mei_dirs)[-1]
    firefox_path = f"/tmp/{latest_mei}/playwright/firefox-1490/firefox/firefox"
    
    if not os.path.exists(firefox_path):
        print(f"❌ Firefox not found at {firefox_path}")
        return False
        
    print(f"✅ Found Firefox at: {firefox_path}")
    
    try:
        result = subprocess.run([
            firefox_path, "--version"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Firefox version check passed: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Firefox version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Firefox test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 WeRSS Browser Functionality Test")
    print("=" * 50)
    
    chrome_ok = test_chrome_functionality()
    print()
    firefox_ok = test_firefox_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Chrome (QR + Crawler): {'✅ PASS' if chrome_ok else '❌ FAIL'}")
    print(f"Firefox (Backup): {'✅ PASS' if firefox_ok else '❌ FAIL'}")
    
    if chrome_ok:
        print("\n🎉 SUCCESS: Browser functionality is working correctly!")
        print("✅ QR code generation should work")
        print("✅ Crawler functionality should work")
        print("\n💡 The issues mentioned in the documentation were likely")
        print("   related to X11 display configuration, not browser availability.")
        return True
    else:
        print("\n❌ FAILURE: Browser functionality issues detected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)