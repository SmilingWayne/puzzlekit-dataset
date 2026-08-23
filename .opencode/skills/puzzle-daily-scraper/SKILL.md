---
name: puzzle-daily-scraper
description: >-
  Operates and troubleshoots puzzlekit-dataset daily puzzle scrapers (Masyu,
  Shingoki, Shakashaka, Hashi, Tapa, LITS) under tools/puzzle-scraper/. Use when the user mentions daily scrape,
  GitHub Actions, launchd, puzzle-scraper, scrape_masyu, scrape_shingoki, scrape_shakashaka,
  scrape_hashi, scrape_tapa, scrape_lits, assets/scraped/, ingest/daily, or debugging automated puzzle collection from
  puzzle-masyu.com / puzzle-shingoki.com / puzzle-shakashaka.com / puzzle-bridges.com / puzzle-tapa.com / puzzle-lits.com.
---

# PuzzleKit 每日谜题爬取（puzzle-scraper）

GitHub Actions 每天 **01:00 / 11:00 UTC**（北京时间 09:00 主跑 + 19:00 兜底）抓取并 commit 到 `ingest/daily`。
当前站点：**Masyu**（size 2–18）、**Shingoki**（size 0–19）、**Shakashaka**（size 0–7）、**Hashi**（size 2, 4, 5, 7, 8, 10–14, 17, 18）、**Tapa**（size 1, 3–10）、**LITS**（size 3, 5–12）。

本机 launchd 仍可作为可选备份，不是云上路径。

> 编码/解码细节见各 `sites/<name>.py`；本 skill 只给**流程化操作与排查**。

## 仓库布局（权威路径）

```
tools/puzzle-scraper/
  lib/           fetch, store, runner, health
  sites/         masyu.py, shingoki.py, shakashaka.py, hashi.py, tapa.py, lits.py
  bin/           scrape_masyu.py, scrape_shingoki.py, scrape_shakashaka.py, scrape_hashi.py, scrape_tapa.py, scrape_lits.py
  scripts/       health_check.sh, verify_shingoki_write.sh
  run_daily.sh   每日调度（Masyu → Shingoki → Shakashaka → Hashi → Tapa → LITS）
  install_launchd.sh   可选 macOS 备份
  logs/          本机 launchd 日志（gitignored）

.github/workflows/daily-scrape.yml

assets/scraped/masyu/     masyu_NNN.json
assets/scraped/shingoki/  shingoki_NNN.json
assets/scraped/shakashaka/  shakashaka_NNN.json
assets/scraped/hashi/     hashi_NNN.json
assets/scraped/tapa/      tapa_NNN.json
assets/scraped/lits/      lits_NNN.json
```

`*.jsonl` 是本地调试日志，**不入库、不参与 catch-up / health**。去重看滚动 JSON 里的 `case_id` 与 `problem`。

**工作目录**：所有命令从 **仓库根目录** 执行。

## 快速命令

```bash
# 健康检查（只读，看 JSON store）
tools/puzzle-scraper/scripts/health_check.sh --ci
tools/puzzle-scraper/scripts/health_check.sh --probe   # 加网络 dry-run

# 手动 dry-run（不写盘）
python3 tools/puzzle-scraper/bin/scrape_masyu.py
python3 tools/puzzle-scraper/bin/scrape_shingoki.py
python3 tools/puzzle-scraper/bin/scrape_shakashaka.py
python3 tools/puzzle-scraper/bin/scrape_hashi.py
python3 tools/puzzle-scraper/bin/scrape_tapa.py
python3 tools/puzzle-scraper/bin/scrape_lits.py

# 手动落盘
python3 tools/puzzle-scraper/bin/scrape_masyu.py --write
python3 tools/puzzle-scraper/bin/scrape_shingoki.py --write
python3 tools/puzzle-scraper/bin/scrape_shakashaka.py --write
python3 tools/puzzle-scraper/bin/scrape_hashi.py --write
python3 tools/puzzle-scraper/bin/scrape_tapa.py --write
python3 tools/puzzle-scraper/bin/scrape_lits.py --write

# 跑完整每日链路（等同 Actions / launchd 触发）
tools/puzzle-scraper/run_daily.sh

python3 -m pytest tests/puzzle_scraper -q
```

## 一次运行的预期结果

| 站点 | 每次抓取 URL 数 | 典型 added | 典型 skipped |
|------|----------------|------------|--------------|
| Masyu | 17 (size 2–18) | ~14 随机 + 1 每日 | ~2（周/月题 id 重复） |
| Shingoki | 20 (size 0–19) | ~17 随机 + 3 special | ~0–3（special 日期重复） |
| Shakashaka | 8 (size 0–7) | ~5 随机 + 3 special | ~0–3（special 日期重复） |
| Hashi | 12 (2, 4, 5, 7, 8, 10–14, 17, 18) | ~9 随机 + 3 special | ~0–3（special 日期重复） |
| Tapa | 9 (1, 3–10) | ~6 随机 + 3 special | ~0–3（special 日期重复） |
| LITS | 9 (3, 5–12) | ~6 随机 + 3 special | ~0–3（special 日期重复） |

终端每行一种状态：`NEW` / `SKIP` / `INVALID` / `FAILED`。
汇总行：`added=N skipped=M failed=0` 为健康。同一天再跑应几乎全是 `SKIP`。

## 去重与滚动存储（验证要点）

每次 `--write` 前扫描该站点目录下**全部** `*_NNN.json`：

1. **case_id 重复** → `SKIP duplicate id …`
2. **problem 文本重复** → `SKIP duplicate problem`

case_id 规则（站点原生，见 `sites/*.py` 的 `make_case_id`）：
- 随机题：`size{N}_{puzzleID}`
- Daily/Weekly/Monthly：`size{N}_{YYYY-MM-DD}`（来自页面 date 选择器；**不是** `loadedId`）

历史遗留 `size{N}_0`：写入时会自动升级为 `size{N}_{date}`（从 `info` 括号内日期推断）。

单文件上限 **500** 条（`lib/store.py` 的 `MAX_PER_FILE`），满后自动 `masyu_002.json` 等。

## GitHub Actions

Workflow：`.github/workflows/daily-scrape.yml`

- 结果 **commit 回 `ingest/daily`** 的 `assets/scraped/`，不自动开 PR，不写 `assets/data/`。
- `schedule` 只在 workflow 文件出现在 **默认分支 `main`** 之后才会定时触发。
- 合并到 `main` 之前：push `ingest/daily`，在 Actions 里 **Run workflow**（选这个分支）做一次真跑。

巡检：

```text
- [ ] Actions run 绿色，或 scrape 失败但 store health 仍通过
- [ ] ingest/daily 上出现 chore(scrape): daily ingest YYYY-MM-DD（若有 NEW）
- [ ] health_check --ci 无 ERROR
- [ ] 抽查 1 条 NEW：problem 首行尺寸与 info 一致，source URL 正确
- [ ] 无大面积 INVALID
```

## 排查决策树

### A. Actions 没跑 / 没 commit

1. workflow 是否已在 `main`？（否则只有 `workflow_dispatch`）
2. 是否 push 了 `ingest/daily`（checkout `ref: ingest/daily`）
3. 查 Actions 日志：测试失败、站点 HTTP 失败、还是 `git push` 权限
4. 全 SKIP 时不会产生新 commit，这是正常的

### B. `FAILED` 或大量 `FAIL`（网络/HTTP）

1. `health_check.sh --probe` 看单页是否可达
2. 临时加大延迟：`--delay-min 8 --delay-max 15`
3. GitHub 机房 IP 被站点拦截时，先看 Actions 日志里的 HTTP 错误

### C. 大量 `INVALID`（解码或尺寸不匹配）

1. 用 curl 抓一页 HTML，确认 `var task`、`puzzleWidth/Height` 仍存在
2. 对比 `sites/<name>.py` 中 `_RE_*` 正则
3. 若仅某一站点：改对应 `sites/*.py`；共性逻辑改 `lib/`
4. 修复后：先 dry-run 全 size，再 `--write`

### D. `added=0` 但无 FAIL（全 SKIP）

正常：当日题已在滚动 JSON 里。不必再找 jsonl。

## 站点改版恢复流程

1. `curl -s "https://www.puzzle-<type>.com/?size=N" -o /tmp/page.html`
2. 在 HTML 中定位：`var task`、`ident`、`puzzleWidth/Height`、`puzzleID`、date 选择器
3. 更新 `sites/<type>.py` 的 `extract()` 与 `make_case_id()`
4. dry-run 全 size → `--write` → 更新本 skill 的「预期结果」表
5. 提交时注明站点变更日期

## 扩展新谜题类型

1. 新增 `sites/<name>.py`（实现 `extract`, `build_case`, `make_case_id`, `SPEC`）
2. 新增 `bin/scrape_<name>.py`（薄入口，复制现有 bin 文件改 import）
3. 在 `run_daily.sh` 注册；在 `lib/health.py` 的 `STORES` 加一行
4. 输出目录 `assets/scraped/<name>/`
5. 在本 skill 补充一行「预期结果」

## 更多参考

- 工具 README：[tools/puzzle-scraper/README.md](../../../tools/puzzle-scraper/README.md)
- 字段与 launchd 细节：[reference.md](reference.md)
