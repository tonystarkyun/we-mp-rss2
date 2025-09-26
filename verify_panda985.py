import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=180000)
    url = 'https://sc.panda985.com/scholar?q=%E4%BA%9A%E9%BA%BB%E7%B1%BD'
    result = await crawler.crawl_website_articles(url, max_articles=5)
    print('success:', result['success'])
    print('total:', result['total_found'])
    print('error:', result['error'])
    for idx, article in enumerate(result['articles'], 1):
        print(idx, article.get('title'), '=>', article.get('url'))

asyncio.run(main())
