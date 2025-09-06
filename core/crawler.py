# core/crawler.py - 链接管理爬虫服务
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
import asyncio
import time
import os
import sys
import shutil
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class LinkCrawler:
    """链接管理爬虫服务"""
    
    def __init__(self, headless: bool = True, timeout: int = 300000):
        self.headless = headless
        self.timeout = timeout
        self.browser_executable = self._find_browser_executable()
        
    async def crawl_website_articles(self, url: str, max_articles: int = 50) -> Dict:
        """
        爬取网站的文章列表
        
        Args:
            url: 目标网站URL
            max_articles: 最大抓取文章数
            
        Returns:
            Dict: 包含成功状态、文章列表和统计信息
        """
        result = {
            'success': False,
            'articles': [],
            'total_found': 0,
            'website_info': {
                'url': url,
                'title': '',
                'description': ''
            },
            'error': None
        }
        
        # 如果是PyInstaller环境，直接使用requests+BeautifulSoup避开Playwright问题
        if hasattr(sys, '_MEIPASS'):
            logger.info("检测到PyInstaller环境，使用requests+BeautifulSoup方案")
            try:
                import requests
                from bs4 import BeautifulSoup
                import re
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                logger.info(f"正在爬取网站: {url}")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取网站基本信息
                result['website_info']['title'] = soup.title.string if soup.title else ''
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                result['website_info']['description'] = meta_desc.get('content', '') if meta_desc else ''
                
                # 根据不同网站提取文章
                articles = []
                if 'pubmed.ncbi.nlm.nih.gov' in url:
                    # PubMed特殊处理
                    article_elements = soup.find_all('article', class_='full-docsum')
                    for element in article_elements[:max_articles]:
                        title_elem = element.find('a', class_='docsum-title')
                        if title_elem:
                            title = title_elem.get_text().strip()
                            link = 'https://pubmed.ncbi.nlm.nih.gov' + title_elem.get('href', '')
                            
                            # 提取摘要
                            abstract_elem = element.find('div', class_='full-view-snippet')
                            abstract = abstract_elem.get_text().strip() if abstract_elem else ''
                            
                            # 提取作者
                            authors_elem = element.find('span', class_='docsum-authors')
                            authors = authors_elem.get_text().strip() if authors_elem else ''
                            
                            # 提取发表时间
                            date_elem = element.find('span', class_='docsum-journal-citation')
                            pub_date = date_elem.get_text().strip() if date_elem else ''
                            
                            articles.append({
                                'title': title,
                                'url': link,
                                'content': abstract,
                                'author': authors,
                                'publish_date': pub_date,
                                'source': 'PubMed'
                            })
                else:
                    # 通用文章提取
                    for selector in ['article', 'div.article', 'div.post', 'div.entry']:
                        elements = soup.select(selector)
                        if elements:
                            break
                    
                    for element in elements[:max_articles]:
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                        title = title_elem.get_text().strip() if title_elem else ''
                        
                        link_elem = element.find('a')
                        link = link_elem.get('href', '') if link_elem else ''
                        if link.startswith('/'):
                            from urllib.parse import urljoin
                            link = urljoin(url, link)
                        
                        content = element.get_text().strip()[:500] + '...' if len(element.get_text().strip()) > 500 else element.get_text().strip()
                        
                        if title and link:
                            articles.append({
                                'title': title,
                                'url': link,
                                'content': content,
                                'author': '',
                                'publish_date': '',
                                'source': result['website_info']['title']
                            })
                
                result['articles'] = articles
                result['total_found'] = len(articles)
                result['success'] = True
                logger.info(f"使用requests方案成功爬取 {len(articles)} 篇文章")
                return result
                
            except Exception as e:
                logger.error(f"requests方案也失败: {e}")
                # 继续尝试Playwright方案
                pass
        
        try:
            async with async_playwright() as p:
                # 检测环境并配置浏览器启动参数
                if hasattr(sys, '_MEIPASS'):
                    logger.info("检测到PyInstaller环境，清除打包浏览器路径使用系统浏览器")
                    # 打印环境信息用于调试
                    logger.info(f"MEIPASS目录: {sys._MEIPASS}")
                    logger.info(f"原PLAYWRIGHT_BROWSERS_PATH: {os.environ.get('PLAYWRIGHT_BROWSERS_PATH', 'Not set')}")
                    logger.info(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
                    
                    # 完全清除PLAYWRIGHT_BROWSERS_PATH，让Playwright使用系统默认行为
                    if 'PLAYWRIGHT_BROWSERS_PATH' in os.environ:
                        del os.environ['PLAYWRIGHT_BROWSERS_PATH']
                        logger.info("已清除PLAYWRIGHT_BROWSERS_PATH，使用系统默认浏览器路径")
                    
                    # 使用Playwright默认行为（就像开发环境一样）
                    logger.info("使用Playwright默认浏览器启动方式")
                    browser = await p.chromium.launch(headless=self.headless)
                else:
                    logger.info("使用Playwright内置Chromium浏览器")
                    browser = await p.chromium.launch(headless=self.headless)
                
                # 创建上下文时添加更多稳定性配置（使用Linux User-Agent）
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    ignore_https_errors=True,
                    java_script_enabled=True,
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                # 增加页面超时时间并使用更宽松的等待策略
                page.set_default_timeout(60000)  # 60秒超时
                page.set_default_navigation_timeout(60000)
                
                logger.info(f"正在爬取网站: {url}")
                
                # 在PyInstaller环境中使用更保守的页面加载策略
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        if attempt == 0:
                            # 第一次尝试：标准加载
                            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                            logger.info("页面加载完成")
                            break
                        elif attempt == 1:
                            # 第二次尝试：仅等待开始加载
                            await page.goto(url, wait_until='commit', timeout=20000)
                            logger.info("页面开始加载完成")
                            await asyncio.sleep(5)  # 手动等待
                            break
                        else:
                            # 最后尝试：不等待，直接导航
                            await page.goto(url, timeout=15000)
                            logger.info("页面导航完成（无等待）")
                            await asyncio.sleep(8)  # 更长的手动等待
                            break
                    except Exception as goto_error:
                        logger.warning(f"第{attempt+1}次页面加载失败: {goto_error}")
                        if attempt == max_retries - 1:
                            raise goto_error
                        await asyncio.sleep(2)  # 重试间隔
                
                # 等待页面加载
                await asyncio.sleep(3)
                
                # 尝试关闭可能的cookie同意弹窗
                await self._handle_cookie_consent(page)
                
                # 获取网站基本信息
                result['website_info'] = await self._extract_website_info(page, url)
                
                # 爬取文章列表
                articles = await self._extract_articles(page, url, max_articles)
                
                result['articles'] = articles
                result['total_found'] = len(articles)
                result['success'] = len(articles) > 0
                
                if not articles:
                    result['error'] = "未找到符合条件的文章链接"
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"爬取网站时发生错误: {str(e)}")
            result['error'] = str(e)
            
        return result
    
    def _find_browser_executable(self) -> Optional[str]:
        """查找可用的浏览器可执行文件"""
        
        # 如果是PyInstaller环境，使用Playwright内置浏览器
        if hasattr(sys, '_MEIPASS'):
            logger.info("检测到PyInstaller环境，使用Playwright内置浏览器")
            return None  # 使用内置浏览器
            
            # Linux和通用路径
            if sys.platform.startswith("linux"):
                browser_paths = [
                    # Google Chrome Linux路径
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable", 
                    "/opt/google/chrome/chrome",
                    "/snap/bin/chromium",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                    # Firefox Linux路径
                    "/usr/bin/firefox",
                    "/opt/firefox/firefox",
                    "/snap/bin/firefox",
                ]
            else:
                # Windows Chrome路径
                browser_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                    # Edge浏览器作为备选
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ]
            
            for browser_path in browser_paths:
                if os.path.exists(browser_path):
                    logger.info(f"找到浏览器: {browser_path}")
                    return browser_path
            
            logger.warning("未找到系统安装的Chrome、Firefox或Edge浏览器")
            return None
        
        # 开发环境使用Playwright自带的浏览器
        logger.info("开发环境，使用Playwright内置浏览器")
        return None
    
    def _get_firefox_executable(self) -> Optional[str]:
        """获取Firefox可执行文件路径（与二维码生成功能保持一致）"""
        
        # 如果是PyInstaller环境，检查打包的Firefox
        if hasattr(sys, '_MEIPASS'):
            packaged_firefox = os.path.join(sys._MEIPASS, 'firefox-native', 'firefox')
            if os.path.exists(packaged_firefox) and os.access(packaged_firefox, os.X_OK):
                logger.info(f"使用打包的原生Firefox: {packaged_firefox}")
                return packaged_firefox
        else:
            # 开发环境：优先使用本地下载的原生Firefox
            native_firefox = os.path.expanduser("~/firefox-native/firefox/firefox")
            if os.path.exists(native_firefox) and os.access(native_firefox, os.X_OK):
                logger.info(f"使用原生Firefox: {native_firefox}")
                return native_firefox
                
        # 检查系统Firefox路径
        firefox_paths = [
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr", 
            "/snap/bin/firefox",
            "/opt/firefox/firefox"
        ]
        
        for path in firefox_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"使用系统Firefox: {path}")
                return path
        
        logger.warning("未找到Firefox浏览器")
        return None
    
    async def _handle_cookie_consent(self, page):
        """处理cookie同意弹窗"""
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("同意")',
            'button:has-text("Agree")',
            'button:has-text("确定")',
            'button#onetrust-accept-btn-handler',
            '.cookie-consent button',
            '[data-testid="cookie-accept"]'
        ]
        
        for selector in cookie_selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    await page.locator(selector).first.click(timeout=2000)
                    await asyncio.sleep(1)
                    break
            except Exception:
                continue
    
    async def _extract_website_info(self, page, url: str) -> Dict[str, str]:
        """提取网站基本信息"""
        info = {
            'url': url,
            'title': '',
            'description': ''
        }
        
        try:
            # 获取网站标题
            title = await page.title()
            if title:
                info['title'] = title.strip()
            
            # 获取网站描述
            meta_desc = page.locator('meta[name="description"]').first
            desc_count = await meta_desc.count()
            if desc_count > 0:
                description = await meta_desc.get_attribute('content')
                if description:
                    info['description'] = description.strip()
                    
        except Exception as e:
            logger.warning(f"提取网站信息时出错: {e}")
            
        return info
    
    async def _extract_articles(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """提取文章列表"""
        articles = []
        
        # 通用文章选择器策略（按优先级排序）
        selectors = [
            # 新闻和博客网站常用选择器
            'article h1 a, article h2 a, article h3 a',
            'article a[href]',
            '.post-title a, .entry-title a',
            '.article-title a, .news-title a',
            'h1 a, h2 a, h3 a',
            '.title a',
            # 列表页面选择器
            'li a[href]',
            'ul a[href]',
            # 通用链接选择器
            'a[href*="/article/"], a[href*="/post/"], a[href*="/news/"]',
            'a[href*="blog"], a[href*="story"]',
            'a[title][href]'
        ]
        
        found_urls = set()
        
        for selector in selectors:
            try:
                links = await page.query_selector_all(selector)
                
                if not links:
                    continue
                    
                logger.info(f"使用选择器 '{selector}' 找到 {len(links)} 个潜在链接")
                
                for link in links:
                    if len(articles) >= max_articles:
                        break
                        
                    try:
                        # 获取链接信息
                        title = (await link.inner_text()).strip()
                        href = await link.get_attribute('href')
                        
                        if not title or not href or len(title) < 5:
                            continue
                            
                        # 处理相对链接
                        full_url = self._normalize_url(href, base_url)
                        
                        if not full_url or full_url in found_urls:
                            continue
                            
                        # 过滤无效链接
                        if not self._is_valid_article_url(full_url, base_url):
                            continue
                            
                        found_urls.add(full_url)
                        articles.append({
                            'title': title[:200],  # 限制标题长度
                            'url': full_url,
                            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                    except Exception as e:
                        logger.debug(f"处理单个链接时出错: {e}")
                        continue
                
                # 如果已经找到足够的文章，停止尝试其他选择器
                if len(articles) >= min(max_articles, 10):
                    break
                    
            except Exception as e:
                logger.debug(f"选择器 '{selector}' 执行失败: {e}")
                continue
        
        logger.info(f"共提取到 {len(articles)} 篇文章")
        return articles
    
    def _normalize_url(self, href: str, base_url: str) -> Optional[str]:
        """规范化URL"""
        if not href:
            return None
            
        # 跳过锚点和javascript链接
        if href.startswith('#') or href.startswith('javascript:'):
            return None
            
        # 处理相对链接
        if href.startswith('/'):
            return urljoin(base_url, href)
        elif href.startswith('http'):
            return href
        else:
            # 相对路径
            return urljoin(base_url, href)
    
    def _is_valid_article_url(self, url: str, base_url: str) -> bool:
        """判断是否是有效的文章URL"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_url)
            
            # 只允许同域或子域的链接
            if not (parsed.netloc == base_parsed.netloc or 
                   parsed.netloc.endswith(f'.{base_parsed.netloc}')):
                return False
            
            # 跳过静态资源
            static_extensions = ['.css', '.js', '.jpg', '.png', '.gif', '.pdf', '.zip']
            if any(url.lower().endswith(ext) for ext in static_extensions):
                return False
            
            # 跳过常见的非文章页面
            skip_patterns = [
                '/login', '/register', '/signup', '/contact', 
                '/about', '/privacy', '/terms', '/search',
                '/tag/', '/category/', '/author/'
            ]
            
            path = parsed.path.lower()
            if any(pattern in path for pattern in skip_patterns):
                return False
            
            return True
            
        except Exception:
            return False

# 全局爬虫实例
crawler_instance = LinkCrawler()

async def crawl_website(url: str, max_articles: int = 50) -> Dict:
    """
    爬取网站文章的便捷函数
    
    Args:
        url: 目标网站URL
        max_articles: 最大文章数
        
    Returns:
        爬取结果字典
    """
    return await crawler_instance.crawl_website_articles(url, max_articles)