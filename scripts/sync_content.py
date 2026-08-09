from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
BASE_URL = "https://murata3594-cyber.github.io/review-sosenkyo/"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def render_rankings(data: dict) -> str:
    rows = []
    for item in data["published"]:
        rows.append(
            f'<a class="rank-list-row" href="{item["article"]}"><span class="num">{item["number"]}</span>'
            f'<span class="topic"><b>{item["title"]}</b><br><small>{item["subtitle"]}</small></span>'
            f'<span class="subcat">{item["axes"]}</span><span class="reviews"><span class="status">公開済み</span></span>'
            '<span class="readmore">読む →</span></a>'
        )
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
<nav class="mobile-nav"><a href="index.html"><span>⌂</span>ホーム</a><a href="rankings.html"><span>◎</span>調査一覧</a><a href="category.html"><span>□</span>カテゴリ</a><a href="methodology.html"><span>i</span>調査方法</a></nav><script src="site.js"></script></body></html>'''


def render_sitemap(data: dict) -> str:
    paths = [""] + [item["article"] for item in data["published"]] + [
        "rankings.html",
        "category.html",
        "methodology.html",
        "about.html",
        "disclosure.html",
        "privacy.html",
    ]
    urls = "\n".join(f"  <url><loc>{BASE_URL}{path}</loc></url>" for path in paths)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def sync(check: bool = False) -> int:
    data = load_manifest()
    outputs = {
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
    if check:
        print("Content synchronization check PASSED")
    else:
        print("Content synchronization completed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))
