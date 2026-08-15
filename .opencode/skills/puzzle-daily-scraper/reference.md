# puzzle-daily-scraper — reference

## JSON store schema

```json
{
  "name": "Masyu",
  "count": 17,
  "count_sol": 0,
  "data": {
    "size6_4172124": {
      "problem": "10 10\n…",
      "solution": "",
      "source": "https://www.puzzle-masyu.com/?size=6",
      "info": "10x10 Hard Masyu",
      "fetched_at": "2026-08-13T16:26:53+00:00"
    }
  }
}
```

`assets/data/` 下的正式数据集与 `assets/scraped/` **隔离**；scraped 为每日归档，合并入主库需单独流程。

Health check 用 `fetched_at` 的 UTC 日期前缀统计「今天新写入」；不读 jsonl。

## GitHub Actions

| 项 | 值 |
|----|-----|
| Workflow | `.github/workflows/daily-scrape.yml` |
| 触发 | 01:00、11:00 UTC；`workflow_dispatch` |
| Checkout / push | `ingest/daily` |
| 写入路径 | `assets/scraped/**/*.json` |

## launchd（可选本机备份）

| 项 | 值 |
|----|-----|
| Label | `com.puzzlekit.puzzle-scraper` |
| 触发 | 09:00、19:00 |
| 程序 | `puzzle-scraper.app` → `tools/puzzle-scraper/run_daily.sh` |
| Plist | `~/Library/LaunchAgents/com.puzzlekit.puzzle-scraper.plist` |
| stdout | `tools/puzzle-scraper/logs/daily.out.log` |
| stderr | `tools/puzzle-scraper/logs/daily.err.log` |

换机/新用户：运行 `install_launchd.sh` 并重新授予 helper app「完全磁盘访问」。

## 站点 URL 模板

| 站点 | URL | 默认 sizes |
|------|-----|------------|
| Masyu | `https://www.puzzle-masyu.com/?size={n}` | 2–18 |
| Shingoki | `https://www.puzzle-shingoki.com/?size={n}` | 0–19 |
| Shakashaka | `https://www.puzzle-shakashaka.com/?size={n}` | 0–7 |

## 代码入口地图

| 职责 | 文件 |
|------|------|
| HTTP 抓取 | `lib/fetch.py` |
| 去重/滚动写盘 | `lib/store.py` |
| 主循环/CLI | `lib/runner.py` |
| Store 健康检查 | `lib/health.py` |
| Masyu 站点 | `sites/masyu.py` |
| Shingoki 站点 | `sites/shingoki.py` |
| Shakashaka 站点 | `sites/shakashaka.py` |
| 每日 shell | `run_daily.sh` |

## Shingoki 尺寸注意

页面 `puzzleWidth/Height` 为**方格数**；`task` 编码的是角点网格，格数为 `(w+1)×(h+1)`。见 `sites/shingoki.py` 的 `grid_dims()`。

## Shakashaka 解码注意

页面 `puzzleWidth/Height` 即为格网尺寸（与 Masyu 相同，无需 +1）。`task` 编码规则（见 `sites/shakashaka.py` 的 `decode_task()`）：

- `B` → 无数字黑格 `x`
- `0`–`4` → 带线索数字的黑格
- `a`–`z` → 连续白格 `-`，长度 = `ord(ch) - ord('a') + 1`

size 映射：0=5×5, 1=10×10, 2=15×15, 3=20×20, 4=25×25, 5=30×30 daily, 6=40×40 weekly, 7=50×50 monthly。
