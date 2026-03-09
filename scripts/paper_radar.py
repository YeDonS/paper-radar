#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}
ROOT = Path(__file__).resolve().parents[1]
PERSONALIZATION = ROOT / 'output' / 'personalization.json'

PROFILE = {
    "name": "jun-sys-arch-storage-aiinfra",
    "categories": ["cs.AR", "cs.DC", "cs.OS", "cs.SY", "cs.AI", "cs.LG", "cs.IR"],
    "positive_keywords": {
        "computer architecture": 8,
        "microarchitecture": 8,
        "memory system": 8,
        "cache": 5,
        "prefetch": 5,
        "tlb": 5,
        "cxl": 9,
        "chiplet": 7,
        "disaggregated": 7,
        "accelerator": 6,
        "gpu cluster": 7,
        "storage": 8,
        "ssd": 8,
        "flash": 7,
        "nvme": 8,
        "io stack": 7,
        "filesystem": 8,
        "file system": 8,
        "key-value store": 7,
        "kv store": 7,
        "lsm": 6,
        "rocksdb": 6,
        "data center": 6,
        "datacenter": 6,
        "distributed system": 7,
        "cloud system": 6,
        "throughput": 5,
        "latency": 5,
        "memory-bound": 6,
        "memory bound": 6,
        "serving": 8,
        "inference": 7,
        "inference system": 9,
        "training system": 8,
        "llm serving": 10,
        "rag system": 6,
        "ai infrastructure": 10,
        "mlsys": 8,
        "vllm": 7,
        "moe": 6,
        "rdma": 7,
        "networked storage": 8,
        "persistent memory": 7,
    },
    "negative_keywords": {
        "medical image": -8,
        "biology": -8,
        "protein": -8,
        "survey": -3,
        "benchmark only": -3,
        "education": -5,
        "social network": -5,
        "vision-language": -4,
        "diffusion": -4,
    },
}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def fetch_entries(categories, max_results):
    query = " OR ".join(f"cat:{c}" for c in categories)
    url = f"{ARXIV_API}?search_query={urllib.parse.quote(query)}&sortBy=submittedDate&sortOrder=descending&start=0&max_results={max_results}"
    req = urllib.request.Request(url, headers={"User-Agent": "paper-radar/0.1 (+https://github.com/openclaw/openclaw)"})
    last_err = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read()
            break
        except Exception as err:
            last_err = err
    else:
        raise last_err
    root = ET.fromstring(xml_data)
    entries = []
    for entry in root.findall("atom:entry", NS):
        title = clean(entry.findtext("atom:title", default="", namespaces=NS))
        summary = clean(entry.findtext("atom:summary", default="", namespaces=NS))
        published = entry.findtext("atom:published", default="", namespaces=NS)
        updated = entry.findtext("atom:updated", default="", namespaces=NS)
        link = ""
        for link_node in entry.findall("atom:link", NS):
            if link_node.attrib.get("rel") == "alternate":
                link = link_node.attrib.get("href", "")
                break
        authors = [clean(a.findtext("atom:name", default="", namespaces=NS)) for a in entry.findall("atom:author", NS)]
        categories = [c.attrib.get("term", "") for c in entry.findall("atom:category", NS)]
        entries.append({
            "title": title,
            "summary": summary,
            "published": published,
            "updated": updated,
            "link": link,
            "authors": authors,
            "categories": categories,
        })
    return entries


def contains_keyword(text: str, kw: str) -> bool:
    kw = kw.strip().lower()
    if re.fullmatch(r"[a-z0-9.+-]+", kw):
        pattern = rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return kw in text


def load_personalization():
    if not PERSONALIZATION.exists():
        return {}
    try:
        data = json.loads(PERSONALIZATION.read_text())
        return data.get('weights', {}) or {}
    except Exception:
        return {}


def score_entry(entry, profile, since_dt, personalization=None):
    text = f"{entry['title']}\n{entry['summary']}".lower()
    score = 0
    reasons = []
    for kw, weight in profile["positive_keywords"].items():
        if contains_keyword(text, kw):
            score += weight
            reasons.append(f"+{weight} {kw}")
    for kw, weight in profile["negative_keywords"].items():
        if contains_keyword(text, kw):
            score += weight
            reasons.append(f"{weight} {kw}")
    for kw, weight in (personalization or {}).items():
        if contains_keyword(text, kw):
            boost = min(4, max(1, int(weight // 2) or 1))
            score += boost
            reasons.append(f"+{boost} zotero:{kw}")
    try:
        published_dt = dt.datetime.fromisoformat(entry["published"].replace("Z", "+00:00"))
    except Exception:
        published_dt = None
    if published_dt and published_dt >= since_dt:
        score += 3
        reasons.append("+3 recent")
    for c in entry["categories"]:
        if c in {"cs.AR", "cs.DC", "cs.OS", "cs.SY"}:
            score += 2
            reasons.append(f"+2 cat:{c}")
    return score, reasons


def format_entry(entry, score, reasons):
    why = ", ".join(reasons[:6]) if reasons else "generic match"
    authors = ", ".join(entry["authors"][:4])
    if len(entry["authors"]) > 4:
        authors += ", ..."
    summary = textwrap.shorten(entry["summary"], width=220, placeholder="...")
    return f"[{score:>2}] {entry['title']}\n  authors: {authors}\n  cats: {', '.join(entry['categories'][:5])}\n  why: {why}\n  summary: {summary}\n  link: {entry['link']}"


def main():
    ap = argparse.ArgumentParser(description="Personalized arXiv paper radar for systems/architecture/storage/AI infra")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-results", type=int, default=120)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    since_dt = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)
    personalization = load_personalization()
    entries = fetch_entries(PROFILE["categories"], args.max_results)
    scored = []
    for entry in entries:
        score, reasons = score_entry(entry, PROFILE, since_dt, personalization)
        if score > 0:
            scored.append({"score": score, "reasons": reasons, "entry": entry})
    scored.sort(key=lambda x: (x["score"], x["entry"]["published"]), reverse=True)
    top = scored[: args.top]

    if args.json:
        json.dump(top, sys.stdout, ensure_ascii=False, indent=2)
        return

    print(f"Paper Radar :: {PROFILE['name']}")
    print(f"Window: last {args.days} days | fetched: {len(entries)} | matched: {len(scored)} | showing: {len(top)}")
    print()
    for idx, item in enumerate(top, 1):
        print(f"#{idx}")
        print(format_entry(item["entry"], item["score"], item["reasons"]))
        print()

if __name__ == "__main__":
    main()
