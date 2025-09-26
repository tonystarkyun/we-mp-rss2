import os
import platform
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
import json

class ChromeController:
    isClose = True
    
    def __init__(self):
        self.system = platform.system().lower()
        self.driver_path = None
        self.browser_path = None
        self.options = Options()
        
        # 设置跨平台兼容的默认选项
        self.options.add_argument("--disable-web-security")
        self.options.add_argument("--disable-features=VizDisplayCompositor")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-plugins")
        self.options.add_argument("--disable-notifications")
        
    def string_to_json(self, json_string):
        try:
            json_obj = json.loads(json_string)
            return json_obj
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return ""
            
    def parse_string_to_dict(self, kv_str: str):
        result = {}
        items = kv_str.strip().split(';')
        for item in items:
            try:
                key, value = item.strip().split('=')
                result[key.strip()] = value.strip()
            except Exception as e:
                pass
        return result
        
    def add_cookies(self, cookies):
        for cookie in cookies:
            self.driver.add_cookie(cookie)
            
    def add_cookie(self, cookie):
        self.driver.add_cookie(cookie)
        
    def _is_chrome_installed_linux(self):
        """检查Linux是否已安装Chrome"""
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/google/chrome/chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return True
                
        try:
            subprocess.run(["which", "google-chrome"], check=True, stdout=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            pass
            
        try:
            subprocess.run(["which", "chromium"], check=True, stdout=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
            
    def _setup_chrome_binary_path(self):
        """设置Chrome二进制文件路径 - Linux专用"""
        if self.system == "linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/opt/google/chrome/chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    print(f"使用系统Chrome: {path}")
                    self.options.binary_location = path
                    return path
                    
            # 检查环境变量指定的路径
            if 'CHROME_BINARY' in os.environ:
                chrome_path = os.environ['CHROME_BINARY']
                if os.path.exists(chrome_path) and os.access(chrome_path, os.X_OK):
                    print(f"使用环境变量指定的Chrome: {chrome_path}")
                    self.options.binary_location = chrome_path
                    return chrome_path
                    
            print("警告: 未找到Chrome二进制文件，将使用系统默认")
            return None
        return None
        
    def _setup_driver(self):
        """自动配置chromedriver"""
        try:
            # 尝试使用webdriver_manager自动下载
            self.driver_path = ChromeDriverManager().install()
            print(f"使用ChromeDriver: {self.driver_path}")
        except Exception as e:
            print(f"ChromeDriver自动安装失败: {str(e)}")
            print("请手动下载ChromeDriver:")
            print("1. 访问 https://chromedriver.chromium.org/")
            print("2. 下载对应Chrome版本的驱动")
            print("3. 将chromedriver放入PATH中")
            raise
            
    def start_browser(self, headless=True):
        """启动浏览器"""
        try:
            if self.system == "linux" and not self._is_chrome_installed_linux():
                raise Exception("未检测到Chrome/Chromium浏览器，请先安装")
                
            self._setup_driver()
            
            # Linux专用：设置Chrome二进制文件路径
            if self.system == "linux":
                self._setup_chrome_binary_path()
                
            # 设置Chrome选项
            if headless:
                self.options.add_argument("--headless")
                self.options.add_argument("--disable-gpu")
                self.options.add_argument("--no-sandbox")
                self.options.add_argument("--disable-dev-shm-usage")
                self.options.add_argument("--disable-software-rasterizer")
                self.options.add_argument("--disable-background-timer-throttling")
                self.options.add_argument("--disable-renderer-backgrounding")
                self.options.add_argument("--disable-backgrounding-occluded-windows")
                self.options.add_argument("--remote-debugging-port=0")
                self.options.add_argument("--disable-extensions-file-access-check")
                self.options.add_argument("--disable-features=TranslateUI")
                self.options.add_argument("--disable-ipc-flooding-protection")
            else:
                # 非headless模式需要这些参数来支持Wayland环境
                self.options.add_argument("--no-sandbox")
                self.options.add_argument("--disable-dev-shm-usage")
                self.options.add_argument("--disable-gpu-sandbox")
                self.options.add_argument("--ozone-platform-hint=auto")
                
            # 添加稳定性配置
            self.options.add_argument("--disable-blink-features=AutomationControlled")
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=self.options)
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(300)
            self.driver.implicitly_wait(30)
            
            # 移除webdriver特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.isClose = False
            return self.driver
            
        except WebDriverException as e:
            print(f"Chrome浏览器启动失败: {str(e)}")
            raise
        except Exception as e:
            print(f"启动失败: {str(e)}")
            raise
            
    def __del__(self):
        """确保浏览器关闭"""
        self.Close()
        
    def open_url(self, url):
        """打开指定URL"""
        try:
            self.driver.get(url)
        except WebDriverException as e:
            print(f"打开URL失败: {str(e)}")
            raise
        except Exception as e:
            print(f"打开URL失败: {str(e)}")
            raise
            
    def Close(self):
        """关闭浏览器"""
        self.HasLogin = False
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.isClose = True
            
    def dict_to_json(self, data_dict):
        """
        将字典转换为JSON字符串
        :param data_dict: 需要转换的字典
        :return: JSON字符串或空字符串（转换失败时）
        """
        try:
            return json.dumps(data_dict, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            print(f"字典转JSON失败: {e}")
            return ""