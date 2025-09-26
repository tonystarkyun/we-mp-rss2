# Statista flaxseed 定制爬取方案

## 修改概述
- 针对 `statista.com/search` 新增 `_extract_statista_search`，在页面内调用 `fetch` 拉取 `asJsonResponse=1` 接口并组装统计条目 URL，避免抓到导航链接。
- 在 `_extract_articles` 中优先识别 Statista 搜索 URL，命中后直接返回定制化结果，其余站点继续走通用选择器逻辑。
- 补充 `json/urlencode` 依赖、完善日志文案和 Docstring，确保输出可读且便于排查。

## 验证
- 运行 `py test_statista.py`，确认返回的 5 条结果均为亚麻籽相关统计页面。

## 后续建议
1. 依据接口的 `page` 参数实现多页抓取，扩展单次的文章覆盖面。
2. 为其它强依赖前端渲染的网站引入类似的 JSON 接口或定制选择器策略。
