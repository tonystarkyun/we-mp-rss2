import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=120000)
    url = 'https://www.reuters.com/site-search/?query=flaxseed'
    result = await crawler.crawl_website_articles(url, max_articles=5)
    print('success:', result['success'])
    print('total:', result['total_found'])
    print('error:', result['error'])
    for idx, article in enumerate(result['articles'], 1):
        print(idx, article['title'], '=>', article['url'])

asyncio.run(main())
