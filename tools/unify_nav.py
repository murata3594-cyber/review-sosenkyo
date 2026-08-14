# -*- coding: utf-8 -*-
"""全ページのヘッダーナビを正本ラベルへ統一する（1回だけ実行）"""
import pathlib, re, sys

CANON_SUB = ('<nav class="nav"><a href="index.html">トップ</a>'
             '<a href="index.html#latest">新着レビュー</a>'
             '<a href="rankings.html">調査一覧</a>'
             '<a href="category.html">カテゴリー</a>'
             '<a href="methodology.html">調査方法</a></nav>')

CANON_INDEX = ('<nav class="nav"><a href="#latest">新着レビュー</a>'
               '<a href="rankings.html">調査一覧</a>'
               '<a href="category.html">カテゴリー</a>'
               '<a href="methodology.html">調査方法</a></nav>')

root = pathlib.Path(".")
changed = 0
for f in sorted(root.glob("*.html")):
    if f.name == "404.html":
        print(f"SKIP (no nav): {f.name}")
        continue
    s = f.read_text(encoding="utf-8")
    canon = CANON_INDEX if f.name == "index.html" else CANON_SUB
    new, n = re.subn(r'<nav class="nav">.*?</nav>', canon, s, count=1)
    if n != 1:
        print(f"FAIL nav not found: {f.name}")
        sys.exit(1)
    if new != s:
        f.write_text(new, encoding="utf-8")
        changed += 1
        print(f"OK: {f.name}")
    else:
        print(f"NOCHANGE: {f.name}")
print(f"done: {changed} files changed")
