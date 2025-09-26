# 万方论文检索 定制爬取方案

## 修改概览
- 在 `core/crawler.py` 中新增 `_extract_wanfang_search`，通过等待 `div.normal-list` 节点并解析标题、作者、摘要、关键词及隐藏的 `title-id-hidden`，再拼装详情页链接。
- 新增站点判定：命中 `s.wanfangdata.com.cn/paper` 时优先使用上述专用逻辑，避免走通用选择器。
- 复用隐藏 ID 的前缀推断 `_type`（如 `periodical -> perio`），构造 `https://www.wanfangdata.com.cn/details/detail.do` 访问口，保证可直接打开文章详情。

## 验证方式
- 运行 `py verify_wanfang.py`，应打印标题及 `detail.do` 详情页链接，确认至少返回 5 条记录。
- 若仍需验证其它站点，可再次执行 `py verify_foodnavigator.py` / `py verify_reuters.py` / `py verify_statista.py`。

## 后续建议
1. 如需抓取更多页，可在订阅 URL 中调整 `p` 参数；内部 `max_articles` 会控制循环次数。
2. 视业务需要可进一步补充更多 `_type` 映射（如 `patent`、`std` 等），并在返回结果中携带原始类型标签以便下游处理。
