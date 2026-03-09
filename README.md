# Paper Radar

Paper Radar is a personal research radar for computer systems, computer architecture, storage, and selected AI infrastructure topics.

Paper Radar 是一个面向 **计算机系统、计算机架构、存储**，并对**高相关 AI Infra** 做有限覆盖的个人论文雷达。

---

## Overview | 项目概览

Paper Radar focuses on a practical research workflow:

- discover recent papers
- keep a stable canonical reading pool
- personalize ranking from an existing Zotero library
- separate papers into actionable tiers
- preserve daily snapshots for later review
- provide structured deep-reading pages for representative papers

Paper Radar 关注的是一个更贴近真实科研使用的工作流：

- 跟踪近期论文
- 保留稳定的经典论文池
- 从现有 Zotero 文献库提取兴趣偏好
- 对论文做分级筛选
- 保留每日快照，便于回看
- 为代表性论文生成结构化精读页面

---

## Core Features | 核心功能

### 1. Topic-aware paper discovery
Papers are ranked with an explicit bias toward:

- storage systems
- key-value stores and LSM-tree related work
- SSD / NVMe / file system topics
- computer architecture and memory systems
- systems papers in the OSDI / ATC / EuroSys flavor

AI infrastructure papers are intentionally constrained unless they are clearly systems-oriented.

### 2. Canonical paper pool
A curated whitelist is maintained to stabilize the recommendation direction and avoid drifting too far toward short-term arXiv noise.

### 3. Zotero-based personalization
Local Zotero metadata is used to extract lightweight preference signals, which are then injected into the ranking pipeline as soft boosts.

### 4. Tiered reading workflow
Recent papers are grouped into:

- **Must Read / 必看**
- **Worth Skimming / 可扫**
- **Skip For Now / 先别看**

### 5. Deep reading pages
Representative papers can be rendered as structured analysis pages with:

- abstract translation
- motivation analysis
- methodology breakdown
- comparison tables
- experiment highlights
- implementation notes
- methodology flowcharts

### 6. Daily archive snapshots
Generated results are archived by date so that papers missed on one day remain accessible later.

---

## Interface | 界面结构

The dashboard is organized around several entry points:

- **Top Venues / 顶会**
- **Must Read / 必看**
- **Worth Skimming / 可扫**
- **Canonical Papers / 经典白名单**
- **Deep Reading Sample / 精读样板**
- **Archive / 历史归档**

Venue-style filters currently include:

- FAST-style
- HPCA-style
- OSDI / ATC / EuroSys-style
- DAC / ICCAD-style

---

## Repository Layout | 仓库结构

```text
assets/       dashboard templates
output/       generated pages, snapshots, and analysis outputs
references/   profiles, canonical paper lists, summary protocols
scripts/      ranking, rendering, Zotero integration, automation
```

---

## Local Usage | 本地使用

Build the site:

```bash
python3 scripts/build_site.py
```

Serve the generated output locally:

```bash
cd output
python3 -m http.server 8765
```

Open in browser:

- Dashboard: `http://localhost:8765`
- Deep reading sample: `http://localhost:8765/wisckey-analysis.html`
- Archive hub: `http://localhost:8765/archive/index.html`

---

## Automation | 自动化

A macOS launchd job can be installed for daily refresh:

```bash
bash scripts/install_daily_launchd.sh
```

Default schedule:

- **08:30 every day**

---

## GitHub Synchronization | GitHub 同步

A helper script is included for routine synchronization:

```bash
bash scripts/sync_github.sh
```

This script will:

1. rebuild the site
2. stage changes
3. create a commit if needed
4. push to the configured remote repository

---

## Current Status | 当前状态

This repository is currently optimized for:

- macOS
- local Zotero-based workflow
- systems / architecture / storage oriented reading

The project is intentionally opinionated: it prefers research usefulness and stable reading direction over generic paper aggregation.

本项目当前主要面向：

- macOS 环境
- 本地 Zotero 工作流
- 以系统 / 架构 / 存储为核心的论文跟踪需求

它不是一个泛化论文聚合器，而是一个更强调研究方向稳定性与阅读效率的个人雷达。 
