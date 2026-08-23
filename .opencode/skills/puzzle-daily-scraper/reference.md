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
| Hashi | `https://www.puzzle-bridges.com/?size={n}` | 2, 4, 5, 7, 8, 10–14, 17, 18 |
| Tapa | `https://www.puzzle-tapa.com/?size={n}` | 1, 3–10 |
| LITS | `https://www.puzzle-lits.com/?size={n}` | 3, 5–12 |

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
| Hashi 站点 | `sites/hashi.py` |
| Tapa 站点 | `sites/tapa.py` |
| LITS 站点 | `sites/lits.py` |
| 每日 shell | `run_daily.sh` |

## Shingoki 尺寸注意

页面 `puzzleWidth/Height` 为**方格数**；`task` 编码的是角点网格，格数为 `(w+1)×(h+1)`。见 `sites/shingoki.py` 的 `grid_dims()`。

## Shakashaka 解码注意

页面 `puzzleWidth/Height` 即为格网尺寸（与 Masyu 相同，无需 +1）。`task` 编码规则（见 `sites/shakashaka.py` 的 `decode_task()`）：

- `B` → 无数字黑格 `x`
- `0`–`4` → 带线索数字的黑格
- `a`–`z` → 连续白格 `-`，长度 = `ord(ch) - ord('a') + 1`

size 映射：0=5×5, 1=10×10, 2=15×15, 3=20×20, 4=25×25, 5=30×30 daily, 6=40×40 weekly, 7=50×50 monthly。

## Hashi 解码注意

页面 `puzzleWidth/Height` 即为格网尺寸（与 Masyu 相同，无需 +1）。`task` 编码规则（见 `sites/hashi.py` 的 `decode_task()`）：

- `1`–`8` → 岛上数字线索
- `a`–`z` → 连续空格 `-`，长度 = `ord(ch) - ord('a') + 1`

size 映射（随机题稳定；special 为采样值，周/月题可能变化）：2=7×7, 4=10×10, 5=10×10, 7=15×15, 8=15×15, 10=25×25, 11=25×25, 12=30×40 weekly, 13=30×30 daily, 14=40×50 monthly, 17=15×15 dense, 18=25×25 dense。

## Tapa 解码注意

页面 `puzzleWidth/Height` 即为格网尺寸（与 Masyu 相同，无需 +1）。`task` 编码规则（见 `sites/tapa.py` 的 `decode_task()`）：

- `0`–`9` 连续数字属于**同一格**（每个数字都是一位数线索，一格可有多个）
- `_` 分隔两个相邻的线索格，避免 `45` 被当成一格里的 4 和 5（应为 `4_5`）
- `a`–`z` → 连续空格 `-`，长度 = `ord(ch) - ord('a') + 1`

size 映射（随机题稳定；special 为采样值，日/周/月题可能变化）：1=6×6, 3=10×10, 4=15×15, 5=15×15, 6=20×20, 7=20×20, 8=25×25 daily, 9=30×30 weekly, 10=35×35 monthly。

## LITS 解码注意

页面 `puzzleWidth/Height` 即为格网尺寸（与 Masyu 相同，无需 +1）。`task` 为逗号分隔的区域编号，按从上到下、从左到右给出；同一数字表示同一区域。

size 映射（随机题稳定；special 为采样值，日/周/月题可能变化）：3=8×8 hard, 5=10×10 hard, 6=15×15 normal, 7=15×15 hard, 8=20×20 normal, 9=20×20 hard, 10=30×30 daily, 11=40×40 weekly, 12=50×50 monthly。
