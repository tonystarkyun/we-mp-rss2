# FoodNavigator flaxseed 定制爬取方案

## 需求概览
- 默认通用选择器在 FoodNavigator 搜索页只能抓到静态栏目，真实结果由 Queryly 动态注入。
- 直接请求页面虽返回 HTML，但文章列表需要调用 Queryly `json.aspx` 接口才能获取。

## 修改内容
- `core/crawler.py:49` 新增 FoodNavigator 在热点站点名单，优先命中时调用专用提取逻辑。
- `core/crawler.py:185` 新增 `_extract_foodnavigator_search`：
  - 读取 `query`、`sort` 等查询参数，构造 Queryly API 调用；
  - 通过 Playwright 上下文请求 `https://api.queryly.com/json.aspx`，解析返回 JSON；
  - 组装标题、摘要、作者、发布日期及完整链接，支持按需分页抓取。
- `core/crawler.py:51/52` 引入 Queryly 接口常量（密钥、字段清单、批量大小），便于后续维护。

## 验证方式
- 运行 `py verify_foodnavigator.py`，应输出若干条 flaxseed 相关文章链接。
- 若要一次抓取更多文章，可传入更大的 `max_articles`（内部自动循环分页，每批 20 条）。

## 后续建议
1. 若需支持 Queryly 的 faceted 过滤（作者、类别、日期），可在 URL 层传入 `facetedkey`/`facetedvalue`/`daterange`，当前代码已兼容这些参数。
2. 如站点更新 Queryly key 或改用新接口，只需调整顶部常量与字段列表即可。
