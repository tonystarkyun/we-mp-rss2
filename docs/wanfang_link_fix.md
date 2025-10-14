# 万方搜索结果链接修复说明

## 背景
- 订阅链接 `https://s.wanfangdata.com.cn/paper?...` 在最近的页面改版后，不再直接在 DOM 中暴露可访问的详情链接。
- 我们原来的爬虫只能拼出 `https://www.wanfangdata.com.cn/details/detail.do?...`，这些地址已经被下线，导致抓取到的文章点击后返回 404。

## 根因分析
- 搜索页通过前端 gRPC-Web 接口 `SearchService.SearchService/search` 返回二进制结果，包含 `Periodical/Thesis/...` 类别、真实详情 token（例如 `ChVQZX...`）以及隐藏的文献 ID `periodical_xxx`。
- 页面渲染时在浏览器内解析该响应并生成可访问的 `https://d.wanfangdata.com.cn/{category}/{token}` 链接，但爬虫并未调用或解析这段响应。

## 修复措施
1. **添加 gRPC-Web 解析逻辑** (`core/crawler.py:470-565`)
   - 根据订阅 URL 中的 `q`、`p` 参数构造 gRPC-Web 请求 payload。
   - 直接向 `SearchService.SearchService/search` 发送 POST，解码响应文本。
   - 用正则提取 `(类型, token, 文献后缀)`，映射成 `record_id -> 真实详情链接`。
2. **更新链接选择策略** (`core/crawler.py:410-434`)
   - 优先使用搜索页 `<a>` 的现有链接。
   - 若页面未给出链接，则根据 `title-id-hidden` 在上述映射表中查找真实链接。
   - 仅在映射失败时退回旧的 `detail.do` 拼接逻辑，保证兼容。
3. **补充类型映射**
   - 为 `Thesis`、`Standard`、`Policy` 等类型分别指定正确的路径及 `record_id` 前缀，使所有类别都能生成有效 URL。

## 验证
- 运行 `python3 verify_wanfang.py`，返回的 5 条文章链接均指向 `https://d.wanfangdata.com.cn/...` 并可正常访问。
- 针对不同关键词（如 “硕士论文”）测试，期刊、会议、学位等类型的链接均解析成功。

## 风险与后续建议
- gRPC 接口依赖于万方现有协议，如后续字段变更需调整解析正则。
- 若需批量抓取多页，可继续利用 `p` 参数并重用新映射逻辑；注意接口访问频率以免触发限流。
