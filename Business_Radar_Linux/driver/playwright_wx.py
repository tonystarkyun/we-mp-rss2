import os
import sys
import time
import json
from PIL import Image
from playwright.sync_api import sync_playwright
from .success import Success
from .store import Store
from .cookies import expire
from core.print import print_error, print_warning, print_info, print_success


class PlaywrightWx:
    HasLogin = False
    SESSION = None
    HasCode = False
    isLOCK = False
    WX_LOGIN = "https://mp.weixin.qq.com/"
    WX_HOME = "https://mp.weixin.qq.com/cgi-bin/home"
    wx_login_url = "static/wx_qrcode.png"
    lock_file_path = "data/.lock"
    CallBack = None
    Notice = None
    
    def __init__(self):
        self.lock_path = os.path.dirname(self.lock_file_path)
        self.refresh_interval = 3660 * 24
        if not os.path.exists(self.lock_path):
            os.makedirs(self.lock_path)
        self.Clean()
        self.release_lock()
        self.playwright = None
        self.browser = None
        self.page = None
        
    def check_dependencies(self):
        """检查Playwright依赖"""
        try:
            import playwright
            return True
        except ImportError as e:
            print("缺少Playwright依赖，请先安装：")
            print("pip install playwright")
            print("playwright install chromium")
            return False
            
    def GetHasCode(self):
        if os.path.exists(self.wx_login_url):
            return True
        return False
        
    def extract_token_from_page(self):
        """从页面中提取token"""
        try:
            # 尝试从当前URL获取token
            current_url = self.page.url
            import re
            token_match = re.search(r'token=([^&]+)', current_url)
            if token_match:
                return token_match.group(1)
            
            # 尝试从localStorage获取
            token = self.page.evaluate("() => localStorage.getItem('token')")
            if token:
                return token
                
            # 尝试从sessionStorage获取
            token = self.page.evaluate("() => sessionStorage.getItem('token')")
            if token:
                return token
                
            return None
        except Exception as e:
            print(f"提取token时出错: {str(e)}")
            return None
            
    def GetCode(self, CallBack=None, Notice=None):
        self.Notice = Notice
        if self.check_lock():
            print_warning("微信公众平台登录脚本正在运行，请勿重复运行")
            return {
                "code": f"{self.wx_login_url}?t={(time.time())}",
                "msg": "微信公众平台登录脚本正在运行，请勿重复运行！"
            }
       
        self.Clean()
        print("子线程执行中")
        from core.thread import ThreadManager
        self.thread = ThreadManager(target=self.wxLogin, args=(CallBack, True))
        self.thread.start()
        print("微信公众平台登录 v1.35 (Playwright)")
        return self.QRcode()
    
    def QRcode(self):
        return {
            "code": f"{self.wx_login_url}?t={(time.time())}",
            "is_exists": self.GetHasCode(),
        }
        
    def wxLogin(self, CallBack=None, NeedExit=False):
        """
        Playwright版本的微信公众平台登录流程
        """
        if not self.check_dependencies():
            return None
            
        try:
            if self.check_lock():
                return "微信公众平台登录脚本正在运行，请勿重复运行！"
            self.set_lock()
            self.HasLogin = False
            self.Clean()
            self.Close()
            
            # 启动Playwright
            print("正在启动Playwright浏览器...")
            self.playwright = sync_playwright().start()
            
            # 检测环境并选择浏览器
            is_packaged = hasattr(sys, '_MEIPASS')
            if is_packaged:
                print("打包环境：使用Playwright Firefox（更稳定）")
                browser_type = self.playwright.firefox
                launch_options = {
                    'headless': False,  # 微信二维码需要可见窗口
                    'firefox_user_prefs': {
                        'dom.webdriver.enabled': False,
                        'useAutomationExtension': False,
                        'security.sandbox.content.level': 5,
                        'general.useragent.override': 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
                    }
                }
            else:
                print("开发环境：使用Playwright Chromium")
                browser_type = self.playwright.chromium
                launch_options = {
                    'headless': False,
                    'args': ['--no-sandbox', '--disable-dev-shm-usage']
                }
            
            self.browser = browser_type.launch(**launch_options)
            
            # 创建新页面
            self.page = self.browser.new_page()
            
            # 设置用户代理和视口
            self.page.set_viewport_size({'width': 1920, 'height': 1080})
            self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
            })
            
            # 打开微信公众平台
            print("正在打开微信公众平台...")
            self.page.goto(self.WX_LOGIN, wait_until='networkidle')
            
            # 等待并定位二维码元素
            print("正在等待二维码加载...")
            qrcode_selector = ".login__type__container__scan__qrcode"
            self.page.wait_for_selector(qrcode_selector, timeout=30000)
            
            # 滚动到二维码区域确保可见
            qrcode_element = self.page.locator(qrcode_selector)
            qrcode_element.scroll_into_view_if_needed()
            
            # 等待二维码图片完全加载
            self.page.wait_for_load_state('networkidle')
            time.sleep(2)
            
            # 获取二维码元素的边界框
            print("正在生成二维码图片...")
            qrcode_box = qrcode_element.bounding_box()
            
            if qrcode_box is None:
                raise Exception("无法获取二维码元素位置")
            
            # 截图并裁剪二维码区域
            screenshot_path = "temp_screenshot.png"
            self.page.screenshot(path=screenshot_path)
            
            # 使用PIL裁剪二维码区域
            img = Image.open(screenshot_path)
            left = int(qrcode_box['x'])
            top = int(qrcode_box['y'])
            right = int(qrcode_box['x'] + qrcode_box['width'])
            bottom = int(qrcode_box['y'] + qrcode_box['height'])
            
            qr_img = img.crop((left, top, right, bottom))
            qr_img.save(self.wx_login_url)
            os.remove(screenshot_path)
            
            print("二维码已保存为 wx_qrcode.png，请扫码登录...")
            self.HasCode = True
            
            # 检查二维码文件大小
            if os.path.getsize(self.wx_login_url) <= 364:
                raise Exception("二维码图片获取失败，请重新扫码")
                
            # 通知用户扫码
            if self.Notice is not None:
                self.Notice()
                
            # 等待登录成功（URL变化到首页）
            print("等待扫码登录...")
            self.page.wait_for_url(f"**/home**", timeout=120000)
            
            self.CallBack = CallBack
            self.Call_Success()
            
        except Exception as e:
            print_error(f"Playwright微信登录错误: {str(e)}")
            self.SESSION = None
            self.Clean()
            self.Close()
        finally:
            self.release_lock()
            if NeedExit:
                self.Clean()
                self.Close()
        return self.SESSION
        
    def format_token(self, cookies, token=""):
        """格式化cookies和token"""
        cookies_str = ""
        cookie_list = []
        
        # 转换Playwright cookies为Selenium格式
        for cookie in cookies:
            cookie_dict = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/'),
                'secure': cookie.get('secure', False),
                'httpOnly': cookie.get('httpOnly', False)
            }
            cookie_list.append(cookie_dict)
            cookies_str += f"{cookie['name']}={cookie['value']}; "
            
        if token == "":
            for cookie in cookies:
                if 'token' in cookie['name'].lower():
                    token = cookie['value']
                    break
                    
        # 计算cookie有效时间
        cookie_expiry = expire(cookie_list)
        return {
            'cookies': cookie_list,
            'cookies_str': cookies_str,
            'token': token,
            'wx_login_url': self.wx_login_url,
            'expiry': cookie_expiry
        }
        
    def Call_Success(self):
        # 获取token
        token = self.extract_token_from_page()
        
        # 获取当前所有cookie
        cookies = self.page.context.cookies()
        
        self.SESSION = self.format_token(cookies, token)
        self.HasLogin = False if self.SESSION["expiry"] is None else True
        self.Clean()
        
        if self.HasLogin:
            print_success("Playwright登录成功！")
            # 转换并保存cookies（保持与原有系统兼容）
            selenium_cookies = self.SESSION['cookies']
            Store.save(selenium_cookies)
        else:
            print_warning("未登录！")
            
        if self.CallBack is not None:
            self.CallBack(self.SESSION)
        return self.SESSION
        
    def Close(self):
        """关闭Playwright浏览器"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.browser:
                self.browser.close() 
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            return True
        except Exception as e:
            print(f"关闭Playwright浏览器时出错: {str(e)}")
            return False
            
    def Clean(self):
        try:
            os.remove(self.wx_login_url)
        except:
            pass
            
    def check_lock(self):
        """检查锁定状态"""
        time.sleep(1)
        return os.path.exists(self.lock_file_path)
        
    def set_lock(self):
        """创建锁定文件"""
        with open(self.lock_file_path, 'w') as f:
            f.write(str(time.time()))
        self.isLOCK = True
        
    def release_lock(self):
        """删除锁定文件"""
        try:
            os.remove(self.lock_file_path)
            self.isLOCK = False
            return True
        except:
            return False


def DoSuccess(cookies) -> dict:
    """兼容性函数"""
    data = PLAYWRIGHT_WX_API.format_token(cookies)
    Success(data)


PLAYWRIGHT_WX_API = PlaywrightWx()