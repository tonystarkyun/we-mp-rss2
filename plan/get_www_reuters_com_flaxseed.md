# Reuters flaxseed 定制爬取方案

## 需求背景
- 默认通用选择器在 Reuters 搜索页只能抓到栏目导航，无法读取真实文章。
- 标准 HTTP 请求会触发 DataDome 校验（HTTP 401）；但在浏览器环境中页面会加载 `articles-by-search-v2` JSON 接口。

## 修改要点
- `core/crawler.py:52` 启动浏览器前检测 `reuters.com`，命中后强制改用有头模式，规避 DataDome 对 headless 的拦截。
- `core/crawler.py:185` 新增 `_extract_reuters_search`：在页面上下文里调用 `articles-by-search-v2` 接口，解析返回 JSON，并拼装文章标题/链接。
- `core/crawler.py:415` 在 `_extract_articles` 前置 Reuters 分支，若成功获取文章则直接返回，再回退 Statista 分支和通用选择器。

## 校验方式
1. 执行 `py verify_reuters.py`，确认输出的链接为 Reuters 的实际文章详情页。
2. 如需回归验证，可再运行 `py verify_statista.py`，确保两个定制入口互不影响。

## 后续建议
- 若需翻页，可在 `_extract_reuters_search` 中调整 `payload['offset']` 与循环逻辑，向接口发起多次请求。
- 若未来 DataDome 策略变化，需同步更新 UA、延时或降级为更强的反爬策略。
