#!/usr/bin/env python3
import argparse
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'output' / 'pdf_cache'

SECTION_ALIASES = {
    'intro': ['introduction', 'overview', 'background', 'motivation'],
    'method': ['methodology', 'method', 'design', 'approach', 'system design', 'architecture', 'implementation', 'framework'],
    'exp': ['evaluation', 'experiments', 'experimental setup', 'results', 'performance evaluation'],
}

STOP_PATTERNS = [
    r'^emails?:', r'@', r'arxiv:', r'^index terms', r'^keywords?', r'^references?$',
    r'^figure\s+\d+', r'^table\s+\d+', r'^section\s+[ivx0-9]+', r'^\d+\) ',
    r'copyright', r'preprint', r'submitted to', r'author', r'university', r'journal',
]

NEGATIVE_HINTS = [
    'section iii describes', 'section iv details', 'emails:', 'index terms', 'arxiv:',
    'this work has been submitted', 'figure', 'table', 'copyright', 'preprint',
]

GROUP_KEYWORDS = {
    'intro': ['problem', 'challenge', 'motivation', 'bottleneck', 'threat', 'limitation', 'why'],
    'method': ['propose', 'present', 'design', 'framework', 'pipeline', 'architecture', 'algorithm', 'module', 'scheduler', 'booleanization', 'quantized'],
    'exp': ['accuracy', 'latency', 'throughput', 'speedup', 'overhead', 'cost', 'memory', 'resource', 'fpga', 'benchmark', 'baseline'],
}


def slugify(text: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:80] or 'paper'


def download(url: str, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        return out
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'paper-radar/0.4'})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        out.write_bytes(resp.read())
    return out


def clean(text: str) -> str:
    text = text.replace('\x00', ' ')
    text = re.sub(r'-\s+', '', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_sentences(text: str):
    parts = re.split(r'(?<=[\.!?])\s+|(?<=[。！？])', text)
    out = []
    for p in parts:
        s = clean(p)
        if len(s) < 35 or len(s) > 500:
            continue
        out.append(s)
    return out


def find_section_start(full_text: str, names):
    lower = full_text.lower()
    starts = []
    for name in names:
        for pat in [rf'\b{name}\b', rf'\d+\.\s*{name}\b', rf'{name}\s*[:\-]']:
            m = re.search(pat, lower)
            if m:
                starts.append(m.start())
    return min(starts) if starts else -1


def next_section_boundary(full_text: str, start: int):
    if start < 0:
        return min(len(full_text), 9000)
    lower = full_text.lower()[start + 50:]
    m = re.search(r'(\b\d+\.\s*[a-z][a-z \-]{3,40}\b|\brelated work\b|\bconclusion\b|\bdiscussion\b|\breferences\b)', lower)
    if not m:
        return min(len(full_text), start + 9000)
    return min(len(full_text), start + 50 + m.start())


def grab_section(full_text: str, group: str, fallback_start=0, span=7000):
    start = find_section_start(full_text, SECTION_ALIASES[group])
    if start < 0:
        start = fallback_start
        end = min(len(full_text), start + span)
    else:
        end = next_section_boundary(full_text, start)
        end = min(end, start + span)
    return clean(full_text[start:end])


def bad_sentence(s: str) -> bool:
    low = s.lower().strip()
    if len(low) < 35:
        return True
    if sum(ch.isdigit() for ch in low) > max(10, len(low) // 5):
        return True
    for pat in STOP_PATTERNS:
        if re.search(pat, low):
            return True
    if low.count('{') or low.count('}'):
        return True
    if low.startswith('we compare our approach') and 'baseline' in low and len(low) < 80:
        return True
    return False


def sentence_score(sentence: str, group: str):
    s = sentence.lower()
    if bad_sentence(sentence):
        return -999
    score = 0
    for bad in NEGATIVE_HINTS:
        if bad in s:
            score -= 8
    for kw in GROUP_KEYWORDS[group]:
        if kw in s:
            score += 4
    if any(k in s for k in ['we propose', 'we present', 'our approach', 'our framework', 'our design']):
        score += 8
    if any(k in s for k in ['benchmark', 'we benchmark', 'baseline']) and group == 'method':
        score -= 5
    if re.search(r'\b\d+(\.\d+)?\s*(x|%|mb|gb|ms|s)\b', s):
        score += 3
    if 60 <= len(sentence) <= 220:
        score += 2
    return score


def summarize_sentences(text: str, group: str, limit=4):
    sents = split_sentences(text)
    ranked = []
    seen = set()
    for i, s in enumerate(sents):
        key = re.sub(r'\W+', '', s.lower())[:120]
        if key in seen:
            continue
        seen.add(key)
        ranked.append((sentence_score(s, group), i, s))
    ranked = [x for x in ranked if x[0] > 0]
    ranked.sort(key=lambda x: (-x[0], x[1]))
    chosen = sorted(ranked[:limit], key=lambda x: x[1])
    return [x[2] for x in chosen]


def infer_focus(title: str, abstract: str, method: str):
    lower = (title + ' ' + abstract + ' ' + method[:2500]).lower()
    if any(k in lower for k in ['rf', '5g', 'wireless', 'jamming', 'fpga', 'ssb', 'radio']):
        return '通信 / RF / 边缘硬件'
    if any(k in lower for k in ['lsm', 'rocksdb', 'ssd', 'nvme', 'storage', 'file system', 'kv store']):
        return '存储 / KV / SSD'
    if any(k in lower for k in ['cache', 'memory', 'cxl', 'chiplet', 'prefetch']):
        return '架构 / 内存系统'
    if any(k in lower for k in ['cluster', 'runtime', 'scheduler', 'serverless', 'distributed', 'faas', 'optical circuit switch']):
        return '系统 / 集群 / 运行时'
    if any(k in lower for k in ['llm', 'inference', 'serving', 'training', 'moe']):
        return 'AI Infra / Serving'
    return '通用系统'


def rewrite_intro(title: str, abstract: str, intro_pts):
    if intro_pts:
        pts = intro_pts[:3]
    else:
        pts = split_sentences(abstract)[:3]
    while len(pts) < 3:
        pts.append('作者想解决一个真实部署场景里的性能、成本或可靠性问题。')
    return pts[:3]


def rewrite_method(title: str, abstract: str, method_pts):
    method_pts = sorted(method_pts, key=lambda x: (0 if any(k in x.lower() for k in ['we propose','we present','our approach','our framework','our design','by learning','we formulate']) else 1, len(x)))
    pts = method_pts[:5]
    if not pts:
        pts = split_sentences(abstract)[:5]
    while len(pts) < 5:
        defaults = [
            '先定义输入、约束和优化目标。',
            '构造核心模块或调度/分类/执行流程。',
            '补齐部署与资源约束相关设计。',
            '与强 baseline 做同条件对比。',
            '报告关键性能、成本或精度结果。',
        ]
        pts.append(defaults[len(pts)])
    return pts[:5]


def rewrite_experiment(exp_pts, abstract: str):
    pts = exp_pts[:4]
    if not pts:
        pts = split_sentences(abstract)[:4]
    return pts[:4]


def analyze(pdf_path: Path, title: str, abstract: str):
    reader = PdfReader(str(pdf_path))
    pages = min(len(reader.pages), 14)
    texts = []
    for i in range(pages):
        try:
            texts.append(reader.pages[i].extract_text() or '')
        except Exception:
            continue
    full = clean(' '.join(texts))
    intro = grab_section(full, 'intro', 0, 7000)
    method = grab_section(full, 'method', max(len(intro) // 2, 0), 9000)
    exp = grab_section(full, 'exp', max(len(method) // 2, 0), 9000)

    intro_pts = rewrite_intro(title, abstract, summarize_sentences(intro or abstract, 'intro', 3))
    method_pts = rewrite_method(title, abstract, summarize_sentences(method or abstract, 'method', 5))
    exp_pts = rewrite_experiment(summarize_sentences(exp or abstract, 'exp', 4), abstract)
    focus = infer_focus(title, abstract, method)

    core_candidates = [x for x in method_pts if any(k in x.lower() for k in ['we propose','we present','our approach','our framework','our design','by learning','we formulate'])] or method_pts or intro_pts or [abstract[:120]]
    return {
        'mode': 'pdf' if full else 'abstract',
        'pages_scanned': pages,
        'focus': focus,
        'intro_points': intro_pts,
        'method_points': method_pts,
        'experiment_points': exp_pts,
        'core_take': core_candidates[0],
        'flow_steps': method_pts[:5],
        'raw_excerpt': clean((method or intro or exp)[:3500]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--title', required=True)
    ap.add_argument('--pdf-url', required=True)
    ap.add_argument('--summary', default='')
    args = ap.parse_args()

    cache = CACHE / f"{slugify(args.title)}.pdf"
    try:
        pdf_path = download(args.pdf_url, cache)
        data = analyze(pdf_path, args.title, args.summary)
        json.dump(data, sys.stdout, ensure_ascii=False)
    except Exception as e:
        json.dump({'mode': 'abstract', 'error': str(e), 'focus': '通用系统', 'intro_points': [], 'method_points': [], 'experiment_points': [], 'core_take': args.summary[:120], 'flow_steps': [], 'raw_excerpt': ''}, sys.stdout, ensure_ascii=False)


if __name__ == '__main__':
    main()
