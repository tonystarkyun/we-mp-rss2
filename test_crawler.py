# test_crawler.py - 链接管理爬虫测试脚本
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import json
import time
from typing import List, Dict, Optional

class LinkCrawler:
    """通用链接爬虫类"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        
    def extract_articles(self, url: str, max_articles: int = 10) -> List[Dict[str, str]]:
        """
        从指定URL爬取文章链接和标题
        
        Args:
            url: 目标网站URL
            max_articles: 最大抓取文章数
            
        Returns:
            List[Dict]: 包含title和url的字典列表
        """
        articles = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                print(f"正在访问: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # 等待页面加载
                time.sleep(2)
                
                # 通用的文章链接选择器（按优先级排序）
                selectors = [
                    'article a',  # 文章容器内的链接
                    'h1 a, h2 a, h3 a',  # 标题链接
                    '.title a',  # 标题类链接  
                    '.post-title a',  # 文章标题链接
                    'a[href*="/article/"], a[href*="/post/"]',  # 包含article或post的链接
                    '.entry-title a',  # 入口标题链接
                    'a[title]',  # 有title属性的链接
                ]
                
                found_links = []
                
                for selector in selectors:
                    try:
                        # 获取链接元素
                        links = page.query_selector_all(selector)
                        if links:
                            print(f"使用选择器 '{selector}' 找到 {len(links)} 个链接")
                            
                            for link in links[:max_articles]:
                                try:
                                    title = link.inner_text().strip()
                                    href = link.get_attribute('href')
                                    
                                    if title and href:
                                        # 处理相对链接
                                        if href.startswith('/'):
                                            from urllib.parse import urljoin
                                            href = urljoin(url, href)
                                        elif href.startswith('#'):
                                            continue  # 跳过锚点链接
                                        elif not href.startswith('http'):
                                            continue  # 跳过其他非HTTP链接
                                            
                                        # 去重
                                        if href not in [item['url'] for item in found_links]:
                                            found_links.append({
                                                'title': title,
                                                'url': href
                                            })
                                            
                                            if len(found_links) >= max_articles:
                                                break
                                                
                                except Exception as e:
                                    print(f"处理链接时出错: {e}")
                                    continue
                            
                            if found_links:
                                break  # 找到链接就停止尝试其他选择器
                                
                    except Exception as e:
                        print(f"选择器 '{selector}' 失败: {e}")
                        continue
                
                articles = found_links
                
            except Exception as e:
                print(f"爬取过程中出错: {e}")
                
            finally:
                browser.close()
                
        return articles

def test_crawler():
    """测试爬虫功能"""
    crawler = LinkCrawler(headless=True)
    
    # 测试多个不同类型的网站
    test_sites = [
        "https://news.ycombinator.com",  # Hacker News
        "https://www.reddit.com/r/programming/",  # Reddit编程板块
        "https://dev.to",  # Dev.to技术博客
    ]
    
    for site in test_sites:
        print(f"\n{'='*50}")
        print(f"测试网站: {site}")
        print(f"{'='*50}")
        
        try:
            articles = crawler.extract_articles(site, max_articles=5)
            
            if articles:
                print(f"[成功] 成功爬取到 {len(articles)} 篇文章:")
                for i, article in enumerate(articles, 1):
                    print(f"  {i}. {article['title'][:100]}...")
                    print(f"     URL: {article['url']}")
                    print()
            else:
                print("[失败] 未能爬取到文章")
                
        except Exception as e:
            print(f"[失败] 爬取失败: {e}")

if __name__ == "__main__":
    print("[测试] 链接管理爬虫功能测试")
    print("=" * 60)
    test_crawler()
    print("\n[完成] 测试完成！")