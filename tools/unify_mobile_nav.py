# -*- coding: utf-8 -*-
"""下部モバイルナビを正本ラベルへ統一する（1回だけ実行）"""
import pathlib, re, sys

CANON_SUB = (
    '<nav class="mobile-nav">'
    '<a href="index.html"><span aria-hidden="true">⌂</span>トップ</a>'
    '<a href="index.html#latest"><span aria-hidden="true">◎</span>新着レビュー</a>'
    '<a href="rankings.html"><span aria-hidden="true">□</span>調査一覧</a>'
    '<a href="methodology.html"><span aria-hidden="true">i</span>調査方法</a>'
    '</nav>'
)
CANON_INDEX = (
    '<nav class="mobile-nav">'
    '<a href="index.html"><span aria-hidden="true">⌂</span>トップ</a>'
    '<a href="index.html#latest"><span aria-hidden="true">◎</span>新着レビュー</a>'
    '<a href="rankings.html"><span aria-hidden="true">□</span>調査一覧</a>'
    '<a href="methodology.html"><span aria-hidden="true">i</span>調査方法</a>'
    '</nav>'
)

root = pathlib.Path(".")
changed = 0
for f in sorted(root.glob("*.html")):
    s = f.read_text(encoding="utf-8")
    if 'class="mobile-nav"' not in s:
        continue
    canon = CANON_INDEX if f.name == "index.html" else CANON_SUB
    new, n = re.subn(r'<nav class="mobile-nav">.*?</nav>', canon, s, count=1)
    if n != 1:
        print(f"FAIL mobile-nav not found: {f.name}")
        sys.exit(1)
    if new != s:
        f.write_text(new, encoding="utf-8")
        changed += 1
        print(f"OK: {f.name}")
    else:
        print(f"NOCHANGE: {f.name}")
print(f"done: {changed} files changed")
