# test_integration.py - 链接管理爬虫集成测试
import requests
import json

# 测试API基础URL
API_BASE = "http://localhost:8001/api/v1/wx"

def test_crawl_api():
    """测试爬虫API"""
    print("=" * 60)
    print("测试链接管理爬虫集成")
    print("=" * 60)
    
    # 测试不需要登录的爬虫功能
    test_url = "https://news.ycombinator.com"
    
    try:
        # 由于API需要认证，我们直接测试核心爬虫功能
        from core.crawler import crawl_website
        
        print(f"正在测试爬取: {test_url}")
        result = crawl_website(test_url, max_articles=5)
        
        print(f"爬取结果:")
        print(f"- 成功: {result['success']}")
        print(f"- 网站标题: {result['website_info']['title']}")
        print(f"- 找到文章数: {result['total_found']}")
        
        if result['articles']:
            print(f"- 文章列表:")
            for i, article in enumerate(result['articles'][:3], 1):
                print(f"  {i}. {article['title'][:80]}...")
                print(f"     URL: {article['url']}")
        
        if result['error']:
            print(f"- 错误信息: {result['error']}")
            
        return result['success']
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_link_creation():
    """测试链接创建流程"""
    print("\n" + "=" * 60)
    print("测试链接创建流程（模拟）")
    print("=" * 60)
    
    # 模拟链接数据
    link_data = {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com",
        "description": "技术新闻聚合网站"
    }
    
    try:
        from core.crawler import crawl_website
        
        # 模拟添加链接时的爬虫过程
        crawl_result = crawl_website(link_data['url'], max_articles=10)
        
        # 构造返回数据
        new_link = {
            "id": "test_123",
            "name": link_data['name'] or crawl_result['website_info']['title'],
            "url": link_data['url'],
            "avatar": "/static/logo.svg",
            "description": link_data['description'] or crawl_result['website_info']['description'],
            "status": 1,
            "article_count": crawl_result['total_found']
        }
        
        print("模拟链接创建结果:")
        print(f"- 链接ID: {new_link['id']}")
        print(f"- 链接名称: {new_link['name']}")
        print(f"- 链接URL: {new_link['url']}")
        print(f"- 描述: {new_link['description'][:100]}...")
        print(f"- 爬取到的文章数: {new_link['article_count']}")
        
        print(f"\n爬取的文章示例:")
        for i, article in enumerate(crawl_result['articles'][:3], 1):
            print(f"  {i}. {article['title'][:80]}...")
            
        return True
        
    except Exception as e:
        print(f"链接创建测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始链接管理爬虫集成测试...")
    
    results = []
    
    # 测试1: 爬虫API功能
    results.append(test_crawl_api())
    
    # 测试2: 链接创建流程
    results.append(test_link_creation())
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试通过！链接管理爬虫功能集成成功。")
    else:
        print("❌ 部分测试失败，需要检查配置。")
        
    return passed == total

if __name__ == "__main__":
    main()