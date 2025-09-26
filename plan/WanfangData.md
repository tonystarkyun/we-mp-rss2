# 万方数据定制化爬取实现详解

## 实现概述

### 背景问题
万方数据知识服务平台 (`https://s.wanfangdata.com.cn/paper`) 是中国重要的学术资源数据库，包含期刊论文、学位论文、会议论文、专利等多种类型的学术文献。其搜索结果页面采用动态加载机制，传统DOM选择器无法有效抓取完整的文献信息。

### 解决方案
通过等待特定DOM节点加载完成，使用JavaScript在浏览器环境中直接提取结构化数据，包括隐藏的文献ID、完整的作者信息、关键词等元数据，然后构造标准的详情页链接。

## 技术架构

### 函数调用链

```
crawl_website(url, max_articles)
├── crawler_instance.crawl_website_articles()
│   ├── async_playwright() 启动浏览器
│   ├── page.goto(url) 访问搜索页面
│   └── _extract_articles(page, base_url, max_articles)
│       └── urlparse(base_url) 解析 URL
│           └── 检测域名: wanfangdata.com.cn + 路径: /paper
│               └── _extract_wanfang_search(page, base_url, max_articles)
│                   ├── page.wait_for_selector() 等待内容加载
│                   ├── page.evaluate() 提取结构化数据
│                   ├── 文献类型映射和URL构造
│                   ├── 作者信息和来源解析
│                   └── 返回标准化文献记录
```

### 架构特点

1. **DOM等待机制**: 确保动态内容完全加载
2. **结构化提取**: 一次性获取所有文献元数据
3. **类型智能映射**: 自动识别文献类型并构造正确链接
4. **元数据丰富**: 提取作者、摘要、关键词、来源等完整信息

## 核心实现

### 1. 域名检测逻辑 (`core/crawler.py:645-648`)

```python
if parsed_url.netloc.endswith('wanfangdata.com.cn') and parsed_url.path.startswith('/paper'):
    wanfang_articles = await self._extract_wanfang_search(page, base_url, max_articles)
    if wanfang_articles:
        return wanfang_articles
```

**触发条件**:
- 域名匹配: `*.wanfangdata.com.cn`
- 路径匹配: `/paper*` (论文搜索页面)
- 优先级: 最高优先级 (排在所有其他定制爬虫之前)

### 2. 动态内容等待 (`core/crawler.py:335-338`)

```python
try:
    await page.wait_for_selector('div.normal-list', timeout=10000)
except Exception:
    return articles
```

**等待策略**:
- **目标元素**: `div.normal-list` (文献列表容器)
- **超时时间**: 10秒
- **失败处理**: 超时返回空列表，避免阻塞

### 3. 结构化数据提取 (`core/crawler.py:340-349`)

```python
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
```

**提取字段**:
- `id`: 隐藏的文献唯一标识符 (`.title-id-hidden`)
- `title`: 文献标题 (`.title`)
- `summary`: 摘要内容 (`.abstract-area`)
- `authors`: 作者列表 (`.author-area .authors`)
- `typeLabel`: 文献类型标签 (`.essay-type`)
- `keywords`: 关键词列表 (`.keywords-area .keywords-list`)

**技术特点**:
- **一次性提取**: 通过单次JavaScript执行获取所有数据
- **数组处理**: 自动处理多值字段(作者、关键词)
- **空值过滤**: 使用`filter(Boolean)`移除空白项
- **文本清理**: 自动`trim()`处理空白字符

### 4. 文献类型映射系统 (`core/crawler.py:354-372`)

```python
type_map = {
    'periodical': 'perio',        # 期刊论文
    'perio': 'perio',
    'degree': 'degree',           # 学位论文
    'thesis': 'degree',
    'dissertation': 'degree',
    'conference': 'conference',   # 会议论文
    'patent': 'patent',           # 专利
    'std': 'std',                 # 标准
    'standard': 'std',
    'tech': 'tech',               # 科技报告
    'report': 'tech',
    'achievement': 'tech',
    'nstr': 'nstr',               # 科技成果
    'localchronicle': 'localchronicle',  # 地方志
    'law': 'law',                 # 法律法规
    'policy': 'policy',           # 政策文件
    'video': 'video'              # 视频资源
}
```

**映射逻辑**:
- **前缀提取**: 从文献ID中提取类型前缀 (`record_id.split('_', 1)[0]`)
- **类型规范化**: 将各种变体映射到标准类型
- **默认回退**: 未知类型默认为 `perio` (期刊)

### 5. URL构造机制 (`core/crawler.py:379-381`)

```python
prefix = record_id.split('_', 1)[0].lower() if '_' in record_id else record_id.lower()
type_param = type_map.get(prefix, prefix or 'perio')
detail_url = f"https://www.wanfangdata.com.cn/details/detail.do?_type={type_param}&id={record_id}"
```

**URL格式**: `https://www.wanfangdata.com.cn/details/detail.do?_type={type}&id={id}`

**参数说明**:
- `_type`: 文献类型参数 (经过映射处理)
- `id`: 完整的文献唯一标识符

### 6. 作者信息解析 (`core/crawler.py:385-391`)

```python
authors = item.get('authors') or []
source_info = ''
if authors:
    tail = authors[-1]
    if any(ch.isdigit() for ch in tail):  # 检测数字(年份、页码等)
        source_info = tail
        authors = authors[:-1]
```

**解析逻辑**:
- **来源分离**: 检测作者列表最后一项是否包含数字
- **智能识别**: 包含数字的项通常是期刊信息、年份或页码
- **信息分类**: 将来源信息单独存储，保持作者列表纯净

### 7. 摘要内容处理 (`core/crawler.py:393-395`)

```python
summary = (item.get('summary') or '').strip()
if summary.startswith('摘要'):
    summary = summary[2:].lstrip('：:').strip()
```

**处理步骤**:
- **前缀清理**: 移除"摘要"标识词
- **分隔符处理**: 清理中英文冒号和空白
- **格式标准化**: 获得纯净的摘要内容

### 8. 数据结构化输出 (`core/crawler.py:400-409`)

```python
articles.append({
    'title': title[:200],                    # 标题(限200字符)
    'url': detail_url,                       # 详情页链接
    'summary': summary[:500] if summary else '',  # 摘要(限500字符)
    'authors': authors,                      # 作者列表
    'source': source_info,                   # 来源信息
    'type': type_label,                      # 文献类型
    'keywords': keywords,                    # 关键词列表
    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')  # 提取时间
})
```

**字段说明**:
- `title`: 文献标题 (截断保护)
- `url`: 可直接访问的详情页链接
- `summary`: 清理后的摘要内容
- `authors`: 纯净的作者名单
- `source`: 期刊、会议或出版信息
- `type`: 原始文献类型标签
- `keywords`: 关键词数组
- `extracted_at`: 数据采集时间戳

## 支持的文献类型

### 核心类型映射

| 原始类型 | 映射类型 | 中文名称 | 示例URL |
|----------|----------|----------|---------|
| periodical/perio | perio | 期刊论文 | `detail.do?_type=perio&id=perio_xxx` |
| degree/thesis/dissertation | degree | 学位论文 | `detail.do?_type=degree&id=degree_xxx` |
| conference | conference | 会议论文 | `detail.do?_type=conference&id=conference_xxx` |
| patent | patent | 专利文献 | `detail.do?_type=patent&id=patent_xxx` |
| std/standard | std | 标准文献 | `detail.do?_type=std&id=std_xxx` |
| tech/report/achievement | tech | 科技报告 | `detail.do?_type=tech&id=tech_xxx` |
| nstr | nstr | 科技成果 | `detail.do?_type=nstr&id=nstr_xxx` |
| localchronicle | localchronicle | 地方志 | `detail.do?_type=localchronicle&id=local_xxx` |
| law | law | 法律法规 | `detail.do?_type=law&id=law_xxx` |
| policy | policy | 政策文件 | `detail.do?_type=policy&id=policy_xxx` |
| video | video | 视频资源 | `detail.do?_type=video&id=video_xxx` |

### 扩展性设计

```python
# 新增文献类型只需在type_map中添加映射
type_map['newtype'] = 'new_category'
```

## 验证方法

### 快速验证
运行验证脚本：
```bash
python verify_wanfang.py
```

### 验证脚本示例
```python
import asyncio
from core.crawler import LinkCrawler

async def main():
    crawler = LinkCrawler(headless=True, timeout=120000)
    url = 'https://s.wanfangdata.com.cn/paper?q=flaxseed'
    result = await crawler.crawl_website_articles(url, max_articles=5)
    print('success:', result['success'])
    print('total:', result['total_found'])
    print('error:', result['error'])
    for idx, article in enumerate(result['articles'], 1):
        print(f"{idx}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   作者: {', '.join(article.get('authors', []))}")
        print(f"   类型: {article.get('type', 'N/A')}")
        print(f"   关键词: {', '.join(article.get('keywords', []))}")
        print()

asyncio.run(main())
```

### 预期输出格式
```
success: True
total: 5
error: None
1. 亚麻籽油的营养价值和功能特性研究
   URL: https://www.wanfangdata.com.cn/details/detail.do?_type=perio&id=perio_12345
   作者: 张三, 李四, 王五
   类型: 期刊论文
   关键词: 亚麻籽油, 营养价值, 功能特性

2. 基于亚麻籽提取物的功能食品开发
   URL: https://www.wanfangdata.com.cn/details/detail.do?_type=degree&id=degree_67890
   作者: 赵六
   类型: 学位论文
   关键词: 亚麻籽, 功能食品, 提取工艺
...
```

## 架构对比

### 与其他定制爬虫的对比

| 特性 | 万方数据 | FoodNavigator | Reuters | Statista | 通用爬虫 |
|------|----------|---------------|---------|----------|-----------|
| **数据源类型** | 学术文献 | 行业资讯 | 新闻报道 | 统计数据 | 通用网页 |
| **检测方式** | DOM等待 | API调用 | API调用 | API调用 | 选择器匹配 |
| **元数据丰富度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **分页支持** | ❌ 单页 | ✅ 自动分页 | ✅ 参数控制 | ✅ 参数控制 | ❌ 单页 |
| **类型识别** | ✅ 智能映射 | ❌ 统一类型 | ❌ 统一类型 | ✅ 实体分类 | ❌ 无分类 |
| **结构化程度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **稳定性** | 高 (DOM解析) | 高 (API直连) | 高 (官方API) | 高 (内部API) | 中 (依赖DOM) |

### 独特优势

1. **学术专业性**: 专门处理学术文献的复杂元数据
2. **类型智能识别**: 自动识别文献类型并构造正确访问链接
3. **作者信息解析**: 智能分离作者和来源信息
4. **关键词提取**: 完整保留学术关键词信息
5. **摘要标准化**: 自动清理摘要格式

## 扩展建议

### 1. 分页支持扩展

```python
# 在URL中添加页码参数支持
async def _extract_wanfang_search_with_pagination(self, page, base_url, max_articles):
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query)
    current_page = int(params.get('p', ['1'])[0])
    
    # 循环抓取多页
    while len(articles) < max_articles:
        # 构造当前页URL并抓取
        page_url = f"{base_url}&p={current_page}"
        page_articles = await self._extract_single_page(page, page_url)
        if not page_articles:
            break
        articles.extend(page_articles)
        current_page += 1
```

### 2. 高级过滤支持

```python
# 支持学科分类和时间范围过滤
advanced_params = {
    'subject': query_params.get('subject', [''])[0],    # 学科分类
    'year_start': query_params.get('ys', [''])[0],      # 起始年份
    'year_end': query_params.get('ye', [''])[0],        # 结束年份
    'institution': query_params.get('org', [''])[0]     # 机构名称
}
```

### 3. 引用信息提取

```python
# 提取文献引用信息
citation_info = await page.evaluate("""
    () => ({
        cited_count: document.querySelector('.cite-count')?.textContent?.trim() || '0',
        download_count: document.querySelector('.download-count')?.textContent?.trim() || '0',
        doi: document.querySelector('.doi-info')?.textContent?.trim() || ''
    })
""")
```

### 4. 多语言支持

```python
# 支持中英文文献标题和摘要
title_fields = ['title', 'title-en', 'title-zh']
abstract_fields = ['abstract', 'abstract-en', 'abstract-zh']

for field in title_fields:
    title_elem = await page.query_selector(f'.{field}')
    if title_elem:
        title = await title_elem.inner_text()
        break
```

## 维护建议

### 1. DOM结构监控
定期检查万方数据页面结构变化，特别关注：
- `.normal-list` 容器结构
- `.title-id-hidden` 隐藏ID位置
- 作者和关键词选择器

### 2. 类型映射更新
根据万方数据新增的文献类型及时更新 `type_map`：
```python
# 示例：新增预印本类型
type_map['preprint'] = 'preprint'
type_map['arxiv'] = 'preprint'
```

### 3. 性能优化
- 调整 `wait_for_selector` 超时时间
- 优化JavaScript执行频率
- 考虑添加缓存机制

### 4. 错误处理增强
```python
# 增加更详细的错误日志
try:
    await page.wait_for_selector('div.normal-list', timeout=10000)
except TimeoutError:
    logger.warning(f"Wanfang page load timeout for URL: {base_url}")
    return articles
except Exception as e:
    logger.error(f"Wanfang extraction error: {str(e)}")
    return articles
```

## 总结

万方数据的定制化爬取实现针对学术文献的特殊需求，提供了完整的元数据提取和智能类型识别功能。通过DOM等待机制确保动态内容完全加载，使用结构化JavaScript提取保证数据完整性。

该实现特别适合学术研究和文献管理场景，为WeRSS项目提供了高质量的中文学术资源支持，与其他专业网站的定制爬虫一起构成了完整的多领域内容抓取解决方案。