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
            # 优先检查环境变量设置的路径（PyInstaller打包后使用）
            if 'CHROMEDRIVER_PATH' in os.environ:
                chromedriver_path = os.environ['CHROMEDRIVER_PATH']
                
                # 如果是直接的可执行文件路径
                if os.path.isfile(chromedriver_path) and os.access(chromedriver_path, os.X_OK):
                    self.driver_path = chromedriver_path
                    print(f"使用打包的ChromeDriver: {self.driver_path}")
                    return
                
                # 如果是目录，搜索其中的可执行文件
                if os.path.isdir(chromedriver_path):
                    for root, dirs, files in os.walk(chromedriver_path):
                        for file in files:
                            if file == 'chromedriver' or (file.startswith('chromedriver') and not file.endswith('.zip')):
                                file_path = os.path.join(root, file)
                                # 检查是否为可执行文件
                                if os.access(file_path, os.X_OK):
                                    self.driver_path = file_path
                                    print(f"使用打包的ChromeDriver: {self.driver_path}")
                                    return
                        
                        # 如果找到zip文件，尝试解压
                        for file in files:
                            if file.endswith('.zip') and 'chromedriver' in file:
                                zip_path = os.path.join(root, file)
                                try:
                                    import zipfile
                                    import tempfile
                                    
                                    # 创建临时目录解压
                                    temp_dir = tempfile.mkdtemp(prefix='chromedriver_')
                                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                        zip_ref.extractall(temp_dir)
                                    
                                    # 在解压的文件中寻找chromedriver
                                    for extracted_root, _, extracted_files in os.walk(temp_dir):
                                        for extracted_file in extracted_files:
                                            if extracted_file == 'chromedriver':
                                                extracted_path = os.path.join(extracted_root, extracted_file)
                                                # 设置执行权限
                                                os.chmod(extracted_path, 0o755)
                                                self.driver_path = extracted_path
                                                print(f"解压并使用ChromeDriver: {self.driver_path}")
                                                return
                                except Exception as e:
                                    print(f"解压ChromeDriver失败: {e}")
                                    continue
            
            # 尝试系统PATH中的chromedriver
            import shutil
            system_chromedriver = shutil.which('chromedriver')
            if system_chromedriver:
                self.driver_path = system_chromedriver
                print(f"使用系统ChromeDriver: {self.driver_path}")
                return
            
            # 最后尝试使用webdriver_manager自动下载
            self.driver_path = ChromeDriverManager().install()
            print(f"使用下载的ChromeDriver: {self.driver_path}")
        except Exception as e:
            print(f"ChromeDriver配置失败: {str(e)}")
            # 尝试使用默认的chromedriver命令
            self.driver_path = 'chromedriver'
            print("使用默认chromedriver命令")
            
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
                self.options.add_argument("--headless=new")  # 使用新版headless模式
                self.options.add_argument("--disable-gpu")
                self.options.add_argument("--no-sandbox")
                self.options.add_argument("--disable-dev-shm-usage")
                # 关键修复：添加Wayland支持（解决AppImage环境差异）
                self.options.add_argument("--ozone-platform-hint=auto")
                # 关键稳定性参数（按用户提供的最佳实践）
                self.options.add_argument("--window-size=1280,800")
                self.options.add_argument("--no-first-run")
                self.options.add_argument("--disable-features=Translate,BackForwardCache,AutomationControlled,TranslateUI,VizDisplayCompositor")
                self.options.add_argument("--disable-software-rasterizer")
                # 保持最精简的稳定参数，避免冲突
                self.options.add_argument("--disable-background-timer-throttling")
                self.options.add_argument("--disable-renderer-backgrounding")
                self.options.add_argument("--remote-debugging-port=0")
                self.options.add_argument("--disable-extensions-file-access-check")
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