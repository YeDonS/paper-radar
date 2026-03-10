#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / 'scripts' / 'paper_radar.py'
PERSONALIZE = ROOT / 'scripts' / 'personalize_from_zotero.py'
CURATED = ROOT / 'scripts' / 'zotero_curated_pool.py'
CANONICAL = ROOT / 'scripts' / 'build_canonical_pool.py'
DEEP_READ = ROOT / 'scripts' / 'pdf_deep_read.py'
ASSET = ROOT / 'assets' / 'dashboard.html'
OUT = ROOT / 'output'
ANALYSIS_DIR = OUT / 'analysis'


def venue_tags(text):
    t = (text or '').lower()
    tags = []
    if any(k in t for k in ['ssd','flash','nvme','file system','filesystem','storage','lsm','rocksdb','persistent memory','wisckey','tiered','kv store','key-value']):
        tags.append('FAST-style')
    if any(k in t for k in ['cache','prefetch','tlb','cxl','chiplet','microarchitecture','memory system','accelerator','dram','nvm']):
        tags.append('HPCA-style')
    if any(k in t for k in ['distributed','cluster','datacenter','runtime','scheduler','resource','operating system','kernel','serverless']):
        tags.append('OSDI/ATC/EuroSys-style')
    if any(k in t for k in ['eda','chip design','placement','routing','iccad','dac','hardware design']):
        tags.append('DAC/ICCAD-style')
    if any(k in t for k in ['llm','inference','training','gpu','moe','serving']):
        tags.append('AI Infra')
    return tags or ['General Systems']


def canonical_boost(title, summary, canonical_rows):
    text = f"{title} {summary}".lower()
    best = 0
    matched = []
    for row in canonical_rows:
        overlap = 0
        for kw in row.get('keywords', []):
            kw = kw.lower()
            if kw and kw in text:
                overlap += 1
        if overlap >= 2:
            matched.append(row['title'])
            best = max(best, min(10, overlap * 2))
    return best, matched[:3]


def score_profile(tags, title, summary, raw_score, canonical_rows):
    text = f"{title}\n{summary}".lower()
    score = raw_score
    if 'FAST-style' in tags:
        score += 10
    if 'HPCA-style' in tags:
        score += 7
    if 'OSDI/ATC/EuroSys-style' in tags:
        score += 4
    if 'DAC/ICCAD-style' in tags:
        score += 2
    if 'AI Infra' in tags:
        score -= 6
    if 'AI Infra' in tags and any(t in tags for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style']):
        score += 3
    if any(k in text for k in ['storage','ssd','nvme','lsm','rocksdb','wisckey','filesystem','file system','tiered']):
        score += 6
    if any(k in text for k in ['cxl','cache','prefetch','tlb','memory system','chiplet']):
        score += 5
    if any(k in text for k in ['llm','diffusion','speech recognition','talking head']) and not any(k in text for k in ['storage','runtime','scheduler','cluster','serving']):
        score -= 5
    boost, matched = canonical_boost(title, summary, canonical_rows)
    score += boost
    return score, matched


def one_liner(entry):
    text = (entry.get('summary') or '').strip().lower()
    if any(k in text for k in ['storage','ssd','filesystem','file system','lsm','rocksdb','tiered']):
        return '存储味比较正，先看 bottleneck 有没有抓对。'
    if any(k in text for k in ['memory','cache','cxl','chiplet','microarchitecture']):
        return '偏内存/架构味，值得看是不是有真货而不是只会画图。'
    if 'serverless' in text and 'llm' in text:
        return '算是 AI infra 里比较像系统活的，能看。'
    if any(k in text for k in ['llm','inference','training']):
        return 'AI infra 方向，但得警惕是不是只是模型套壳。'
    return '先扫摘要和实验，别被标题党骗了。'


def tier(score):
    if score >= 26:
        return '必看'
    if score >= 14:
        return '可扫'
    return '先别看'


def pure_ai(tags):
    return 'AI Infra' in tags and not any(t in tags for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style', 'DAC/ICCAD-style'])


def cap_ai_ratio(items, limit_ai=2):
    out, ai_count = [], 0
    for item in items:
        if pure_ai(item['venue_tags']):
            if ai_count >= limit_ai:
                continue
            ai_count += 1
        out.append(item)
    return out


def slugify(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = text.encode('ascii', 'ignore').decode('ascii').lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text[:72] or 'paper'


def zh_summary(text):
    s = (text or '').strip()
    if not s:
        return '暂无摘要，别硬脑补。'
    return s


def bullets_from_summary(summary):
    raw = re.split(r'(?<=[\.!?;])\s+|(?<=[。！？；])', (summary or '').strip())
    bullets = [x.strip(' -\n\t') for x in raw if x.strip()]
    if not bullets:
        bullets = [(summary or '').strip()]
    return bullets[:6]


def infer_focus(item):
    tags = item.get('venue_tags') or []
    text = f"{item.get('title','')}\n{item.get('summary','')}".lower()
    if 'FAST-style' in tags:
        return '存储 / KV / SSD 路线'
    if 'HPCA-style' in tags:
        return '架构 / 内存系统 路线'
    if 'OSDI/ATC/EuroSys-style' in tags:
        return '系统 / 集群 / 运行时 路线'
    if 'AI Infra' in tags:
        return 'AI Infra / Serving 路线'
    if any(k in text for k in ['cache', 'memory', 'cxl', 'prefetch']):
        return '内存层次 / cache 路线'
    return '通用系统路线'


def html_escape(s):
    return html.escape(s or '', quote=True)


def render_analysis_html(item):
    title = item['title']
    summary = zh_summary(item.get('summary'))
    bullets = bullets_from_summary(summary)
    pdfa = item.get('pdf_analysis') or {}
    focus = pdfa.get('focus') or infer_focus(item)
    tags = ''.join(f'<span class="chip">{html_escape(t)}</span>' for t in (item.get('venue_tags') or []))
    authors = ', '.join(item.get('authors') or []) or '未知作者'
    link = item.get('link') or ''
    pdf_link = item.get('pdf_link') or ''
    reasons = item.get('why') or ''
    one = item.get('one_liner') or ''

    intro_pts = pdfa.get('intro_points') or []
    method_pts = pdfa.get('method_points') or []
    exp_pts = pdfa.get('experiment_points') or []
    focus_take_map = {
        '通信 / RF / 边缘硬件': '这是通信/RF 边缘检测路线，重点看特征设计、可解释性和硬件落地。',
        '存储 / KV / SSD': '这是存储/KV 路线，重点看 bottleneck 抓得准不准。',
        '架构 / 内存系统': '这是架构/内存系统路线，重点看收益是不是来自真实硬件约束。',
        '系统 / 集群 / 运行时': '这是系统/调度路线，重点看调度目标、约束和 baseline 公平性。',
        'AI Infra / Serving': '这是 AI infra 路线，重点看是不是系统改进而不是模型套壳。',
    }
    display_take = pdfa.get('core_take') or focus_take_map.get(focus) or one

    motivation_a = intro_pts[0] if len(intro_pts) > 0 else (bullets[0] if len(bullets) > 0 else '作者想解决一个系统瓶颈问题。')
    motivation_b = intro_pts[1] if len(intro_pts) > 1 else (bullets[1] if len(bullets) > 1 else '现有方案在效率、成本或可扩展性上有明显烂点。')
    motivation_c = intro_pts[2] if len(intro_pts) > 2 else (bullets[2] if len(bullets) > 2 else '核心直觉是换个系统切分方式，把关键路径优化掉。')

    steps = method_pts[:5] if method_pts else bullets[:5]
    while len(steps) < 5:
        defaults = [
            '定义输入与系统目标，先把问题边界钉死。',
            '设计核心模块或调度策略，压缩关键路径。',
            '加入资源管理 / 一致性 / 容错处理。',
            '输出结果并在目标 workload 上验证。',
            '根据瓶颈做进一步工程优化。',
        ]
        steps.append(defaults[len(steps)])

    flow_nodes = [
        'N1: 输入请求 / 数据 / workload',
        'N2: 预处理与任务切分',
        'N3: 核心方法模块',
        'N4: 资源调度 / 存储 / 执行路径优化',
        'N5: 输出结果与性能评估',
    ]
    flow_edges = ['N1 -> N2', 'N2 -> N3', 'N3 -> N4', 'N4 -> N5']
    flow_plain = [f'1. {steps[0]}', f'2. {steps[1]}', f'3. {steps[2]}', f'4. {steps[3]}', f'5. {steps[4]}']
    mode = pdfa.get('mode', 'abstract')
    used_pdf = mode == 'pdf'
    mode_label = 'PDF 深读' if used_pdf else '摘要降级'
    hero_note = '自动精读页（已接入 PDF 正文抽取与结构化总结）' if used_pdf else '自动精读页（这次 PDF 没吃进去，当前是摘要降级版，不算真精读）'
    abstract_note = '注：本页优先基于 PDF 正文抽取与结构化重写。' if used_pdf else '注：这次没成功吃到 PDF，当前是基于摘要的降级结果。'
    excerpt_block = f'<details><summary>正文摘录（自动抓取）</summary><pre>{html_escape(pdfa.get("raw_excerpt", ""))}</pre></details>' if pdfa.get('raw_excerpt') else ''
    exp_source = exp_pts[:4] if exp_pts else ['当前可见证据主要来自摘要，说明作者声称方法在目标场景上有效。', '但具体提升数字、baseline、公平性、实验设置，必须看 PDF 正文才能下刀。']
    exp_block = ''.join(f'<p>- {html_escape(x)}</p>' for x in exp_source)

    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{html_escape(title)} · 自动精读</title><style>
:root{{--bg:#0b1020;--panel:#121a30;--soft:#1a2442;--text:#ecf2ff;--muted:#9fb0d1;--accent:#7c9cff;--good:#5bd6a1}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,system-ui,sans-serif;background:radial-gradient(circle at top,#18254f 0,#0b1020 45%,#0b1020 100%);color:var(--text)}}.wrap{{max-width:1280px;margin:0 auto;padding:24px 20px 70px}}.layout{{display:grid;grid-template-columns:240px 1fr 320px;gap:18px}}.nav,.panel,.aside{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:18px}}.nav a{{display:block;color:#c8d6ff;text-decoration:none;padding:8px 0}}.hero h1{{margin:0 0 8px 0}}.muted{{color:var(--muted)}}.chip{{display:inline-block;padding:5px 10px;border-radius:999px;background:rgba(124,156,255,.15);margin-right:8px;margin-top:8px}}.step{{padding:12px;border-left:3px solid var(--accent);background:var(--panel);border-radius:12px;margin:10px 0}}.table{{width:100%;border-collapse:collapse}}.table td,.table th{{border:1px solid rgba(255,255,255,.08);padding:10px;vertical-align:top}}.table th{{background:rgba(255,255,255,.05)}}.kpi{{background:#121a30;border:1px solid rgba(255,255,255,.06);padding:12px;border-radius:14px;margin-bottom:10px}}code,pre{{white-space:pre-wrap;word-break:break-word}}a{{color:#c8d6ff}}@media(max-width:1100px){{.layout{{grid-template-columns:1fr}}.nav,.aside{{order:2}}}}</style></head>
<body><div class="wrap"><div class="layout"><aside class="nav"><h3>导航</h3><a href="#abs">0. 摘要翻译</a><a href="#motivation">1. 方法动机</a><a href="#design">2. 方法设计</a><a href="#compare">3. 与其他方法对比</a><a href="#exp">4. 实验表现与优势</a><a href="#apply">5. 学习与应用</a><a href="#summary">6. 总结</a><a href="#flow">7. 方法流程图</a></aside><main class="panel"><section class="hero"><h1>{html_escape(title)}</h1><div class="muted">{html_escape(hero_note)}</div><div><span class="chip">{html_escape(mode_label)}</span>{tags}</div></section>
<section id="abs"><h2>0. 摘要翻译</h2><p>{html_escape(summary)}</p><p class="muted">{html_escape(abstract_note)}</p>{f'<p><a href="{html_escape(link)}" target="_blank">摘要页</a> · <a href="{html_escape(pdf_link)}" target="_blank">PDF</a></p>' if pdf_link else ''}</section>
<section id="motivation"><h2>1. 方法动机</h2><p><b>1a 作者为什么提出这个方法：</b>{html_escape(motivation_a)}</p><p><b>1b 现有方法痛点/不足：</b>{html_escape(motivation_b)}</p><p><b>1c 研究假设或核心直觉：</b>{html_escape(motivation_c)}</p></section>
<section id="design"><h2>2. 方法设计</h2>
<div class="step"><b>Step 1</b><br>{html_escape(steps[0])}</div>
<div class="step"><b>Step 2</b><br>{html_escape(steps[1])}</div>
<div class="step"><b>Step 3</b><br>{html_escape(steps[2])}</div>
<div class="step"><b>Step 4</b><br>{html_escape(steps[3])}</div>
<div class="step"><b>Step 5</b><br>{html_escape(steps[4])}</div>
<p class="muted">方法主线判断：{html_escape(focus)}。当前模式：{html_escape(mode_label)}；扫描页数：{html_escape(str(pdfa.get('pages_scanned','-')))}。</p>{excerpt_block}</section>
<section id="compare"><h2>3. 与其他方法对比</h2><table class="table"><tr><th>维度</th><th>结论</th></tr><tr><td>主流方案</td><td>通常在精度、延迟、成本、可解释性或部署资源之间拉扯，很难全都要。</td></tr><tr><td>本文方法</td><td>{html_escape(display_take or '本文更像是在部署约束下重新平衡性能、成本和可落地性。')}</td></tr><tr><td>创新点</td><td>{html_escape(method_pts[0] if method_pts else display_take or '需要结合正文继续细看。')}</td></tr><tr><td>适用场景</td><td>{html_escape(focus)}</td></tr><tr><td>风险</td><td>重点检查 baseline 是否够强、指标是否完整、硬件/部署收益是否真的可落地。</td></tr></table></section>
<section id="exp"><h2>4. 实验表现与优势</h2>{exp_block}<p>- 快速检查清单：有没有和强 baseline 比；有没有端到端指标；有没有成本/延迟/吞吐一起报；有没有极端 case。</p><p class="muted">别被摘要吹晕，这是系统论文，不是许愿池。</p></section>
<section id="apply"><h2>5. 学习与应用</h2><p>- 如果你要拿来做研究借鉴，先抓它的方法切分方式，不要先学包装词。</p><p>- 真正该抄的是：瓶颈建模、模块边界、关键优化点、实验对照设计。</p><p>- 如果后面接上 PDF 自动解析，这里可以继续补：开源状态、复现路径、关键超参/实现细节、可迁移任务。</p></section>
<section id="summary"><h2>6. 总结</h2><p style="font-size:22px;font-weight:800">{html_escape((display_take or '正文已抓到，继续看方法细节。')[:20])}</p><p>速记版：</p><p>{'<br>'.join(html_escape(x) for x in flow_plain)}</p><p class="muted">下一步建议：先看 PDF 的方法图、系统架构图、实验表 1 和 ablation，再决定值不值得深挖。</p></section>
<section id="flow"><h2>7. 方法流程图</h2><h3>Plain-text numbered flow</h3><pre>{html_escape(chr(10).join(flow_plain))}</pre><h3>Draw.io draft nodes/edges</h3><pre>Nodes:\n{html_escape(chr(10).join('- ' + x for x in flow_nodes))}\n\nEdges:\n{html_escape(chr(10).join('- ' + x for x in flow_edges))}</pre><h3>Mermaid</h3><pre>flowchart TD\n  N1[输入请求/数据/workload] --> N2[预处理与任务切分]\n  N2 --> N3[核心方法模块]\n  N3 --> N4[资源调度/存储/执行路径优化]\n  N4 --> N5[输出结果与性能评估]</pre></section></main><aside class="aside"><h3>关键信息卡</h3><div class="kpi"><b>作者</b><div class="muted">{html_escape(authors)}</div></div><div class="kpi"><b>打分 / 层级</b><div class="muted">{html_escape(str(item.get('score','')))} / {html_escape(item.get('tier',''))}</div></div><div class="kpi"><b>命中理由</b><div class="muted">{html_escape(reasons)}</div></div><div class="kpi"><b>一句话判断</b><div class="muted">{html_escape(display_take)}</div></div>{f'<div class="kpi"><b>摘要页</b><div><a href="{html_escape(link)}" target="_blank">打开摘要页</a></div></div>' if link else ''}{f'<div class="kpi"><b>PDF</b><div><a href="{html_escape(pdf_link)}" target="_blank">打开 PDF</a></div></div>' if pdf_link else ''}</aside></div></div></body></html>'''




def enrich_with_pdf(item):
    pdf_link = item.get('pdf_link')
    if not pdf_link or not DEEP_READ.exists():
        return item
    try:
        raw = subprocess.check_output([
            'python3', str(DEEP_READ),
            '--title', item.get('title',''),
            '--pdf-url', pdf_link,
            '--summary', item.get('summary','')
        ], text=True, timeout=120)
        item['pdf_analysis'] = json.loads(raw)
    except Exception as e:
        item['pdf_analysis'] = {'mode': 'abstract', 'error': str(e)}
    return item

def build_analysis_pages(items):
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    for idx, item in enumerate(items, 1):
        slug = slugify(item['title'])
        if slug in seen:
            slug = f'{slug}-{idx}'
        seen.add(slug)
        item['analysis_path'] = f'./analysis/{slug}.html'
        html_doc = render_analysis_html(item)
        (ANALYSIS_DIR / f'{slug}.html').write_text(html_doc)


def main():
    ap = argparse.ArgumentParser(description='Render markdown digest + pretty dashboard for paper radar')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--top', type=int, default=10)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.check_output(['python3', str(PERSONALIZE)], text=True)
    except Exception:
        pass
    subprocess.check_output(['python3', str(CANONICAL)], text=True)

    raw = subprocess.check_output(['python3', str(RADAR), '--days', str(args.days), '--top', '30', '--json'], text=True)
    rows = json.loads(raw)
    curated_rows = json.loads(subprocess.check_output(['python3', str(CURATED), '--top', '8'], text=True))
    canonical_rows = json.loads((OUT / 'canonical.json').read_text())

    items = []
    counts = Counter()
    for row in rows:
        e = row['entry']
        text = f"{e['title']}\n{e['summary']}"
        tags = venue_tags(text)
        adj, matched = score_profile(tags, e['title'], e['summary'], row['score'], canonical_rows)
        why = row['reasons'][:6]
        if matched:
            why.append('canon:' + ' / '.join(matched))
        items.append({
            'source': 'recent',
            'score': adj,
            'tier': tier(adj),
            'title': e['title'],
            'authors': e['authors'][:5],
            'link': e['link'],
            'pdf_link': (e['link'].replace('/abs/', '/pdf/') + '.pdf') if e.get('link') and '/abs/' in e['link'] else '',
            'arxiv_id': e['link'].rstrip('/').split('/')[-1] if e.get('link') else '',
            'why': '；'.join(why),
            'venue_tags': tags,
            'one_liner': one_liner(e),
            'summary': e['summary'],
            'matched_canonical': matched,
        })

    items.sort(key=lambda x: x['score'], reverse=True)
    items = cap_ai_ratio(items, limit_ai=2)
    prefer = [x for x in items if any(t in x['venue_tags'] for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style']) or x['matched_canonical']]
    backup = [x for x in items if x not in prefer]
    items = (prefer + backup)[:args.top]
    for idx, item in enumerate(items):
        if idx < 5:
            enrich_with_pdf(item)
    build_analysis_pages(items)

    curated = []
    for row in curated_rows:
        tags = row.get('tags') or ['Systems']
        for t in tags:
            counts[t] += 1
        curated.append({
            'source': 'curated',
            'score': row['score'] + 20,
            'tier': '经典',
            'title': row['title'],
            'authors': [],
            'link': '',
            'why': '；'.join(tags) + '；来自 Zotero 现有论文池',
            'venue_tags': tags,
            'one_liner': '这类更像你的长期主线，适合精读和做研究借鉴。',
            'summary': row.get('abstract') or '',
            'publicationTitle': row.get('publicationTitle'),
            'date': row.get('date'),
            'itemID': row.get('itemID'),
        })

    for item in canonical_rows:
        for t in item['venue_tags']:
            counts[t] += 1
    for item in items:
        for t in item['venue_tags']:
            counts[t] += 1

    tier_counts = Counter(item['tier'] for item in items)
    payload = {
        'meta': {
            'days': args.days,
            'fetched': 120,
            'matched': len(rows),
            'tag_counts': dict(counts),
            'tier_counts': dict(tier_counts),
        },
        'featured_analysis': {
            'title': 'WiscKey 精读样板',
            'path': './wisckey-analysis.html'
        },
        'canonical': canonical_rows,
        'curated': curated,
        'items': items,
    }
    (OUT / 'latest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    md = ['# Paper Radar Digest', '', f'- window: last {args.days} days', f'- shown: {len(items)}', '']
    md += ['## 精读样板', '', '- WiscKey 精读样板：见 `wisckey-analysis.html`', '']
    md += ['## 顶会 / 经典白名单池', '']
    for i, p in enumerate(canonical_rows, 1):
        md += [f'### 白名单-{i}. {p["title"]}', f'- venue: {p["why"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- take: {p["one_liner"]}', '']
    md += ['## Zotero 经典相关论文', '']
    for i, p in enumerate(curated, 1):
        md += [f'### 经典-{i}. {p["title"]}', f'- score: {p["score"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- why: {p["why"]}', f'- take: {p["one_liner"]}', '']
    for group in ['必看', '可扫', '先别看']:
        subset = [x for x in items if x['tier'] == group]
        if not subset:
            continue
        md += [f'## {group}', '']
        for i, p in enumerate(subset, 1):
            md += [f'### {group}-{i}. {p["title"]}', f'- score: {p["score"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- why: {p["why"]}', f'- take: {p["one_liner"]}', f'- link: {p["link"]}', f'- pdf: {p.get("pdf_link", "")}', f'- analysis: {p["analysis_path"]}', '']
    (OUT / 'latest.md').write_text('\n'.join(md))
    shutil.copy2(ASSET, OUT / 'index.html')
    try:
        subprocess.check_output(['python3', str(ROOT / 'scripts' / 'archive_snapshot.py')], text=True)
    except Exception:
        pass
    print(str(OUT / 'index.html'))
    print(str(OUT / 'latest.md'))

if __name__ == '__main__':
    main()
