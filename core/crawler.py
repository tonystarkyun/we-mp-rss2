# core/crawler.py - 链接管理爬虫服务
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
import asyncio
import time
import os
import sys
import shutil
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, unquote_plus
import re
import logging

logger = logging.getLogger(__name__)

FOODNAVIGATOR_QUERYLY_KEY = '162cd04ba9044343'
FOODNAVIGATOR_EXT_FIELDS = 'eventStartDate,creator,subtype,firstPubDate,sectionSupplier,freeByLine,imageresizer,promo_image,resizerv2_id,resizerv2_auth,resizerv2_mimetype,subheadline'
FOODNAVIGATOR_BATCH_SIZE = 20

class LinkCrawler:
    """链接管理爬虫服务"""
    
    def __init__(self, headless: bool = True, timeout: int = 300000):
        self.headless = headless
        self.timeout = timeout
        self.browser_executable = self._find_browser_executable()
        
    async def crawl_website_articles(self, url: str, max_articles: int = 50) -> Dict:
        """
        爬取网站的文章列??
        
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
                parsed_target_url = urlparse(url)
                target_headless = self.headless
                if parsed_target_url.netloc.endswith('reuters.com') and target_headless:
                    target_headless = False
                    logger.info('Reuters domain detected; switching to headful mode to satisfy anti-bot checks')
                # 根据环境选择浏览器启动方??
                if self.browser_executable:
                    # 使用系统浏览??
                    logger.info("Using system browser: %s", self.browser_executable)
                    browser = await p.chromium.launch(
                        executable_path=self.browser_executable,
                        headless=target_headless,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-features=VizDisplayCompositor'
                        ]
                    )
                else:
                    # 使用Playwright内置浏览??
                    logger.info("Using bundled Playwright browser")
                    browser = await p.chromium.launch(headless=target_headless)
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                logger.info("Crawling site: %s", url)
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
            logger.error("Error while crawling: %s", e)
            result['error'] = str(e)
            
        return result
    
    def _find_browser_executable(self) -> Optional[str]:
        """Locate an available browser executable on the host."""
        
        # 如果是PyInstaller环境，优先查找系统安装的Chrome
        if hasattr(sys, '_MEIPASS'):
            logger.info("Detected PyInstaller environment, searching for system browser")
            
            # Windows Chrome路径
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                # Edge浏览器作为备??
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    logger.info("Found browser executable: %s", chrome_path)
                    return chrome_path
            
            logger.warning("No system Chrome or Edge browser found")
            return None
        
        # 开发环境使用Playwright自带的浏览器
        logger.info("Development environment detected; using bundled Playwright browser")
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
            logger.warning("Error extracting site info: %s", e)
            
        return info
    
    async def _extract_foodnavigator_search(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """Special handling for FoodNavigator search pages."""
        articles: List[Dict[str, str]] = []
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        keyword = ''
        for key in ('query',):
            values = query_params.get(key)
            if values:
                keyword = unquote_plus((values[0] or '').strip())
                if keyword:
                    break

        if not keyword:
            return articles

        sort_param = ''
        for key in ('sort', 'sortby'):
            value = query_params.get(key, [None])[0]
            if value:
                sort_param = value.lower()
                break

        start_index = 0
        for key in ('endindex', 'index', 'offset', 'start'):
            value = query_params.get(key, [None])[0]
            if value:
                try:
                    start_index = max(int(value), 0)
                    break
                except ValueError:
                    continue

        if start_index == 0:
            page_value = query_params.get('page', [None])[0]
            if page_value:
                try:
                    page_number = max(int(page_value), 1)
                    start_index = (page_number - 1) * FOODNAVIGATOR_BATCH_SIZE
                except ValueError:
                    start_index = 0

        faceted_key = query_params.get('facetedkey', [None])[0]
        faceted_value = query_params.get('facetedvalue', [None])[0]
        date_range = query_params.get('daterange', [None])[0]

        offset = max(start_index, 0)
        user_agent = await page.evaluate('() => navigator.userAgent')

        while len(articles) < max_articles:
            batch = min(max_articles - len(articles), FOODNAVIGATOR_BATCH_SIZE)
            params = {
                'queryly_key': FOODNAVIGATOR_QUERYLY_KEY,
                'query': keyword,
                'endindex': str(offset),
                'batchsize': str(batch),
                'showfaceted': 'true',
                'extendeddatafields': FOODNAVIGATOR_EXT_FIELDS,
                'timezoneoffset': '0'
            }

            if sort_param == 'date':
                params['sort'] = 'date'

            if faceted_key and faceted_value:
                params['facetedkey'] = faceted_key
                params['facetedvalue'] = faceted_value

            if date_range:
                params['daterange'] = date_range

            response = await page.context.request.get(
                'https://api.queryly.com/json.aspx',
                params=params,
                headers={
                    'User-Agent': user_agent,
                    'Accept': 'application/json',
                    'Referer': base_url
                }
            )

            if not response.ok:
                logger.warning('FoodNavigator search API returned non-200 response: %s', response.status)
                break

            try:
                data = json.loads(await response.text())
            except json.JSONDecodeError as exc:
                logger.warning('Failed to decode FoodNavigator search payload: %s', exc)
                break

            items = data.get('items') or []
            if not items:
                break

            for item in items:
                if len(articles) >= max_articles:
                    break

                link = (item.get('link') or '').strip()
                if not link:
                    continue

                if link.startswith('//'):
                    article_url = 'https:' + link
                elif link.startswith('http'):
                    article_url = link
                else:
                    article_url = urljoin('https://www.foodnavigator.com', link)

                title = (item.get('title') or '').strip()
                if not title:
                    title = article_url

                summary = (item.get('subheadline') or item.get('description') or '').strip()
                published = (item.get('firstPubDate') or item.get('pubdate') or '').strip()
                creator = (item.get('creator') or '').strip()

                articles.append({
                    'title': title[:200],
                    'url': article_url,
                    'summary': summary[:500] if summary else '',
                    'author': creator,
                    'published_at': published,
                    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                })

            metadata = data.get('metadata') or {}
            next_index = metadata.get('endindex')
            try:
                next_index_int = int(next_index)
            except (TypeError, ValueError):
                next_index_int = offset + len(items)

            if next_index_int <= offset or len(articles) >= max_articles:
                break

            offset = next_index_int

        return articles

    async def _extract_wanfang_search(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """Special handling for Wanfang search pages."""
        articles: List[Dict[str, str]] = []

        try:
            await page.wait_for_selector('div.normal-list', timeout=10000)
        except Exception:
            return articles

        raw_items = await page.evaluate(
            """() => Array.from(document.querySelectorAll('div.normal-list')).map(el => ({
                id: (el.querySelector('.title-id-hidden')?.textContent || '').trim(),
                title: (el.querySelector('.title')?.textContent || '').trim(),
                summary: (el.querySelector('.abstract-area')?.innerText || '').trim(),
                authors: Array.from(el.querySelectorAll('.author-area .authors')).map(node => node.textContent.trim()).filter(Boolean),
                typeLabel: el.querySelector('.essay-type')?.textContent?.trim() || '',
                keywords: Array.from(el.querySelectorAll('.keywords-area .keywords-list')).map(node => node.textContent.trim()).filter(Boolean)
            }))"""
        )

        if not raw_items:
            return articles

        type_map = {
            'periodical': 'perio',
            'perio': 'perio',
            'degree': 'degree',
            'thesis': 'degree',
            'dissertation': 'degree',
            'conference': 'conference',
            'patent': 'patent',
            'std': 'std',
            'standard': 'std',
            'tech': 'tech',
            'report': 'tech',
            'achievement': 'tech',
            'nstr': 'nstr',
            'localchronicle': 'localchronicle',
            'law': 'law',
            'policy': 'policy',
            'video': 'video'
        }

        for item in raw_items:
            record_id = (item.get('id') or '').strip()
            if not record_id:
                continue

            prefix = record_id.split('_', 1)[0].lower() if '_' in record_id else record_id.lower()
            type_param = type_map.get(prefix, prefix or 'perio')
            detail_url = f"https://www.wanfangdata.com.cn/details/detail.do?_type={type_param}&id={record_id}"

            title = (item.get('title') or '').strip() or detail_url

            authors = item.get('authors') or []
            source_info = ''
            if authors:
                tail = authors[-1]
                if any(ch.isdigit() for ch in tail):
                    source_info = tail
                    authors = authors[:-1]

            summary = (item.get('summary') or '').strip()
            if summary.startswith('摘要'):
                summary = summary[2:].lstrip('：:').strip()

            keywords = item.get('keywords') or []
            type_label = item.get('typeLabel') or ''

            articles.append({
                'title': title[:200],
                'url': detail_url,
                'summary': summary[:500] if summary else '',
                'authors': authors,
                'source': source_info,
                'type': type_label,
                'keywords': keywords,
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            })

            if len(articles) >= max_articles:
                break

        return articles

    async def _extract_reuters_search(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """Special handling for Reuters site search pages."""
        articles: List[Dict[str, str]] = []
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        keyword = ''
        for key in ('query', 'blob'):
            values = query_params.get(key)
            if values:
                keyword = (values[0] or '').strip()
                if keyword:
                    break

        if not keyword:
            return articles

        size = max(1, min(max_articles, 20))
        payload = {
            'keyword': keyword,
            'offset': 0,
            'orderby': 'display_date:desc',
            'size': size,
            'website': 'reuters'
        }

        fetch_script = """async ({url, payload}) => {
            const params = new URLSearchParams();
            params.set('query', JSON.stringify(payload));
            params.set('d', '318');
            params.set('mxId', '00000000');
            params.set('_website', 'reuters');
            const response = await fetch(`${url}?${params.toString()}`, {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            return { status: response.status, text: await response.text() };
        }"""

        try:
            fetch_result = await page.evaluate(fetch_script, {
                'url': 'https://www.reuters.com/pf/api/v3/content/fetch/articles-by-search-v2',
                'payload': payload
            })
        except Exception as exc:
            logger.warning('Failed to query Reuters search API via page context: %s', exc)
            return articles

        status = fetch_result.get('status') if isinstance(fetch_result, dict) else None
        if status != 200:
            logger.warning('Reuters search API returned non-200 response: %s', status)
            return articles

        raw_text = (fetch_result.get('text') or '').strip()
        if not raw_text:
            return articles

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning('Failed to decode Reuters search payload: %s', exc)
            return articles

        items = data.get('result', {}).get('articles') or []
        base_domain = 'https://www.reuters.com'

        for item in items:
            if len(articles) >= max_articles:
                break

            title = (item.get('title') or item.get('headline') or '').strip()
            description = (item.get('description') or '').strip()
            if not title and description:
                title = description[:200]

            url_path = (item.get('canonical_url') or item.get('url') or '').strip()
            if not url_path:
                continue

            if url_path.startswith('http'):
                article_url = url_path
            else:
                article_url = urljoin(base_domain, url_path)

            if not title:
                title = article_url

            articles.append({
                'title': title[:200],
                'url': article_url,
                'published_at': item.get('published_time'),
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            })

        return articles

    async def _extract_statista_search(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """专门处理 Statista 搜索结果页"""
        articles: List[Dict[str, str]] = []
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        # 构建请求参数，保留原有查询条件并强制返回 JSON
        api_params = [('asJsonResponse', '1')]
        for key, values in query_params.items():
            for value in values:
                if value is not None:
                    api_params.append((key, value))

        # Statista 接口在缺少部分参数时会回退默认值，这里补齐关键参数
        defaults = {
            'q': '',
            'p': '1',
            'sortMethod': 'relevance',
            'accuracy': 'and',
            'interval': '0',
            'idRelevance': '0',
            'isRegionPref': '-1',
            'isoregion': '0',
            'language': '0',
        }
        existing_keys = {key for key, _ in api_params}
        for key, value in defaults.items():
            if key not in existing_keys:
                api_params.append((key, value))

        try:
            query_string = urlencode(api_params, doseq=True)
            target_url = f"https://www.statista.com/search/?{query_string}"
            fetch_result = await page.evaluate(
                "async (targetUrl) => {\n                    const response = await fetch(targetUrl, {\n                        headers: {\n                            'Accept': 'application/json, text/plain, */*',\n                            'X-Requested-With': 'XMLHttpRequest'\n                        },\n                        credentials: 'include'\n                    });\n                    const text = await response.text();\n                    return { status: response.status, text };\n                }",
                target_url
            )
            status = fetch_result.get('status') if fetch_result else None
            if status != 200:
                logger.warning("Statista API non-2xx response: %s", status)
                return articles

            raw_text = (fetch_result.get('text') or '').strip()
            if not raw_text:
                return articles

            data = json.loads(raw_text)
            results = data.get('results', {})
            main_results = results.get('mainselect') or []
            entity_ids = data.get('justSmart', {}).get('actionParameters', {}).get('entityIds', {})
            id_to_name = {str(v): k for k, v in entity_ids.items()}

            for item in main_results:
                if len(articles) >= max_articles:
                    break

                identity = str(item.get('identity') or '')
                entity_name = id_to_name.get(identity)
                article_url = self._build_statista_url(item, entity_name)
                if not article_url:
                    continue

                title_fields = [
                    item.get('graphheader'),
                    item.get('pagetitle'),
                    item.get('catchline'),
                    item.get('title'),
                    item.get('pseudotitle'),
                    item.get('subtitle'),
                ]
                title = next((t.strip() for t in title_fields if t), None)
                if not title:
                    title = article_url

                articles.append({
                    'title': title[:200],
                    'url': article_url,
                    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                })

            return articles
        except Exception as exc:
            logger.warning("Failed to parse Statista search results: %s", exc)
            return articles


    async def _solve_panda_slider(self, page) -> bool:
        """Attempt to bypass Panda985 slider challenge."""
        try:
            slider = await page.wait_for_selector('.slider', timeout=5000)
        except Exception:
            return False

        try:
            handler = await page.wait_for_selector('#slider .handler', timeout=2000)
        except Exception:
            return False

        slider_box = await slider.bounding_box()
        handler_box = await handler.bounding_box()
        if not slider_box or not handler_box:
            return False

        await page.wait_for_timeout(500)

        start_x = handler_box['x'] + handler_box['width'] / 2
        start_y = handler_box['y'] + handler_box['height'] / 2
        max_travel = slider_box['width'] - handler_box['width']
        if max_travel <= 0:
            return False
        target_x = start_x + max_travel
        mid_x = start_x + max_travel * 0.82

        try:
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(mid_x, start_y, steps=15)
            await page.wait_for_timeout(120)
            await page.mouse.move(target_x, start_y, steps=10)
            await page.mouse.up()
        except Exception as exc:
            logger.debug('Failed to simulate Panda985 slider drag: %s', exc)
            return False

        try:
            await page.wait_for_load_state('networkidle', timeout=8000)
        except Exception:
            await page.wait_for_timeout(2000)

        try:
            await page.wait_for_selector('#gs_res_ccl', timeout=6000)
            return True
        except Exception:
            return False

    async def _extract_panda985_scholar(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """Special handling for Panda985 scholar search pages."""
        articles: List[Dict[str, str]] = []

        slider_passed = await self._solve_panda_slider(page)
        if slider_passed:
            try:
                await page.wait_for_selector('#gs_res_ccl .gs_r', timeout=8000)
            except Exception:
                logger.debug('Panda985 results failed to appear after slider resolution')
                return articles
        else:
            try:
                await page.wait_for_selector('#gs_res_ccl .gs_r', timeout=8000)
            except Exception:
                return articles

        raw_items = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('#gs_res_ccl .gs_r.gs_or')).map(node => {
                const titleLink = node.querySelector('h3.gs_rt a');
                const titleText = titleLink ? titleLink.innerText : (node.querySelector('h3.gs_rt')?.innerText || '');
                const downloadLink = node.querySelector('.down_sci');
                const clusterLink = node.querySelector('a.gs_nph[href*="cluster="]');
                return {
                    title: titleText.trim(),
                    url: titleLink ? titleLink.href : '',
                    summary: (node.querySelector('.gs_rs')?.innerText || '').trim(),
                    meta: (node.querySelector('.gs_a')?.innerText || '').trim(),
                    badge: (node.querySelector('.gs_ctg2')?.innerText || '').trim(),
                    pdf: (node.querySelector('.gs_ggsd a')?.href || '').trim(),
                    download: downloadLink ? (downloadLink.getAttribute('data-gp') || downloadLink.getAttribute('href') || '') : '',
                    cluster: clusterLink ? clusterLink.getAttribute('href') : ''
                };
            }).filter(item => item.title);
        }""")

        seen_urls = set()
        for item in raw_items:
            if len(articles) >= max_articles:
                break

            url = (item.get('url') or '').strip()
            if not url:
                download_url = (item.get('download') or '').strip()
                if download_url:
                    if download_url.startswith('http'):
                        url = download_url
                    else:
                        url = urljoin(base_url, download_url)
            if not url:
                cluster_url = (item.get('cluster') or '').strip()
                if cluster_url:
                    url = urljoin(base_url, cluster_url)
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = (item.get('title') or url).strip()
            summary = ' '.join((item.get('summary') or '').split())
            meta = ' '.join((item.get('meta') or '').split())

            article: Dict[str, str] = {
                'title': title[:200],
                'url': url,
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            if summary:
                article['summary'] = summary[:500]

            if meta:
                article['source'] = meta
                match = re.search(r'(19|20)\d{2}', meta)
                if match:
                    article['published_at'] = match.group(0)

            badge = (item.get('badge') or '').strip()
            if badge:
                article['type'] = badge

            pdf_url = (item.get('pdf') or '').strip()
            if pdf_url:
                article['pdf_url'] = pdf_url

            articles.append(article)

        return articles

    async def _extract_google_scholar(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """Special handling for Google Scholar search pages."""
        articles: List[Dict[str, str]] = []

        try:
            await page.wait_for_selector('#gs_res_ccl .gs_r', timeout=8000)
        except Exception:
            captcha_node = await page.query_selector('form#captcha-form, iframe[src*="recaptcha"], #recaptcha')
            if captcha_node:
                logger.warning('Google Scholar presented captcha; aborting extraction')
            else:
                logger.debug('Google Scholar results failed to appear in time')
            return articles

        raw_items = await page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('#gs_res_ccl .gs_r.gs_or'));
            return rows.map(node => {
                const titleLink = node.querySelector('h3.gs_rt a');
                const titleText = titleLink ? titleLink.innerText : (node.querySelector('h3.gs_rt')?.innerText || '');
                const pdfLink = node.querySelector('.gs_or_ggsm a, .gs_or_ggsb a');
                const actionLinks = Array.from(node.querySelectorAll('.gs_fl a'));
                const citeLink = actionLinks.find(link => /Cited by/i.test(link.innerText));
                const relatedLink = actionLinks.find(link => /Related articles/i.test(link.innerText));
                return {
                    title: titleText.trim(),
                    url: titleLink ? titleLink.href : '',
                    summary: (node.querySelector('.gs_rs')?.innerText || '').trim(),
                    meta: (node.querySelector('.gs_a')?.innerText || '').trim(),
                    pdf: pdfLink ? pdfLink.href : '',
                    citeText: citeLink ? citeLink.innerText.trim() : '',
                    citeUrl: citeLink ? citeLink.href : '',
                    relatedUrl: relatedLink ? relatedLink.href : ''
                };
            }).filter(item => item.title);
        }""")

        seen_urls = set()
        base = 'https://scholar.google.com'

        for item in raw_items:
            if len(articles) >= max_articles:
                break

            url = (item.get('url') or '').strip()
            if not url:
                continue
            if url.startswith('/'):
                url = urljoin(base, url)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = (item.get('title') or url).strip()
            summary = ' '.join((item.get('summary') or '').split())
            meta = ' '.join((item.get('meta') or '').split())

            article: Dict[str, str] = {
                'title': title[:200],
                'url': url,
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            if summary:
                article['summary'] = summary[:500]

            if meta:
                article['source'] = meta
                year_match = re.search(r'(19|20)\d{2}', meta)
                if year_match:
                    article['published_at'] = year_match.group(0)

            pdf_url = (item.get('pdf') or '').strip()
            if pdf_url:
                article['pdf_url'] = pdf_url if pdf_url.startswith('http') else urljoin(base, pdf_url)

            cite_text = (item.get('citeText') or '').strip()
            if cite_text:
                m = re.search(r'(\d+)', cite_text)
                if m:
                    article['citations'] = int(m.group(1))
                cite_url = (item.get('citeUrl') or '').strip()
                if cite_url:
                    article['citations_url'] = cite_url if cite_url.startswith('http') else urljoin(base, cite_url)

            related_url = (item.get('relatedUrl') or '').strip()
            if related_url:
                article['related_url'] = related_url if related_url.startswith('http') else urljoin(base, related_url)

            articles.append(article)

        return articles

    def _build_statista_url(self, item: Dict, entity_name: Optional[str]) -> Optional[str]:
        """根据实体类型构建 Statista 详情页地址"""
        if not item:
            return None

        slug = (item.get('uri') or item.get('url') or '').strip('/')
        if not slug:
            return None

        idcontent = item.get('idcontent')
        base = 'https://www.statista.com'

        entity_to_path = {
            'statistic': 'statistics',
            'forecast': 'statistics',
            'infographic': 'infographic',
            'topic': 'topics',
            'study': 'study',
            'dossier': 'study',
            'dossierplus': 'study',
            'toplist': 'study',
            'survey': 'study',
            'marketstudy': 'study',
            'branchreport': 'study',
            'brandreport': 'study',
            'companyreport': 'study',
            'countryreport': 'study',
        }

        path_prefix = entity_to_path.get(entity_name)
        if path_prefix and idcontent:
            return f"{base}/{path_prefix}/{idcontent}/{slug}/"

        # 回退到直接拼接 slug
        if slug.startswith('http'):
            return slug

        return f"{base}/{slug}/"

    async def _extract_articles(self, page, base_url: str, max_articles: int) -> List[Dict[str, str]]:
        """提取文章列表"""
        articles = []
        
        parsed_url = urlparse(base_url)

        if parsed_url.netloc.endswith('wanfangdata.com.cn') and parsed_url.path.startswith('/paper'):
            wanfang_articles = await self._extract_wanfang_search(page, base_url, max_articles)
            if wanfang_articles:
                return wanfang_articles

        if parsed_url.netloc.endswith('foodnavigator.com') and parsed_url.path.startswith('/search'):
            foodnavigator_articles = await self._extract_foodnavigator_search(page, base_url, max_articles)
            if foodnavigator_articles:
                return foodnavigator_articles

        if parsed_url.netloc.endswith('reuters.com'):
            reuters_articles = await self._extract_reuters_search(page, base_url, max_articles)
            if reuters_articles:
                return reuters_articles

        if parsed_url.netloc.endswith('panda985.com') and parsed_url.path.startswith('/scholar'):
            panda_articles = await self._extract_panda985_scholar(page, base_url, max_articles)
            if panda_articles:
                return panda_articles

        if parsed_url.netloc.endswith('google.com') and parsed_url.path.startswith('/scholar'):
            google_articles = await self._extract_google_scholar(page, base_url, max_articles)
            if google_articles:
                return google_articles

        if parsed_url.netloc.endswith('statista.com') and parsed_url.path.startswith('/search'):
            statista_articles = await self._extract_statista_search(page, base_url, max_articles)
            if statista_articles:
                return statista_articles

        
        # 通用文章选择器策略（按优先级排序??
        selectors = [
            # 新闻和博客网站常用选择??
            'article h1 a, article h2 a, article h3 a',
            'article a[href]',
            '.post-title a, .entry-title a',
            '.article-title a, .news-title a',
            'h1 a, h2 a, h3 a',
            '.title a',
            # 列表页面选择??
            'li a[href]',
            'ul a[href]',
            # 通用链接选择??
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
                    
                logger.info("Selector '%s' yielded %d candidate links", selector, len(links))
                
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
                        logger.debug("Error while processing a single link: %s", e)
                        continue
                
                # 如果已经找到足够的文章，停止尝试其他选择??
                if len(articles) >= min(max_articles, 10):
                    break
                    
            except Exception as e:
                logger.debug("Selector '%s' failed: %s", selector, e)
                continue
        
        logger.info("Extracted %d potential articles", len(articles))
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
            
            # 只允许同域或子域的链??
            if not (parsed.netloc == base_parsed.netloc or 
                   parsed.netloc.endswith(f'.{base_parsed.netloc}')):
                return False
            
            # 跳过静态资??
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
    爬取网站文章的便捷函??
    
    Args:
        url: 目标网站URL
        max_articles: 最大文章数
        
    Returns:
        爬取结果字典
    """
    return await crawler_instance.crawl_website_articles(url, max_articles)

