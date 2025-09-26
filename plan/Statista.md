# Statista 定制化爬取实现详解

## 实现概述

### 背景问题
Statista（全球领先的市场和消费数据平台）的搜索页面存在以下技术挑战：

1. **前端渲染依赖**: 搜索结果通过JavaScript动态生成，HTML源码中不包含实际统计数据
2. **导航链接干扰**: 通用选择器会误抓取大量导航栏、分类页面等非统计内容链接
3. **复杂URL结构**: 不同类型的统计数据（图表、研究、话题等）使用不同的URL路径结构
4. **实体类型识别**: 需要根据内容类型构建正确的详情页链接

### 解决方案
采用"内部API + 智能URL构建"策略：
1. **API发现**: 识别Statista内部使用的搜索JSON接口
2. **浏览器内调用**: 通过`fetch`在页面上下文中调用接口，绕过CORS限制
3. **实体类型映射**: 根据API返回的实体信息智能构建URL
4. **多字段标题提取**: 优先级级联提取最佳标题内容

## 技术架构

### 函数调用链

```
crawl_website(url, max_articles)
├── crawler_instance.crawl_website_articles()
│   ├── async_playwright() 启动浏览器
│   ├── page.goto(url) 访问搜索页面
│   └── _extract_articles(page, base_url, max_articles)
│       └── urlparse(base_url) 解析URL
│           └── 检测statista.com + /search路径
│               └── _extract_statista_search(page, base_url, max_articles)
│                   ├── parse_qs() 解析查询参数
│                   ├── 构建API参数（保留原参数 + asJsonResponse=1）
│                   ├── 补充默认参数（q, p, sortMethod等）
│                   ├── page.evaluate() 浏览器内fetch调用
│                   ├── json.loads() 解析API响应
│                   ├── 实体ID映射和类型识别
│                   ├── _build_statista_url() 智能URL构建
│                   └── 多字段标题提取和记录标准化
```

### 核心策略

1. **参数透传**: 保留用户原始搜索参数，确保搜索意图不变
2. **默认补齐**: 为缺失的关键参数提供合理默认值
3. **实体映射**: 通过`justSmart.actionParameters.entityIds`建立ID到类型的映射
4. **URL智能构建**: 根据实体类型选择正确的路径前缀

## 核心实现

### 1. 域名检测与路由 (`core/crawler.py:789-792`)

```python
if parsed_url.netloc.endswith('statista.com') and parsed_url.path.startswith('/search'):
    statista_articles = await self._extract_statista_search(page, base_url, max_articles)
    if statista_articles:
        return statista_articles
```

**触发条件**:
- **域名匹配**: `*.statista.com`
- **路径匹配**: `/search*` (搜索页面专用)
- **优先级**: 较低优先级 (在万方、FoodNavigator、Reuters、Panda985之后)

### 2. 查询参数处理 (`core/crawler.py:519-527`)

```python
parsed = urlparse(base_url)
query_params = parse_qs(parsed.query)

# 构建请求参数，保留原有查询条件并强制返回 JSON
api_params = [('asJsonResponse', '1')]
for key, values in query_params.items():
    for value in values:
        if value is not None:
            api_params.append((key, value))
```

**参数处理策略**:
- **透传原参数**: 保留用户所有搜索条件
- **强制JSON**: 添加`asJsonResponse=1`激活API模式
- **多值支持**: 正确处理具有多个值的参数

**支持的搜索参数**:
- `q`: 搜索关键词
- `p`: 页码
- `sortMethod`: 排序方式 (`relevance`, `publicationDate`)
- `accuracy`: 搜索精度 (`and`, `or`)
- `interval`: 时间区间
- `isoregion`: 地理区域
- `language`: 语言设置

### 3. 默认参数补齐 (`core/crawler.py:529-544`)

```python
defaults = {
    'q': '',                    # 搜索关键词
    'p': '1',                   # 页码
    'sortMethod': 'relevance',  # 排序方式
    'accuracy': 'and',          # 搜索精度
    'interval': '0',            # 时间区间
    'idRelevance': '0',         # ID相关性
    'isRegionPref': '-1',       # 地区偏好
    'isoregion': '0',           # ISO地区代码
    'language': '0',            # 语言设置
}
existing_keys = {key for key, _ in api_params}
for key, value in defaults.items():
    if key not in existing_keys:
        api_params.append((key, value))
```

**默认值设计原理**:
- **API兼容性**: Statista接口在缺少参数时会使用内部默认值，可能与预期不符
- **搜索质量**: 明确指定参数确保搜索结果的一致性
- **向后兼容**: 即使API更新，默认参数也能提供基础功能

### 4. 内部API调用 (`core/crawler.py:546-562`)

```python
query_string = urlencode(api_params, doseq=True)
target_url = f"https://www.statista.com/search/?{query_string}"
fetch_result = await page.evaluate(
    "async (targetUrl) => {\n                    const response = await fetch(targetUrl, {\n                        headers: {\n                            'Accept': 'application/json, text/plain, */*',\n                            'X-Requested-With': 'XMLHttpRequest'\n                        },\n                        credentials: 'include'\n                    });\n                    const text = await response.text();\n                    return { status: response.status, text };\n                }",
    target_url
)
```

**技术要点**:

**API端点**: 与用户访问的URL相同，但通过`asJsonResponse=1`切换到JSON模式

**关键请求头**:
- `Accept`: 明确期望JSON响应
- `X-Requested-With`: 标识AJAX请求，触发API响应模式
- `credentials: 'include'`: 包含用户会话信息

**浏览器内执行优势**:
- **会话继承**: 自动使用页面的登录状态和Cookie
- **CORS绕过**: 避免跨域请求限制
- **环境一致**: 与正常用户访问环境完全相同

### 5. 数据结构解析 (`core/crawler.py:563-566`)

```python
data = json.loads(raw_text)
results = data.get('results', {})
main_results = results.get('mainselect') or []
entity_ids = data.get('justSmart', {}).get('actionParameters', {}).get('entityIds', {})
id_to_name = {str(v): k for k, v in entity_ids.items()}
```

**API响应结构**:
```json
{
    "results": {
        "mainselect": [
            {
                "identity": "123456",
                "graphheader": "主标题",
                "pagetitle": "页面标题", 
                "catchline": "副标题",
                "title": "标题",
                "uri": "url-slug",
                "idcontent": "content-id"
            }
        ]
    },
    "justSmart": {
        "actionParameters": {
            "entityIds": {
                "statistic": 123456,
                "topic": 789012
            }
        }
    }
}
```

**数据映射逻辑**:
- **主要结果**: `results.mainselect`包含搜索到的统计项目
- **实体类型**: `justSmart.actionParameters.entityIds`提供ID到类型的映射
- **反向映射**: 构建`{id: type}`字典用于URL构建

### 6. 实体类型映射系统 (`core/crawler.py:736-751`)

```python
entity_to_path = {
    'statistic': 'statistics',      # 统计数据
    'forecast': 'statistics',       # 预测数据  
    'infographic': 'infographic',   # 信息图表
    'topic': 'topics',              # 主题页面
    'study': 'study',               # 研究报告
    'dossier': 'study',             # 档案报告
    'dossierplus': 'study',         # 高级档案
    'toplist': 'study',             # 排行榜
    'survey': 'study',              # 调查报告
    'marketstudy': 'study',         # 市场研究
    'branchreport': 'study',        # 行业报告
    'brandreport': 'study',         # 品牌报告
    'companyreport': 'study',       # 公司报告
    'countryreport': 'study',       # 国家报告
}
```

**映射原理**:
- **路径规范化**: 不同实体类型对应不同的URL路径前缀
- **类型聚合**: 多种报告类型统一归类为`study`路径
- **URL一致性**: 确保生成的链接与Statista官方URL格式一致

### 7. 智能URL构建 (`core/crawler.py:724-761`)

```python
def _build_statista_url(self, item: Dict, entity_name: Optional[str]) -> Optional[str]:
    if not item:
        return None

    slug = (item.get('uri') or item.get('url') or '').strip('/')
    if not slug:
        return None

    idcontent = item.get('idcontent')
    base = 'https://www.statista.com'

    # 根据实体类型构建URL
    path_prefix = entity_to_path.get(entity_name)
    if path_prefix and idcontent:
        return f"{base}/{path_prefix}/{idcontent}/{slug}/"

    # 回退到直接拼接slug
    if slug.startswith('http'):
        return slug
    return f"{base}/{slug}/"
```

**URL构建逻辑**:

**完整路径格式**: `https://www.statista.com/{path_prefix}/{idcontent}/{slug}/`

**构建步骤**:
1. **提取slug**: 从`uri`或`url`字段获取URL片段
2. **获取ID**: 从`idcontent`字段获取内容ID
3. **确定路径**: 根据实体类型映射获取路径前缀
4. **组装URL**: 按标准格式组装完整URL
5. **回退机制**: 无法确定类型时直接使用slug

**URL示例**:
- 统计数据: `https://www.statista.com/statistics/12345/flaxseed-production/`
- 主题页面: `https://www.statista.com/topics/67890/agriculture/`
- 研究报告: `https://www.statista.com/study/11111/market-analysis/`

### 8. 多字段标题提取 (`core/crawler.py:578-588`)

```python
title_fields = [
    item.get('graphheader'),    # 图表标题（优先级最高）
    item.get('pagetitle'),      # 页面标题
    item.get('catchline'),      # 副标题
    item.get('title'),          # 通用标题
    item.get('pseudotitle'),    # 伪标题
    item.get('subtitle'),       # 子标题
]
title = next((t.strip() for t in title_fields if t), None)
if not title:
    title = article_url
```

**标题提取策略**:
- **优先级级联**: 按照内容质量依次尝试不同标题字段
- **非空验证**: 跳过空白或None值
- **URL回退**: 无可用标题时使用URL作为标题
- **长度限制**: 最终标题限制在200字符以内

**字段优先级说明**:
1. `graphheader`: 图表专用标题，最具描述性
2. `pagetitle`: 页面SEO标题，通常最完整
3. `catchline`: 营销标题，简洁明了
4. `title`: 通用标题字段
5. `pseudotitle`: 生成的标题
6. `subtitle`: 补充说明标题

### 9. 数据标准化输出 (`core/crawler.py:590-594`)

```python
articles.append({
    'title': title[:200],
    'url': article_url,
    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
})
```

**输出字段**:
- `title`: 标题（截断保护）
- `url`: 可直接访问的详情页链接
- `extracted_at`: 数据提取时间戳

**设计特点**:
- **字段精简**: 只保留核心必要信息
- **URL可用性**: 确保链接可以直接访问
- **时间戳**: 便于数据新鲜度管理

## API接口详解

### Statista Search API规范

**端点**: `https://www.statista.com/search/`

**请求方法**: GET

**必需参数**:
- `asJsonResponse`: 值为`1`，激活JSON响应模式

**搜索参数**:
- `q`: 搜索关键词
- `p`: 页码（从1开始）
- `sortMethod`: 排序方式
  - `relevance`: 相关性排序（默认）
  - `publicationDate`: 发布日期排序

**过滤参数**:
- `accuracy`: 搜索精度
  - `and`: 精确匹配（默认）
  - `or`: 模糊匹配
- `interval`: 时间区间
  - `0`: 不限时间（默认）
  - `1`: 最近一年
  - `2`: 最近五年
- `isoregion`: 地理区域代码
- `language`: 语言设置
- `isRegionPref`: 地区偏好设置

**响应格式**:
```json
{
    "results": {
        "mainselect": [
            {
                "identity": "统计项ID",
                "graphheader": "图表标题",
                "pagetitle": "页面标题",
                "catchline": "副标题",
                "title": "通用标题",
                "pseudotitle": "生成标题",
                "subtitle": "子标题",
                "uri": "url-slug",
                "url": "url-path", 
                "idcontent": "内容ID"
            }
        ]
    },
    "justSmart": {
        "actionParameters": {
            "entityIds": {
                "实体类型名": 实体ID
            }
        }
    }
}
```

## 验证方法

### 快速验证
运行验证脚本：
```bash
python verify_statista.py
```

### 验证脚本示例
```python
import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=120000)
    url = 'https://www.statista.com/search/?q=flaxseed&p=1&sortMethod=publicationDate'
    result = await crawler.crawl_website_articles(url, max_articles=5)
    
    print('success:', result['success'])
    print('total_found:', result['total_found'])
    print('error:', result['error'])
    
    for idx, article in enumerate(result['articles'], 1):
        print(f"{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print()

asyncio.run(main())
```

### 预期输出
```
success: True
total_found: 5
error: None
1. Seeded area of flaxseed in Canada from 1908 to 2025 (in 1,000s)
   URL: https://www.statista.com/statistics/831898/seeded-area-flaxseed-canada/

2. Harvested area of flaxseed in Canada from 1965 to 2024 (in 1,000s)
   URL: https://www.statista.com/statistics/454274/area-of-flaxseed-harvested-in-canada/

3. Farm cash receipts from flaxseed in Canada from 1971 to 2024 (in million U.S. dollars)
   URL: https://www.statista.com/statistics/449282/farm-cash-receipts-of-flaxseed-canada/
...
```

### 验证要点
- [ ] **API调用成功**: 检查HTTP 200响应
- [ ] **JSON解析正常**: 验证响应格式正确
- [ ] **URL构建准确**: 确认生成的链接可访问
- [ ] **标题提取完整**: 检查标题内容质量
- [ ] **实体类型识别**: 验证不同类型的URL构建

## 架构对比

### 与其他定制爬虫的对比

| 特性 | Statista | FoodNavigator | Reuters | 万方数据 | 通用爬虫 |
|------|----------|---------------|---------|----------|-----------|
| **数据类型** | 统计数据 | 行业资讯 | 新闻报道 | 学术文献 | 通用网页 |
| **API集成** | ✅ 内部API | ✅ Queryly | ✅ 官方API | ❌ DOM解析 | ❌ 无API |
| **URL智能构建** | ✅ 实体映射 | ❌ 固定格式 | ❌ 固定格式 | ✅ 类型映射 | ❌ 直接提取 |
| **多字段标题** | ✅ 级联提取 | ✅ 多字段 | ✅ 备选字段 | ✅ 单字段 | ✅ 单字段 |
| **参数透传** | ✅ 完整保留 | ✅ 部分支持 | ❌ 简化参数 | ❌ 无参数 | ❌ 无参数 |
| **分页支持** | 🔄 可扩展 | ✅ 自动分页 | 🔄 可扩展 | ❌ 单页 | ❌ 单页 |
| **实体分类** | ✅ 12种类型 | ❌ 无分类 | ❌ 无分类 | ✅ 12种类型 | ❌ 无分类 |
| **数据权威性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

### 独特优势

1. **统计数据专业性**: 专门针对统计数据和市场研究内容
2. **实体类型智能识别**: 自动识别并构建正确的URL格式
3. **多字段标题优化**: 级联提取最佳标题内容
4. **参数完整透传**: 保持用户搜索意图不变
5. **URL构建准确性**: 生成的链接与官方格式完全一致

### 应用场景

1. **市场研究**: 获取行业统计数据和趋势分析
2. **商业决策**: 访问权威的市场数据支持决策
3. **学术研究**: 引用可靠的统计数据源
4. **投资分析**: 获取行业和公司数据
5. **新闻报道**: 引用权威统计数据

## 扩展建议

### 1. 分页支持实现

```python
async def _extract_statista_search_with_pagination(self, page, base_url, max_articles):
    all_articles = []
    current_page = 1
    
    while len(all_articles) < max_articles:
        # 构建当前页参数
        page_params = parse_qs(urlparse(base_url).query)
        page_params['p'] = [str(current_page)]
        
        # 调用单页API
        page_articles = await self._extract_single_page(page, page_params)
        if not page_articles:
            break
            
        all_articles.extend(page_articles)
        current_page += 1
        
        # 避免请求过快
        await asyncio.sleep(1)
    
    return all_articles[:max_articles]
```

### 2. 高级过滤支持

```python
# 支持更多过滤条件
advanced_filters = {
    'region': query_params.get('isoregion', ['0'])[0],     # 地理区域
    'timeframe': query_params.get('interval', ['0'])[0],   # 时间范围
    'content_type': query_params.get('content', [''])[0],  # 内容类型
    'industry': query_params.get('industry', [''])[0],     # 行业分类
    'company': query_params.get('company', [''])[0]        # 公司筛选
}

# 添加到API参数中
for key, value in advanced_filters.items():
    if value:
        api_params.append((key, value))
```

### 3. 数据增强提取

```python
# 提取更多元数据
enhanced_article = {
    'title': title[:200],
    'url': article_url,
    'data_type': entity_name,                              # 数据类型
    'content_id': item.get('idcontent'),                   # 内容ID
    'region': item.get('region_info'),                     # 地理信息
    'industry': item.get('industry_category'),             # 行业分类
    'publication_date': item.get('published_date'),        # 发布日期
    'last_updated': item.get('last_updated'),              # 最后更新
    'data_points': item.get('data_point_count'),           # 数据点数量
    'chart_type': item.get('chart_type'),                  # 图表类型
    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
}
```

### 4. 错误处理增强

```python
async def _robust_statista_api_call(self, page, target_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await page.evaluate("""
                async (url) => {
                    try {
                        const response = await fetch(url, {
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'include',
                            timeout: 30000
                        });
                        return { status: response.status, text: await response.text() };
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            """, target_url)
            
            if result.get('error'):
                raise Exception(f"Fetch error: {result['error']}")
                
            return result
            
        except Exception as e:
            logger.warning(f"Statista API attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
            else:
                raise
```

### 5. 缓存优化

```python
import hashlib
from datetime import datetime, timedelta

class StatistaCache:
    def __init__(self, ttl_hours=6):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_key(self, search_params):
        param_str = urllib.parse.urlencode(sorted(search_params))
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def get(self, search_params):
        key = self._get_cache_key(search_params)
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, search_params, data):
        key = self._get_cache_key(search_params)
        self.cache[key] = (data, datetime.now())
        
        # 清理过期缓存
        self._cleanup_expired()
    
    def _cleanup_expired(self):
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
```

## 维护建议

### 1. API接口监控

```python
async def monitor_statista_api(self):
    test_url = "https://www.statista.com/search/?q=test&asJsonResponse=1"
    
    try:
        result = await self._test_api_call(test_url)
        
        # 检查响应结构
        if not result.get('results', {}).get('mainselect'):
            logger.warning("Statista API structure may have changed")
            return False
            
        # 检查实体映射
        entity_ids = result.get('justSmart', {}).get('actionParameters', {}).get('entityIds', {})
        if not entity_ids:
            logger.warning("Statista entity mapping structure changed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Statista API monitoring failed: {e}")
        return False
```

### 2. URL构建验证

```python
async def validate_statista_urls(self, articles):
    valid_count = 0
    
    for article in articles[:5]:  # 测试前5个链接
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(article['url'], timeout=10) as response:
                    if response.status == 200:
                        valid_count += 1
                    else:
                        logger.warning(f"Invalid Statista URL: {article['url']} (status: {response.status})")
        except Exception as e:
            logger.warning(f"URL validation failed for {article['url']}: {e}")
    
    success_rate = valid_count / min(len(articles), 5)
    if success_rate < 0.8:
        logger.error(f"Statista URL validation success rate too low: {success_rate:.2%}")
    
    return success_rate >= 0.8
```

### 3. 实体类型更新

```python
# 定期检查新的实体类型
async def discover_new_entity_types(self, page):
    # 执行多种搜索获取不同类型的实体
    test_queries = ['market study', 'forecast', 'infographic', 'survey']
    
    discovered_types = set()
    
    for query in test_queries:
        result = await self._call_api_for_discovery(page, query)
        entity_ids = result.get('justSmart', {}).get('actionParameters', {}).get('entityIds', {})
        discovered_types.update(entity_ids.keys())
    
    # 比较现有映射
    existing_types = set(entity_to_path.keys())
    new_types = discovered_types - existing_types
    
    if new_types:
        logger.info(f"Discovered new Statista entity types: {new_types}")
        # 可以发送告警或自动更新配置
```

### 4. 性能优化

```python
# 批量处理URL构建
def batch_build_urls(self, items, id_to_name_map):
    urls = []
    
    for item in items:
        try:
            identity = str(item.get('identity', ''))
            entity_name = id_to_name_map.get(identity)
            url = self._build_statista_url(item, entity_name)
            if url:
                urls.append(url)
        except Exception as e:
            logger.debug(f"URL build failed for item {item.get('identity')}: {e}")
            continue
    
    return urls

# 并发验证URL
async def concurrent_url_validation(self, urls):
    async def validate_single_url(session, url):
        try:
            async with session.head(url, timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    async with aiohttp.ClientSession() as session:
        tasks = [validate_single_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_urls = [url for url, valid in zip(urls, results) if valid]
    return valid_urls
```

## 总结

Statista的定制化爬取实现通过"内部API + 智能URL构建"策略，成功解决了统计数据平台的复杂技术挑战。该实现具有以下特点：

### 技术优势
- **API直连**: 绕过前端渲染，直接获取结构化数据
- **智能URL构建**: 根据实体类型自动生成正确的访问链接
- **参数透传**: 完整保留用户搜索意图
- **多字段标题**: 级联提取最佳标题内容
- **实体类型识别**: 支持12种不同的统计数据类型

### 应用价值
- **权威数据源**: Statista作为全球领先的统计数据平台
- **多样化内容**: 涵盖统计图表、市场研究、行业报告等
- **专业性强**: 为商业决策和学术研究提供可靠数据支持
- **全球覆盖**: 涵盖各国各行业的统计数据

该实现为WeRSS项目提供了高质量的统计数据内容源，与其他定制爬虫一起构成了涵盖学术、行业、新闻、数据等多个领域的完整内容抓取解决方案，特别适合需要权威统计数据支持的应用场景。