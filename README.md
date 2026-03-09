# Paper Radar / 论文雷达

A personal paper radar for systems, architecture, storage, and selected AI infrastructure research.

一个面向 **系统、计算机架构、存储，以及少量高相关 AI Infra** 的私人论文雷达项目。

---

## English

### What it is

Paper Radar is a personalized research scouting and reading assistant.
It combines:

- daily/weekly recent-paper discovery
- canonical paper whitelist
- Zotero-based interest personalization
- tiered recommendations (`Must Read`, `Worth Skimming`, `Skip For Now`)
- visual dashboard
- professor-style deep reading pages with methodology flowcharts
- daily archive snapshots

### Main features

- **Venue-oriented browsing**
  - FAST-style
  - HPCA-style
  - OSDI / ATC / EuroSys-style
  - DAC / ICCAD-style
- **Personalized ranking** from Zotero library signals
- **Canonical paper pool** to stabilize long-term research taste
- **Deep-dive analysis pages** (example: WiscKey)
- **SVG methodology flowchart** embedded in the analysis page
- **Archive snapshots** so yesterday's recommendations are not lost
- **macOS launchd auto-refresh** skeleton

### Project structure

```text
assets/       UI templates
output/       generated dashboard, analysis pages, snapshots
references/   profiles, whitelist papers, summary templates
scripts/      ranking, rendering, Zotero integration, archiving, automation
```

### Local usage

```bash
python3 scripts/build_site.py
cd output && python3 -m http.server 8765
```

Open:

- Dashboard: `http://localhost:8765`
- Deep reading sample: `http://localhost:8765/wisckey-analysis.html`
- Archive hub: `http://localhost:8765/archive/index.html`

### Auto refresh

Install the macOS daily job:

```bash
bash scripts/install_daily_launchd.sh
```

Default schedule: **08:30 every day**.

### GitHub sync

A helper script is included:

```bash
bash scripts/sync_github.sh
```

It will:
- build the site
- commit changes
- push to the configured GitHub repository

---

## 中文

### 这是什么

Paper Radar 是一个偏研究工作流的私人论文雷达。
它把这些东西揉在一起：

- 每日 / 每周新论文发现
- 顶会 / 经典白名单池
- 基于 Zotero 的个性化兴趣建模
- 分级推荐（必看 / 可扫 / 先别看）
- 可视化 dashboard
- 教授视角的精读页与方法流程图
- 每日历史归档

### 核心功能

- **按顶会风格浏览**
  - FAST-style
  - HPCA-style
  - OSDI / ATC / EuroSys-style
  - DAC / ICCAD-style
- **基于 Zotero 的兴趣加权排序**
- **经典论文白名单池**，防止推荐被短期热点带偏
- **精读页面**（当前样板：WiscKey）
- **SVG 方法流程图** 直接嵌入页面
- **历史归档**，防止今天没看明天就没了
- **macOS launchd 自动更新骨架**

### 项目结构

```text
assets/       页面模板
output/       生成后的首页、精读页、归档
references/   用户画像、白名单论文、总结模板
scripts/      排序、渲染、Zotero 集成、归档、自动化脚本
```

### 本地运行

```bash
python3 scripts/build_site.py
cd output && python3 -m http.server 8765
```

打开：

- 主界面：`http://localhost:8765`
- 精读样板：`http://localhost:8765/wisckey-analysis.html`
- 归档中心：`http://localhost:8765/archive/index.html`

### 自动更新

安装 macOS 的每日任务：

```bash
bash scripts/install_daily_launchd.sh
```

默认每天 **08:30** 自动构建。

### GitHub 同步

附带了一键同步脚本：

```bash
bash scripts/sync_github.sh
```

它会：
- 重新构建站点
- 提交改动
- 推送到配置好的 GitHub 仓库

---

## Notes / 说明

- This repo currently focuses on macOS + Zotero local workflow.
- 目前主要面向 macOS + 本地 Zotero 使用场景。
- The recommendation logic is intentionally opinionated toward storage/systems/architecture.
- 推荐逻辑会明显偏向存储 / 系统 / 架构，而不是泛 AI 热门论文。
