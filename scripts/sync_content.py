from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
SITE_CONFIG = ROOT / "config" / "site.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def base_url() -> str:
    cfg = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
    return str(cfg["production_url"]).rstrip("/") + "/"


def item_row(item: dict, status: str = "公開済み") -> str:
    return (
        f'<a class="rank-list-row" href="{item["article"]}"><span class="num">{item["number"]}</span>'
        f'<span class="topic"><b>{item["title"]}</b><br><small>{item["subtitle"]}</small></span>'
        f'<span class="subcat">{item["axes"]}</span><span class="reviews"><span class="status">{status}</span></span>'
        '<span class="readmore">読む →</span></a>'
    )


def render_rankings(data: dict) -> str:
    rows = [item_row(item) for item in data["published"]]
    for item in data.get("next", []):
        rows.append(
            f'<div class="rank-list-row"><span class="num">{item["number"]}</span>'
            f'<span class="topic"><b>{item["title"]}</b><br><small>{item["subtitle"]}</small></span>'
            f'<span class="subcat">{item["axes"]}</span><span class="reviews"><span class="status wait">{item["status"]}</span></span>'
            '<span class="readmore">準備中</span></div>'
        )
    rows_html = "\n".join(rows)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>調査テーマ一覧｜レビュー総選挙</title><meta name="description" content="レビュー総選挙の公開済み・調査中・候補テーマ一覧。"><link rel="stylesheet" href="styles.css"></head><body>
<header class="header"><div class="wrap header-row"><a class="logo" href="index.html"><span class="logo-seal">選</span>レビュー<em>総選挙</em></a><nav class="nav"><a href="index.html">トップ</a><a href="category.html">カテゴリー</a><a href="methodology.html">調査方法</a></nav></div></header>
<section class="section"><div class="wrap"><div class="sec-kicker">RESEARCH INDEX</div><h1 style="font-size:44px;margin-top:5px">調査テーマ一覧</h1><p>公開済み、調査中、次に調べる候補を同じ一覧で管理しています。</p>
<div class="rank-list" style="margin-top:22px"><div class="rank-list-head"><span>No.</span><span>テーマ</span><span>比較軸</span><span>状態</span><span></span></div>
{rows_html}
</div></div></section>
<footer class="footer"><div class="wrap"><a class="logo" href="index.html"><span class="logo-seal">選</span>レビュー<em>総選挙</em></a></div></footer>
<nav class="mobile-nav"><a href="index.html"><span>⌂</span>ホーム</a><a href="rankings.html"><span>◎</span>調査一覧</a><a href="category.html"><span>□</span>カテゴリ</a><a href="methodology.html"><span>i</span>調査方法</a></nav><script src="site.js"></script></body></html>'''


def render_sitemap(data: dict) -> str:
    root = base_url()
    paths = [""] + [item["article"] for item in data["published"]] + [
        "rankings.html", "category.html", "methodology.html", "about.html", "disclosure.html", "privacy.html", "contact.html"
    ]
    urls = "\n".join(f"  <url><loc>{root}{path}</loc></url>" for path in paths)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def render_index(current: str, data: dict) -> str:
    published = data.get("published", [])
    total = len(published)
    counts = {
        "kitchen": sum(1 for x in published if x.get("category") == "kitchen"),
        "cleaning": sum(1 for x in published if x.get("category") == "cleaning"),
        "pet": sum(1 for x in published if x.get("category") == "pet"),
    }
    next_item = (data.get("next") or [{}])[0]
    next_title = next_item.get("title", "次の調査を選定中")
    next_subtitle = next_item.get("subtitle", "候補を自動調査")

    text = current
    text = re.sub(r'(<div class="big">)\d+テーマ(</div>)', rf'\g<1>{total}テーマ\g<2>', text, count=1)
    text = re.sub(r'(<div class="vote-line"><span>キッチン・家事</span><b>)\d+テーマ(</b>)', rf'\g<1>{counts["kitchen"]}テーマ\g<2>', text, count=1)
    text = re.sub(r'(<div class="vote-line"><span>掃除・洗濯</span><b>)\d+テーマ(</b>)', rf'\g<1>{counts["cleaning"]}テーマ\g<2>', text, count=1)
    text = re.sub(r'(<div class="vote-line"><span>生活・ペット</span><b>)\d+テーマ(</b>)', rf'\g<1>{counts["pet"]}テーマ\g<2>', text, count=1)
    text = re.sub(r'(<div class="signal"><small>公開済み</small><strong>)\d+テーマ(</strong>)', rf'\g<1>{total}テーマ\g<2>', text, count=1)
    text = re.sub(r'(<div class="signal"><small>根拠台帳</small><strong>)\d+データセット(</strong>)', rf'\g<1>{total}データセット\g<2>', text, count=1)
    text = re.sub(
        r'<div class="signal"><small>次の調査</small><strong>.*?</strong><em>.*?</em></div>',
        f'<div class="signal"><small>次の調査</small><strong>{next_title}</strong><em>{next_subtitle}</em></div>',
        text,
        count=1,
    )
    text = re.sub(r'(<div class="sec-kicker">RESEARCH LIBRARY</div><h2>)公開済み\d+テーマ(</h2>)', rf'\g<1>公開済み{total}テーマ\g<2>', text, count=1)

    library_rows = "\n".join(item_row(item, status="公開") for item in published)
    pattern = re.compile(
        r'(<section class="section alt" id="library">.*?<div class="rank-list"><div class="rank-list-head"><span>No\.</span><span>テーマ</span><span>主な判断軸</span><span>状態</span><span></span></div>\n)(.*?)(\n</div><p style="margin-top:16px">)',
        re.S,
    )
    text, count = pattern.subn(rf'\g<1>{library_rows}\g<3>', text, count=1)
    if count != 1:
        raise RuntimeError("index.html research library block could not be synchronized")
    return text


def sync(check: bool = False) -> int:
    data = load_manifest()
    index_path = ROOT / "index.html"
    index_current = index_path.read_text(encoding="utf-8")
    outputs = {
        index_path: render_index(index_current, data),
        ROOT / "rankings.html": render_rankings(data),
        ROOT / "sitemap.xml": render_sitemap(data),
    }
    drift = []
    for path, expected in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != expected:
            if check:
                drift.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(expected, encoding="utf-8")
    if drift:
        print("Content synchronization required:")
        for path in drift:
            print(" -", path)
        print("Run: python scripts/sync_content.py")
        return 1
    print("Content synchronization check PASSED" if check else "Content synchronization completed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))
