# Firefox 爬虫统一评估

## 当前爬虫实现
- `core/crawler.py:62-76` 仅通过 `p.chromium.launch(...)` 启动 Chromium，没有暴露 Playwright Firefox 的入口，所以要统一到 Firefox 需调整这段逻辑。
- `_find_browser_executable`（`core/crawler.py:112-139`）只搜索系统 Chrome/Edge，并将路径传给 Chromium；即便打包时准备了 Firefox 也不会被利用。
- 打包环境报出的 `Page.goto: Target page, context or browser has been closed` 属于 Chromium 在无完整系统依赖时常见的崩溃类型，进一步说明需要改用 Firefox。

## 打包与运行时配置
- `WeRSS-Linux.spec:24-27` 已将 `~/.cache/ms-playwright`（含 `firefox-1490`）和 `~/firefox-native/firefox` 条件打包进分发包；前提是构建机要提前安装 Playwright Firefox。
- `runtime_hook_playwright.py:17-61` 会在 PyInstaller 环境设置 `PLAYWRIGHT_BROWSERS_PATH` 与 `FIREFOX_BINARY`，为 Playwright Firefox 做好路径准备，但目前主代码仍旧调用 Chromium 导致这些配置未被使用。
- `build-linux.sh:42-45` 只安装 Python 依赖，没有执行 `playwright install firefox`；构建机若未预装 Firefox 缓存，打包产物就缺少对应二进制。

## 已实施改动
- `core/crawler.py` 现默认通过 `p.firefox.launch(...)` 启动 Playwright Firefox，并在 `core/crawler.py:58-71` 记录来源日志；`_find_browser_executable` 支持环境变量、Playwright 目录、打包目录与系统路径四层探测，同时通过 `_validate_firefox_binary`（`core/crawler.py:153-168`）过滤无效可执行文件；路透社定制逻辑增强了请求头部（`core/crawler.py:476-487`）并新增 `_is_reuters_article_path` 过滤导航链接，仅保留带有日期后缀或 `-id` 的文章路径（`core/crawler.py:1049-1070`）。
- `build-linux.sh:42-48` 在安装 Python 依赖后运行 `python3 -m playwright install firefox`，确保构建机缓存了 Firefox 浏览器。
- `runtime_hook_playwright.py:17-55` 在 PyInstaller 环境中同时设置 `FIREFOX_BINARY` 与 `PLAYWRIGHT_FIREFOX_EXECUTABLE_PATH`，并输出调试日志，方便确认路径。

## 推荐验证流程
1. 在开发环境运行 `python3 main.py -job True -init True`，确认日志出现 `Using bundled Playwright Firefox browser` 等字样且爬取成功。
2. 重新执行 `./build-linux.sh`，再用 `dist/start.sh` 启动测试，确认日志中出现 `Using Firefox executable:`（或 Bundled 提示）并完成爬取。
