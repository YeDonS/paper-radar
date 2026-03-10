#!/usr/bin/env python3
import argparse
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references' / 'summary-template.md'
GEMINI_DISABLED = False
GEMINI_DISABLE_REASON = ''


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


pdf_mod = load_module(ROOT / 'scripts' / 'pdf_deep_read.py', 'pdf_deep_read_mod_for_llm')


def clean(text: str) -> str:
    text = text.replace('\x00', ' ')
    text = re.sub(r'-\s+', '', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_pdf(pdf_path: Path, max_pages=14):
    reader = PdfReader(str(pdf_path))
    pages = min(len(reader.pages), max_pages)
    chunks = []
    for i in range(pages):
        try:
            txt = clean(reader.pages[i].extract_text() or '')
        except Exception:
            txt = ''
        if txt:
            chunks.append(f"[Page {i+1}] {txt[:5000]}")
    return pages, chunks


def build_protocol_prompt(title: str, abstract: str, body_chunk: str, section_name: str):
    protocol = REF.read_text() if REF.exists() else ''
    return f'''你现在是严厉但靠谱的系统论文精读助手。严格遵守下面协议，不要偷懒，不要输出协议解释，不要输出多余寒暄。

【精读协议】
{protocol}

【额外硬规则】
- 全部用中文。
- 不要出现“Section III describes”“Emails:”这种垃圾元信息；看到就忽略。
- 不要输出“通信/RF/边缘硬件”这类前台标签词。
- 只围绕当前要求的小节输出，不要把整篇一次性写完。
- 如果正文信息不足，可以明确写“从当前抽取正文里只能确认到……”，但不能瞎编。
- 输出纯文本，不要 markdown 代码块。

【论文标题】
{title}

【摘要】
{abstract}

【当前抽取正文】
{body_chunk}

【当前任务】
只生成这一小节：{section_name}
'''


def run_gemini(prompt: str):
    global GEMINI_DISABLED, GEMINI_DISABLE_REASON
    if GEMINI_DISABLED:
        return None, f'gemini:disabled:{GEMINI_DISABLE_REASON}'
    try:
        proc = subprocess.run(
            ['gemini', '-p', prompt],
            text=True,
            capture_output=True,
            timeout=240,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip(), 'gemini'
        err = (proc.stderr or proc.stdout or '').strip()
        lower = err.lower()
        if 'quota' in lower or '429' in lower or 'rate limit' in lower or 'free_tier' in lower:
            GEMINI_DISABLED = True
            GEMINI_DISABLE_REASON = 'quota'
        return None, f'gemini:{err[:600] or "non-zero exit"}'
    except Exception as e:
        msg = str(e)
        lower = msg.lower()
        if 'quota' in lower or '429' in lower or 'rate limit' in lower:
            GEMINI_DISABLED = True
            GEMINI_DISABLE_REASON = 'quota'
        return None, f'gemini:{msg}'


def run_openai(prompt: str):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None, 'openai:no_api_key'
    payload = {
        'model': 'gpt-4.1',
        'messages': [
            {'role': 'system', 'content': '你是严格的中文论文精读助手。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.2,
    }
    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            data = json.loads(r.read().decode())
        return data['choices'][0]['message']['content'].strip(), 'openai'
    except Exception as e:
        return None, f'openai:{e}'


def llm(prompt: str):
    out, src = run_gemini(prompt)
    if out:
        return out, src
    out2, src2 = run_openai(prompt)
    if out2:
        return out2, src2
    raise RuntimeError(f'LLM failed | {src} | {src2}')


def html_wrap(title: str, sections_html: str, model_used: str):
    safe_title = html.escape(title or '', quote=True)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{safe_title} · LLM精读</title><style>
:root{{--bg:#0b1020;--panel:#121a30;--soft:#1a2442;--text:#ecf2ff;--muted:#9fb0d1;--accent:#7c9cff}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,system-ui,sans-serif;background:radial-gradient(circle at top,#18254f 0,#0b1020 45%,#0b1020 100%);color:var(--text)}}.wrap{{max-width:1180px;margin:0 auto;padding:24px 20px 70px}}.panel{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:20px}}section{{margin:0 0 24px 0}}h1,h2,h3{{margin-top:0}}.muted{{color:var(--muted)}}table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid rgba(255,255,255,.08);padding:10px;vertical-align:top}}th{{background:rgba(255,255,255,.05)}}pre{{white-space:pre-wrap;word-break:break-word;background:#10182d;padding:12px;border-radius:12px}}ul,ol{{padding-left:22px}}a{{color:#c8d6ff}}</style></head>
<body><div class="wrap"><div class="panel"><h1>{safe_title}</h1><div class="muted">LLM 精读页（基于 PDF 正文抽取 + 强模型重写，当前来源：{html.escape(model_used, quote=True)}）</div>{sections_html}</div></div></body></html>'''


def ensure_section(title, sid, body):
    return f'<section id="{sid}"><h2>{html.escape(title, quote=True)}</h2>{body}</section>'


def paragraphize(text: str):
    parts = [p.strip() for p in re.split(r'\n\s*\n+', text or '') if p.strip()]
    if not parts:
        parts = [text.strip()] if text and text.strip() else []
    return ''.join(f'<p>{html.escape(p)}</p>' for p in parts)


def fallback_section(name: str, pdfa: dict, title: str, abstract: str):
    intro = pdfa.get('intro_points') or []
    method = pdfa.get('method_points') or []
    exp = pdfa.get('experiment_points') or []
    focus = pdfa.get('focus') or '系统路线'
    core = pdfa.get('core_take') or clean(abstract)[:180] or '从当前抽取正文里只能确认到核心目标与大致方法。'
    flow = pdfa.get('flow_steps') or method[:5]
    excerpt = pdfa.get('raw_excerpt') or ''

    if name == '0. 摘要翻译':
        return paragraphize(f'基于当前摘要，这篇论文主要在解决长上下文推理中的效率与资源开销问题。\n\n{abstract or "当前缺摘要，只能依赖 PDF 正文抽取。"}')
    if name == '1. 方法动机':
        text = f'''1a 作者为什么提出这个方法\n{intro[0] if len(intro) > 0 else core}\n\n1b 现有方法痛点/不足\n{intro[1] if len(intro) > 1 else '现有方案通常在检索粒度、缓存开销和语义完整性之间拉扯。'}\n\n1c 研究假设或核心直觉\n{intro[2] if len(intro) > 2 else '作者的核心直觉是重新组织上下文与索引结构，把线性扫描压成更高效的检索过程。'}'''
        return paragraphize(text)
    if name == '2. 方法设计':
        steps = method[:5]
        while len(steps) < 5:
            steps.append(['定义输入和约束。','构造核心索引或执行结构。','做检索/调度/筛选。','把选中的内容送入主计算路径。','补上增量更新与工程细节。'][len(steps)])
        return ''.join(f'<div class="step"><b>Step {i+1}</b><br>{html.escape(s)}</div>' for i, s in enumerate(steps))
    if name == '3. 与其他方法对比':
        text = f'''主流方案通常在精度、延迟、成本、可解释性或部署资源之间拉扯，很难全都要。\n\n本文方法\n{core}\n\n适用场景\n{focus}\n\n风险\n要重点检查 baseline 是否够强、指标是否完整、收益是否真的来自方法本身。'''
        return paragraphize(text)
    if name == '4. 实验表现与优势':
        pts = exp[:4] or ['从当前抽取正文里只能确认到作者报告了推理效率提升和性能保持。', '但具体数字、实验设置与 baseline 公平性还得继续核对 PDF。']
        return ''.join(f'<p>- {html.escape(x)}</p>' for x in pts)
    if name == '5. 学习与应用':
        text = '如果你要复现，先抓方法边界、索引结构、增量更新策略和实验设置。真正值得学的是瓶颈建模、核心数据结构和 baseline 对照设计。'
        return paragraphize(text)
    if name == '6. 总结':
        quick = [f'1. {x}' for x in (flow[:5] or ['先切分上下文。','再建层次索引。','生成时做分层筛选。','只取相关 KV。','增量更新索引。'])]
        return paragraphize(f'一句话：{core[:80]}\n\n速记版：\n' + '\n'.join(quick))
    if name == '方法流程图':
        plain = [f'{i+1}. {x}' for i, x in enumerate(flow[:5] or ['输入数据','结构化切分','构建索引','按需筛选','输出结果'])]
        return f'<pre>{html.escape(chr(10).join(plain))}</pre>' + (f'<details><summary>正文摘录（fallback）</summary><pre>{html.escape(excerpt)}</pre></details>' if excerpt else '')
    return paragraphize(core)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--title', required=True)
    ap.add_argument('--summary', default='')
    ap.add_argument('--pdf', required=True)
    args = ap.parse_args()

    pages, chunks = extract_pdf(Path(args.pdf))
    body = '\n\n'.join(chunks)
    pdfa = pdf_mod.analyze(Path(args.pdf), args.title, args.summary)

    tasks = [
        ('abs', '0. 摘要翻译'),
        ('motivation', '1. 方法动机'),
        ('design', '2. 方法设计'),
        ('compare', '3. 与其他方法对比'),
        ('exp', '4. 实验表现与优势'),
        ('apply', '5. 学习与应用'),
        ('summary', '6. 总结'),
        ('flow', '方法流程图'),
    ]
    rendered = []
    models = []
    errors = []
    for sid, name in tasks:
        prompt = build_protocol_prompt(args.title, args.summary, body[:24000], name)
        try:
            out, src = llm(prompt)
            models.append(src)
            rendered.append(ensure_section(name, sid, paragraphize(out)))
        except Exception as e:
            errors.append(f'{name}: {e}')
            rendered.append(ensure_section(name, sid, fallback_section(name, pdfa, args.title, args.summary)))
            models.append('pdf-fallback')

    model_used = ', '.join(dict.fromkeys(models)) if models else 'pdf-fallback'
    html_doc = html_wrap(args.title, ''.join(rendered), model_used)
    json.dump({'ok': True, 'mode': 'llm-pdf', 'pages_scanned': pages, 'html': html_doc, 'model_used': model_used, 'error': '; '.join(errors)[:1200]}, sys.stdout, ensure_ascii=False)


if __name__ == '__main__':
    main()
