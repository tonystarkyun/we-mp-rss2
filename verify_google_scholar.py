import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=180000)
    url = 'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=flaxseed&btnG='
    result = await crawler.crawl_website_articles(url, max_articles=5)
    print('success:', result['success'])
    print('total:', result['total_found'])
    print('error:', result['error'])
    for idx, article in enumerate(result['articles'], 1):
        print(idx, article.get('title'), '=>', article.get('url'))

asyncio.run(main())
