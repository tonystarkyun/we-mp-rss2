import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=120000)
    target_url = "https://www.statista.com/search/?q=flaxseed&p=1&sortMethod=publicationDate"
    result = await crawler.crawl_website_articles(target_url, max_articles=5)

    print("success:", result.get("success"))
    print("total_found:", result.get("total_found"))
    print("error:", result.get("error"))
    for idx, article in enumerate(result.get("articles", []), 1):
        print(f"{idx}. {article['title']} => {article['url']}")

if __name__ == "__main__":
    asyncio.run(main())
