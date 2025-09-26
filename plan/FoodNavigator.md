# FoodNavigator 定制化爬取实现详解

## 实现概述

### 背景问题
FoodNavigator 网站的搜索页面 (`https://www.foodnavigator.com/search/?query=flaxseed`) 使用 Queryly 第三方搜索服务，真实的文章列表通过 JavaScript 动态加载。传统的 DOM 选择器无法获取到实际的搜索结果内容，只能抓取到静态的页面框架。

### 解决方案
直接调用 Queryly API 接口 (`https://api.queryly.com/json.aspx`) 获取 JSON 格式的搜索结果，绕过前端渲染限制，实现高效、稳定的数据抓取。

## 技术架构

### 函数调用链

```
crawl_website(url, max_articles)
├── crawler_instance.crawl_website_articles()
│   ├── async_playwright() 启动浏览器
│   ├── page.goto(url) 访问搜索页面
│   └── _extract_articles(page, base_url, max_articles)
│       └── urlparse(base_url) 解析 URL
│           └── 检测域名: foodnavigator.com + 路径: /search
│               └── _extract_foodnavigator_search(page, base_url, max_articles)
│                   ├── parse_qs() 解析查询参数
│                   ├── 提取关键词和过滤条件
│                   ├── 构建 Queryly API 参数
│                   └── 循环分页请求：
│                       ├── page.context.request.get() 调用 API
│                       ├── json.loads() 解析响应数据
│                       ├── 提取文章信息 (标题、链接、作者、日期)
│                       └── 检查分页continuation
```

### 架构优势

1. **优先级处理**: FoodNavigator → Reuters → Statista → 通用爬虫
2. **API直连**: 绕过前端JavaScript渲染，直接获取结构化数据
3. **分页支持**: 自动处理多页结果，突破单页限制
4. **参数兼容**: 支持排序、过滤、日期范围等高级查询功能

## 核心实现

### 1. 常量配置管理 (`core/crawler.py:15-17`)

```python
FOODNAVIGATOR_QUERYLY_KEY = '162cd04ba9044343'
FOODNAVIGATOR_EXT_FIELDS = 'eventStartDate,creator,subtype,firstPubDate,sectionSupplier,freeByLine,imageresizer,promo_image,resizerv2_id,resizerv2_auth,resizerv2_mimetype,subheadline'
FOODNAVIGATOR_BATCH_SIZE = 20
```

**设计原理**:
- 集中管理配置，便于维护和更新
- `QUERYLY_KEY`: FoodNavigator在Queryly的API密钥
- `EXT_FIELDS`: 扩展字段，获取作者、发布日期、摘要等详细信息
- `BATCH_SIZE`: 每次API调用获取的文章数量，平衡性能和稳定性

### 2. 域名检测逻辑 (`core/crawler.py:650-653`)

```python
if parsed_url.netloc.endswith('foodnavigator.com') and parsed_url.path.startswith('/search'):
    foodnavigator_articles = await self._extract_foodnavigator_search(page, base_url, max_articles)
    if foodnavigator_articles:
        return foodnavigator_articles
```

**触发条件**:
- 域名匹配: `*.foodnavigator.com` 
- 路径匹配: `/search*`
- 优先级: 高优先级（在Reuters和Statista之前）

### 3. 查询参数解析 (`core/crawler.py:195-234`)

```python
parsed = urlparse(base_url)
query_params = parse_qs(parsed.query)

# 提取搜索关键词
keyword = ''
for key in ('query',):
    values = query_params.get(key)
    if values:
        keyword = unquote_plus((values[0] or '').strip())

# 提取排序参数
sort_param = ''
for key in ('sort', 'sortby'):
    value = query_params.get(key, [None])[0]
    if value:
        sort_param = value.lower()

# 提取分页参数
start_index = 0
for key in ('endindex', 'index', 'offset', 'start'):
    value = query_params.get(key, [None])[0]
    if value:
        try:
            start_index = max(int(value), 0)
            break
        except ValueError:
            continue

# 支持page参数转换为offset
if start_index == 0:
    page_value = query_params.get('page', [None])[0]
    if page_value:
        page_number = max(int(page_value), 1)
        start_index = (page_number - 1) * FOODNAVIGATOR_BATCH_SIZE

# 高级过滤参数
faceted_key = query_params.get('facetedkey', [None])[0]
faceted_value = query_params.get('facetedvalue', [None])[0]
date_range = query_params.get('daterange', [None])[0]
```

**支持的URL参数**:
- `query`: 搜索关键词 (必需)
- `sort/sortby`: 排序方式 (`date` 按日期排序)
- `page`: 页码 (从1开始)
- `endindex/offset`: 起始位置 (从0开始)
- `facetedkey/facetedvalue`: 分类过滤
- `daterange`: 日期范围过滤

### 4. Queryly API 调用 (`core/crawler.py:239-269`)

```python
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

    # 条件参数添加
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
            'Referer': base_url  # 重要：Queryly需要正确的Referer
        }
    )
```

**关键技术点**:
- **循环分页**: `while` 循环自动处理多页结果
- **动态批量**: 根据剩余需求调整批量大小
- **请求头设置**: User-Agent 和 Referer 确保API正常响应
- **Playwright集成**: 使用浏览器上下文的请求对象，共享Cookie和会话

### 5. 数据解析和格式化 (`core/crawler.py:285-315`)

```python
for item in items:
    if len(articles) >= max_articles:
        break

    # URL规范化
    link = (item.get('link') or '').strip()
    if link.startswith('//'):
        article_url = 'https:' + link
    elif link.startswith('http'):
        article_url = link
    else:
        article_url = urljoin('https://www.foodnavigator.com', link)

    # 数据提取
    title = (item.get('title') or '').strip()
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
```

**数据字段说明**:
- `title`: 文章标题 (限制200字符)
- `url`: 完整的文章链接
- `summary`: 文章摘要/副标题 (限制500字符)
- `author`: 作者信息
- `published_at`: 发布时间 (原始格式)
- `extracted_at`: 抓取时间戳

### 6. 分页机制 (`core/crawler.py:317-327`)

```python
metadata = data.get('metadata') or {}
next_index = metadata.get('endindex')
try:
    next_index_int = int(next_index)
except (TypeError, ValueError):
    next_index_int = offset + len(items)

if next_index_int <= offset or len(articles) >= max_articles:
    break

offset = next_index_int
```

**分页逻辑**:
- 从API响应的 `metadata.endindex` 获取下次请求的起始位置
- 当 `next_index` 不递增时停止分页 (防止无限循环)
- 达到目标文章数量时提前结束

## API接口详解

### Queryly API 规范

**端点**: `https://api.queryly.com/json.aspx`

**必需参数**:
- `queryly_key`: API密钥
- `query`: 搜索关键词

**可选参数**:
- `endindex`: 起始位置 (分页用)
- `batchsize`: 批量大小 (默认20)
- `sort`: 排序方式 (`date`, `relevance`)
- `showfaceted`: 是否显示分类信息 (`true`/`false`)
- `extendeddatafields`: 扩展字段列表 (逗号分隔)
- `facetedkey`: 分类字段名
- `facetedvalue`: 分类值
- `daterange`: 日期范围
- `timezoneoffset`: 时区偏移

**响应格式**:
```json
{
  "items": [
    {
      "title": "文章标题",
      "link": "/article/path",
      "subheadline": "文章摘要",
      "creator": "作者名",
      "firstPubDate": "发布日期",
      "description": "描述"
    }
  ],
  "metadata": {
    "endindex": "下一页起始位置",
    "totalresults": "总结果数"
  }
}
```

## 验证方法

### 快速验证
运行验证脚本：
```bash
python verify_foodnavigator.py
```

### 预期输出
```
success: True
total: 5
error: None
1 Lactating women should restrict flaxseed intake: Researchers => https://www.foodnavigator.com/Article/2015/09/04/lactating-women-should-restrict-flaxseed-intake-researchers/
2 Europe's food safety watchdog plays down flaxseed cyanide danger => https://www.foodnavigator.com/Article/2019/08/21/Europe-s-food-safety-watchdog-plays-down-flaxseed-cyanide-danger/
...
```

### 功能验证清单
- [ ] 基本搜索功能 (`?query=flaxseed`)
- [ ] 分页功能 (`?query=flaxseed&page=2`)
- [ ] 排序功能 (`?query=flaxseed&sort=date`)
- [ ] 批量设置 (调整 `max_articles` 参数)
- [ ] 错误处理 (无效关键词、网络异常)

## 扩展说明

### 支持的高级功能

1. **分类过滤**:
   ```
   https://www.foodnavigator.com/search/?query=flaxseed&facetedkey=category&facetedvalue=nutrition
   ```

2. **日期范围**:
   ```
   https://www.foodnavigator.com/search/?query=flaxseed&daterange=2023-01-01,2023-12-31
   ```

3. **按日期排序**:
   ```
   https://www.foodnavigator.com/search/?query=flaxseed&sort=date
   ```

### 架构对比

| 功能 | FoodNavigator | Reuters | Statista | 通用爬虫 |
|------|---------------|---------|----------|-----------|
| API集成 | Queryly API | articles-by-search-v2 | 内部JSON接口 | DOM选择器 |
| 分页支持 | ✅ 自动分页 | ✅ 参数控制 | ✅ 参数控制 | ❌ 单页限制 |
| 元数据 | 作者、日期、摘要 | 标题、链接、日期 | 统计类型、ID | 标题、链接 |
| 过滤能力 | 分类、日期、排序 | 关键词、大小 | 查询条件、类型 | 无 |
| 稳定性 | 高 (API直连) | 高 (官方API) | 高 (内部API) | 中 (依赖DOM) |

### 维护建议

1. **监控API变化**: 定期检查Queryly接口是否更新
2. **密钥管理**: 如果API密钥变更，需要更新常量配置
3. **字段扩展**: 可以根据需要调整 `FOODNAVIGATOR_EXT_FIELDS` 获取更多数据
4. **性能优化**: 可以调整 `BATCH_SIZE` 平衡请求频率和数据量
5. **错误处理**: 考虑添加重试机制和更详细的错误日志

### 未来扩展方向

1. **多站点支持**: 扩展到其他使用Queryly的网站
2. **缓存机制**: 对频繁查询的结果进行缓存
3. **实时更新**: 支持增量更新和变化检测
4. **数据分析**: 集成文章情感分析和主题分类
5. **API封装**: 提供独立的FoodNavigator搜索API服务

## 总结

FoodNavigator的定制化爬取实现通过直接调用Queryly API，成功解决了JavaScript动态加载内容的抓取难题。该方案具有高效、稳定、功能丰富的特点，为WeRSS项目提供了强大的FoodNavigator内容源支持。

与Reuters和Statista的定制实现一起，形成了一个完整的专业网站抓取解决方案，大大提升了WeRSS在特定领域的内容获取能力。