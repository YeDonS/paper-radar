# Paper Radar

一个本地论文列表和阅读页面，主要关注存储系统、计算机架构，以及部分 AI 基础设施论文。脚本负责收集、排序和生成页面，也可以结合 Zotero 文献库调整排序。

## 本地查看

```bash
git clone https://github.com/YeDonS/paper-radar.git
cd paper-radar
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/serve_local.py
```

打开 [http://127.0.0.1:8765](http://127.0.0.1:8765)，即可查看仓库中已有的页面。

## 更新论文列表

```bash
python3 scripts/build_site.py
```

构建过程会获取近期论文、生成阅读列表，并将上一次的结果保存到历史目录。更新时需要联网，并能读取本机的 Zotero 数据库，默认位置是 `~/Zotero/zotero.sqlite`。

页面包含近期论文、经典论文、阅读分析和历史记录。排序默认偏向存储与系统方向，适合个人使用。

## 阅读分析

模型精读会下载论文 PDF，并调用本机的 Gemini CLI 或 OpenAI 接口（通过 `OPENAI_API_KEY` 配置）。论文列表和已有的阅读页面可以独立查看。

## 目录

```text
assets/        页面模板
scripts/       检索、排序、生成页面和本地服务
references/    研究方向、经典论文清单和阅读模板
output/        生成的页面与论文列表
```

经典论文清单在 [references/canonical-papers.json](references/canonical-papers.json)，阅读模板在 [references/summary-template.md](references/summary-template.md)。

当前主要在 macOS 和本地 Zotero 环境下使用。macOS 定时更新脚本见 [scripts/install_daily_launchd.sh](scripts/install_daily_launchd.sh)，其中的目录需要按本机调整。
