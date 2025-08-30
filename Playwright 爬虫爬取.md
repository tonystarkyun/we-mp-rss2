# Playwright 爬虫爬取



明白了！下面我用 **Playwright**（Python 与 Node.js 两种写法）手把手教你如何抓取 ScienceDirect 这个搜索页中**每条结果的标题与文章页链接（可视为“全文链接”入口）**。另外还给出一个不带浏览器的 `requests + BeautifulSoup` 方案（更快，但更容易受页面结构变化影响）。

> ⚠️ 提醒：抓取前请先阅读并遵守目标站点的服务条款与 robots.txt，控制频率、只做合理的学术/个人用途，避免高并发与过度访问。

------

## 方案 A：Playwright（Python，同步 API）

### 1) 安装

```bash
pip install playwright
python -m playwright install chromium
```

### 2) 脚本（保存为 `scidirect_playwright.py`）

下面的脚本会：

- 打开 `https://www.sciencedirect.com/search?qs=flaxseed`
- 提取当前页所有结果的**标题**与**文章页链接**
- 逐页点击 **Next** 翻页（可通过 `MAX_PAGES` 控制页数）
- 结果写入 CSV

```python
# scidirect_playwright.py
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import csv, time

START_URL = "https://www.sciencedirect.com/search?qs=flaxseed"
OUTPUT_CSV = "sciencedirect_flaxseed.csv"
MAX_PAGES = 5                # 抓取的页数上限
WAIT_BETWEEN_PAGES = 1.0     # 翻页后停顿，降低频率

TITLE_LINK_SELECTOR_PRIMARY = 'h2 a[href*="/science/article/"]'
# 备用选择器（页面结构变化时尝试）
TITLE_LINK_SELECTOR_FALLBACKS = [
    'a[href*="/science/article/"][aria-label]',
    'a[href*="/science/article/pii/"]'
]

NEXT_SELECTORS = [
    'a[aria-label="Next"]',
    'a[rel="next"]',
    'button[aria-label="Next"]'
]

def extract_rows(page):
    """从当前页提取 标题 + 文章链接"""
    results = page.eval_on_selector_all(
        TITLE_LINK_SELECTOR_PRIMARY,
        'els => els.map(el => ({title: el.textContent.trim(), url: el.href}))'
    )

    # 如主选择器找不到，尝试备用
    if not results:
        for sel in TITLE_LINK_SELECTOR_FALLBACKS:
            results = page.eval_on_selector_all(
                sel,
                'els => els.map(el => ({title: el.textContent.trim(), url: el.href}))'
            )
            if results:
                break

    # 清洗与去重
    seen = set()
    cleaned = []
    for r in results or []:
        title = (r.get("title") or "").strip()
        url = (r.get("url") or "").strip()
        if not title or not url:
            continue
        # 只保留文章详情页链接
        if "/science/article/" not in url:
            continue
        if url in seen:
            continue
        seen.add(url)
        cleaned.append({"title": title, "url": url})
    return cleaned

def click_next(page):
    """尝试点击下一页按钮，成功返回 True，失败返回 False"""
    for sel in NEXT_SELECTORS:
        if page.locator(sel).count() > 0:
            btn = page.locator(sel).first
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn.click()
                    return True
            except Exception:
                pass
    return False

def main():
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(START_URL, wait_until="domcontentloaded")

        # 有时会有 cookies 提示，尝试点击“Accept”
        for sel in ['button:has-text("Accept")',
                    'button:has-text("Agree")',
                    'button#onetrust-accept-btn-handler']:
            try:
                page.locator(sel).click(timeout=2000)
                break
            except Exception:
                pass

        # 等到结果元素出现（若页面结构变动，仍能继续但更稳妥）
        try:
            page.wait_for_selector(TITLE_LINK_SELECTOR_PRIMARY, timeout=15000)
        except PWTimeout:
            pass

        page_index = 1
        while True:
            print(f"[+] 抓取第 {page_index} 页：{page.url}")
            rows.extend(extract_rows(page))

            if page_index >= MAX_PAGES:
                break

            # 尝试翻页
            if not click_next(page):
                print("[i] 找不到下一页或已到末页。")
                break

            page.wait_for_load_state("domcontentloaded")
            time.sleep(WAIT_BETWEEN_PAGES)
            page_index += 1

        browser.close()

    # 写入 CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "url"])
        w.writeheader()
        w.writerows(rows)

    print(f"[✔] 共导出 {len(rows)} 条到 {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
```

**运行：**

```bash
python scidirect_playwright.py
```

> 想换关键词？把 `START_URL` 改成 `https://www.sciencedirect.com/search?qs=<你的关键词>`（URL 需编码）。
>  想抓更多页？把 `MAX_PAGES` 调大，注意频率与站点负载。

------

## 方案 B：Playwright（Node.js）

### 1) 安装

```bash
npm i -D playwright
npx playwright install chromium
```

### 2) 脚本（保存为 `scidirect_playwright.js`）

```js
// scidirect_playwright.js
const { chromium } = require('playwright');
const fs = require('fs');

const START_URL = 'https://www.sciencedirect.com/search?qs=flaxseed';
const OUTPUT_CSV = 'sciencedirect_flaxseed_node.csv';
const MAX_PAGES = 5;
const WAIT_BETWEEN_PAGES = 1000;

const TITLE_SEL = 'h2 a[href*="/science/article/"]';
const TITLE_FALLBACKS = [
  'a[href*="/science/article/"][aria-label]',
  'a[href*="/science/article/pii/"]'
];
const NEXT_SELECTORS = ['a[aria-label="Next"]', 'a[rel="next"]', 'button[aria-label="Next"]'];

async function extractRows(page) {
  let results = await page.$$eval(TITLE_SEL, els =>
    els.map(el => ({ title: el.textContent.trim(), url: el.href }))
  );

  if (!results.length) {
    for (const sel of TITLE_FALLBACKS) {
      results = await page.$$eval(sel, els =>
        els.map(el => ({ title: el.textContent.trim(), url: el.href }))
      );
      if (results.length) break;
    }
  }

  const seen = new Set();
  const cleaned = [];
  for (const r of results || []) {
    const title = (r.title || '').trim();
    const url = (r.url || '').trim();
    if (!title || !url) continue;
    if (!url.includes('/science/article/')) continue;
    if (seen.has(url)) continue;
    seen.add(url);
    cleaned.push({ title, url });
  }
  return cleaned;
}

async function clickNext(page) {
  for (const sel of NEXT_SELECTORS) {
    const btn = page.locator(sel).first();
    if (await btn.count()) {
      try {
        if (await btn.isVisible() && await btn.isEnabled()) {
          await btn.click();
          return true;
        }
      } catch (_) {}
    }
  }
  return false;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  await page.goto(START_URL, { waitUntil: 'domcontentloaded' });

  // Cookie 同意
  for (const sel of ['button:has-text("Accept")', 'button:has-text("Agree")', 'button#onetrust-accept-btn-handler']) {
    try { await page.click(sel, { timeout: 2000 }); break; } catch (_) {}
  }

  try { await page.waitForSelector(TITLE_SEL, { timeout: 15000 }); } catch (_) {}

  let all = [];
  let pageIndex = 1;

  while (true) {
    console.log(`[+] 抓取第 ${pageIndex} 页：${page.url()}`);
    all = all.concat(await extractRows(page));

    if (pageIndex >= MAX_PAGES) break;

    if (!(await clickNext(page))) {
      console.log('[i] 找不到下一页或已到末页。');
      break;
    }
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(WAIT_BETWEEN_PAGES);
    pageIndex += 1;
  }

  // 写 CSV
  const header = 'title,url\n';
  const lines = all.map(r =>
    `"${r.title.replace(/"/g, '""')}",${r.url}`
  );
  fs.writeFileSync(OUTPUT_CSV, header + lines.join('\n'), 'utf8');
  console.log(`[✔] 共导出 ${all.length} 条到 ${OUTPUT_CSV}`);

  await browser.close();
})();
```

**运行：**

```bash
node scidirect_playwright.js
```

------

## 方案 C：不用浏览器（`requests + BeautifulSoup`，更轻量）

> 这个方案直接请求 HTML 并解析，速度快，但如果站点改结构或需要前端渲染/同意弹窗，可能失败。失败时就用上面的 Playwright。

```python
# scidirect_requests_bs4.py
import csv, time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

BASE = "https://www.sciencedirect.com/search"
QUERY = "flaxseed"
SHOW = 25          # 每页条数（站点默认一般是 25）
MAX_PAGES = 5
SLEEP = 1.0
OUTPUT_CSV = "sciencedirect_flaxseed_bs4.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

rows = []
offset = 0

for page_idx in range(MAX_PAGES):
    params = {"qs": QUERY, "offset": offset, "show": SHOW}
    url = f"{BASE}?{urlencode(params)}"
    print(f"[+] 抓取第 {page_idx+1} 页：{url}")
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # 选择器：标题所在的 h2 > a
    anchors = soup.select('h2 a[href*="/science/article/"]')
    # 若抓不到，试备用
    if not anchors:
        anchors = soup.select('a[href*="/science/article/pii/"]')

    if not anchors:
        print("[i] 未找到结果，可能需要使用 Playwright。")
        break

    for a in anchors:
        title = a.get_text(strip=True)
        href = a.get("href", "").strip()
        if not title or not href:
            continue
        full = urljoin(BASE, href)
        rows.append({"title": title, "url": full})

    # 简单判断：如果这一页拿到的条数少于 SHOW，可能到末页
    if len(anchors) < SHOW:
        break

    offset += SHOW
    time.sleep(SLEEP)

# 写 CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["title", "url"])
    w.writeheader()
    w.writerows(rows)

print(f"[✔] 共导出 {len(rows)} 条到 {OUTPUT_CSV}")
```

------

## 可选：同时抓“PDF 直链”（若有开放获取）

有些文章有 **View PDF / Download PDF**。你可以在拿到文章页链接后，**再打开文章页**，尝试抓 PDF 按钮的链接（仅对开放获取文章可用）。以 Python + Playwright 为例，加入如下函数并在主循环中对每篇文章调用（注意频率）：

```python
def try_get_pdf_url(context, article_url):
    page = context.new_page()
    try:
        page.goto(article_url, wait_until="domcontentloaded")
        # 常见 PDF 按钮文本（不同期刊略有差异）
        # 也可尝试: 'a[title*="PDF"]', 'a:has-text("PDF")'
        for sel in ['a:has-text("PDF")', 'a[aria-label*="PDF"]', 'a[title*="PDF"]']:
            if page.locator(sel).count() > 0:
                href = page.locator(sel).first.get_attribute("href")
                if href:
                    return page.url if href.startswith("#") else page.evaluate("(h) => new URL(h, location.href).href", href)
    except Exception:
        pass
    finally:
        page.close()
    return None
```

> 温馨提示：为避免过多页面跳转，建议只对需要 PDF 的少量条目做这个二次访问，并适当 `sleep` 控制频率。

------

## 常见问题 & 可靠性小技巧

- **翻页失败怎么办？**
   上面示例默认点击“Next”。如果按钮选择器失效，可以用“偏移量”法直接构造 URL（`offset=0,25,50,...`）。
   例如：`https://www.sciencedirect.com/search?qs=flaxseed&show=25&offset=25`
- **选择器找不到元素？**
   打开开发者工具（F12），检查每条结果的标题实际标签路径（通常是 `h2 > a`），把脚本里的选择器改成你看到的实际结构即可。
- **速度与礼貌访问**：
   控制 `MAX_PAGES`、每页之间 `sleep`，不要并发打开大量页面；抓完即关浏览器实例。
- **输出格式**：
   例子用 CSV。若你偏向 JSON，只需把结果列表 `rows` 用 `json.dump` 写文件即可。

------

如果你告诉我你更偏好 **Python 或 Node**，以及想抓取的**页数/关键词**，我可以直接把上面对应版本的脚本按你的参数定制好（包括输出为 JSON、追加 PDF 链接等）。