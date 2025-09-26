# scholar.google.com flaxseed 定制化方案

## 目标链接
- https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=flaxseed&btnG=

## 定制化调整
- 在 `core/crawler.py` 新增 `_extract_google_scholar`，解析 `#gs_res_ccl .gs_r.gs_or` 结果卡片，返回标题、链接、摘要、来源信息、年份、PDF、引用次数等字段；域名统一补齐为 `https://scholar.google.com`。
- 对 `meta` 字段进行年份正则抽取，引用信息匹配 “Cited by” 链接并转换为数值，附带引用跳转与相关文献链接。
- 在 `_extract_articles` 中注入 `google.com/scholar` 专用分支，优先使用定制逻辑，避免退回通用选择器。
- 遇到 reCAPTCHA（检测 `form#captcha-form` / `recaptcha`）时记录 warning 并返回空列表，便于上层重试或人工介入。

## 验证方式
- 执行 `python verify_google_scholar.py`：
  - 预期 `success: True`
  - `total_found` 通常为 5（受 `max_articles` 限制，可按需调整）
  - 终端打印标题与目标链接，便于人工抽查。

## 注意事项
- Google Scholar 具备严格的反爬策略，频繁请求可能触发验证码；必要时需延长抓取间隔或使用代理。
- 部分链接指向付费数据库，若需要正文内容需结合目标站点权限策略。
- 如需分页抓取，可利用 `start=` 参数增量遍历，建议配合限速和缓存，避免触发风控。
