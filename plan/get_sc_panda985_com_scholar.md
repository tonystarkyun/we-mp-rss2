# sc.panda985.com Scholar 定制化方案

## 目标链接
- https://sc.panda985.com/scholar?q=%E4%BA%9A%E9%BA%BB%E7%B1%BD

## 定制化调整
- 在 `core/crawler.py` 新增 `_solve_panda_slider`，通过两段式拖拽模拟（中途停顿 + 收尾微调）自动通过 Panda985 的滑块校验，避免页面停留在验证态。
- 新增 `_extract_panda985_scholar`，在滑块通过后等待搜索结果渲染，批量提取 `#gs_res_ccl .gs_r.gs_or` 列表；字段包含标题、摘要、来源信息、年份（正则抓取 19/20 开头的年份）、类型标识（如 [PDF]）、PDF 下载链接。
- 在 `_extract_articles` 中增加域名分支，当访问 `*.panda985.com/scholar` 时优先使用定制解析逻辑，确保不会退回通用选择器。
- 归一化摘要和来源文本，去除多余空白并限制长度，输出结构与既有站点保持一致。

## 验证方式
- 运行 `python verify_panda985.py`，默认抓取前 5 条：
  - `success: True`
  - `total_found: 2`（示例环境下首屏仅解析出 2 条独特结果）
  - 会打印每条记录的标题与目标链接，便于人工抽查。

## 已知注意事项
- 滑块偶尔会重新出现，如遇重复验证可在重试逻辑中再次调用 `_solve_panda_slider`。
- 返回的外链多指向学术数据库，若需抓取正文需配合相应站点策略。
- 页面包含广告占位，当前通过选择器过滤；若 DOM 结构变化需同步更新提取逻辑。
