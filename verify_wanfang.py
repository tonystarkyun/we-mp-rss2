import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=120000)
    url = 'https://s.wanfangdata.com.cn/paper?q=%E4%BA%9A%E9%BA%BB%E7%B1%BD&p=1'
    result = await crawler.crawl_website_articles(url, max_articles=5)
    print('success:', result['success'])
    print('total:', result['total_found'])
    print('error:', result['error'])
    for idx, article in enumerate(result['articles'], 1):
        print(idx, article['title'], '=>', article['url'])

asyncio.run(main())
