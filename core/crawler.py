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
        
        try:
            async with async_playwright() as p:
                # 统一使用Firefox浏览器，开发和打包环境完全一致
                logger.info("使用Firefox浏览器")
                browser = await p.firefox.launch(headless=self.headless)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'
                )
                page = await context.new_page()
                
                logger.info(f"正在爬取网站: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                
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
        
        # 无论在什么环境，都使用Firefox浏览器
        # 这样打包环境和开发环境行为完全一致
        logger.info("使用Firefox浏览器（开发和打包环境统一行为）")
        return None
        
        # 开发环境使用Playwright自带的浏览器
        logger.info("开发环境，使用Firefox浏览器")
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
                        
                        # 尝试提取发布时间
                        publish_time = await self._extract_publish_time(page, link)
                        
                        articles.append({
                            'title': title[:200],  # 限制标题长度
                            'url': full_url,
                            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'publish_time_timestamp': publish_time
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
        
        # 按发布时间降序排序（最新的在前面）
        articles = await self._sort_articles_by_time(articles)
        
        return articles
    
    async def _extract_publish_time(self, page, link_element) -> str:
        """尝试提取发布时间"""
        try:
            # 尝试在链接附近查找时间信息
            parent = await link_element.locator('xpath=..').first.element_handle()
            if parent:
                # 常见的时间选择器
                time_selectors = [
                    'time',
                    '.date', '.time', '.published', '.post-date', '.publish-time',
                    '.entry-date', '.article-date', '.news-date',
                    '[datetime]', '[data-time]', '[data-date]',
                    '.meta-date', '.timestamp'
                ]
                
                for selector in time_selectors:
                    try:
                        time_elem = await parent.query_selector(selector)
                        if time_elem:
                            # 尝试获取datetime属性
                            datetime_attr = await time_elem.get_attribute('datetime')
                            if datetime_attr:
                                return self._parse_time_string(datetime_attr)
                            
                            # 获取文本内容
                            time_text = await time_elem.inner_text()
                            if time_text:
                                parsed_time = self._parse_time_string(time_text.strip())
                                if parsed_time:
                                    return parsed_time
                    except Exception:
                        continue
            
            return ""  # 无法提取时间时返回空字符串
            
        except Exception as e:
            logger.debug(f"提取发布时间失败: {e}")
            return ""
    
    def _parse_time_string(self, time_str: str) -> str:
        """解析时间字符串，返回本地时区时间戳"""
        import re
        from datetime import datetime, timezone
        import time
        
        if not time_str:
            return ""
            
        try:
            # 清理时间字符串
            time_str = re.sub(r'[^\d\-\/:\s年月日时分秒]', '', time_str.strip())
            
            # 常见时间格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
            ]
            
            # 尝试解析时间
            for fmt in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    timestamp = int(dt.timestamp())
                    # 确保时间戳有效（不能是0或负数）
                    if timestamp > 0:
                        return str(timestamp)
                except ValueError:
                    continue
                    
            # 处理相对时间（如"2小时前"，"昨天"等）
            now = datetime.now()
            if '小时前' in time_str or 'hours ago' in time_str.lower():
                hours = re.findall(r'\d+', time_str)
                if hours:
                    from datetime import timedelta
                    dt = now - timedelta(hours=int(hours[0]))
                    timestamp = int(dt.timestamp())
                    if timestamp > 0:
                        return str(timestamp)
            
            if '天前' in time_str or 'days ago' in time_str.lower():
                days = re.findall(r'\d+', time_str)
                if days:
                    from datetime import timedelta
                    dt = now - timedelta(days=int(days[0]))
                    timestamp = int(dt.timestamp())
                    if timestamp > 0:
                        return str(timestamp)
            
            return ""
            
        except Exception as e:
            logger.debug(f"解析时间字符串失败 '{time_str}': {e}")
            return ""
    
    async def _sort_articles_by_time(self, articles: List[Dict]) -> List[Dict]:
        """按发布时间排序文章（最新的在前）"""
        try:
            def sort_key(article):
                timestamp = article.get('publish_time_timestamp', '')
                if timestamp and timestamp.isdigit():
                    return int(timestamp)
                return 0  # 无时间信息的排在最后
            
            # 按时间戳降序排序
            sorted_articles = sorted(articles, key=sort_key, reverse=True)
            
            logger.info("文章已按发布时间排序")
            return sorted_articles
            
        except Exception as e:
            logger.warning(f"文章时间排序失败: {e}")
            return articles  # 排序失败时返回原列表
    
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
