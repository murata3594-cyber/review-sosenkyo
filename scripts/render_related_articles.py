#!/usr/bin/env python3
"""記事末に「あわせて読みたい比較」spotlightを描画する（ビルド時、dist限定）。

2026-08-24 の v22 で導入したホームの `commerce-spotlight`（暗色地・放射グラデ
ーション・グラスカード）と同じ視覚言語を、記事テンプレートの内部導線として
再利用する。リンク先は data/content_manifest.json に既に登録されている公開
記事だけ。新しい商品名・価格・在庫・ランキングは一切作らない
（AGENTS.md / CLAUDE.md の「捏造しない」原則）。

選定ロジック: 同一カテゴリの他記事を manifest 掲載順に最大3件。同一カテゴリ
だけで3件そろわない場合だけ、他カテゴリから manifest 順に補う。

編集元のHTMLは書き換えない。dist だけを変換する（render_affiliate_blocks.py
/ render_result_modules.py と同じ方式）。既存記事内の地の文リンク
（一部記事にある `id="related"` の `.sectionbox`）はそのまま残し、上書き
しない。挿入先はカードのidと衝突しないよう `related-spotlight-title` を使う。
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
START = "<!-- RELATED_SPOTLIGHT_START -->"
END = "<!-- RELATED_SPOTLIGHT_END -->"
FOOTER_MARKER = '<footer class="footer">'
MAX_CARDS = 3

# scripts/sync_content.py の CATEGORY_META と同じ値。カテゴリを追加/変更した
# ときは両方を同じコミットで更新する（値の正本は sync_content.py 側）。
CATEGORY_LABELS = {
    "kitchen": "キッチン・家事",
    "cleaning": "掃除・洗濯・バス",
    "pet": "生活・ペット",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def pick_related(article: str, category: str, items: list[dict]) -> list[dict]:
    same = [it for it in items if it["article"] != article and it["category"] == category]
    other = [it for it in items if it["article"] != article and it["category"] != category]
    return (same + other)[:MAX_CARDS]


def render_section(picks: list[dict]) -> str:
    if not picks:
        return ""
    cards = []
    for it in picks:
        label = CATEGORY_LABELS.get(it["category"], it["category"])
        desc = it.get("subtitle") or it.get("axes") or ""
        cards.append(
            f'<a class="related-card" href="{esc(it["article"])}">'
            f'<span class="related-card__tag">{esc(label)}</span>'
            f'<strong>{esc(it["title"])}</strong>'
            f'<span>{esc(desc)}</span>'
            '<em>比較を読む <b aria-hidden="true">→</b></em>'
            "</a>"
        )
    return (
        START
        + '<section class="related-spotlight" aria-labelledby="related-spotlight-title"><div class="wrap">'
        + '<span class="related-kicker">MORE COMPARISONS</span>'
        + '<h2 id="related-spotlight-title">あわせて読みたい比較</h2>'
        + '<p class="related-lede">同じ悩みで比較しやすいテーマをまとめました。'
        + "価格・在庫・仕様は変わることがあるため、最新情報は各記事のリンク先で確認してください。</p>"
        + f'<div class="related-grid">{"".join(cards)}</div>'
        + "</div></section>"
        + END
    )


def strip_block(text: str) -> str:
    return re.sub(re.escape(START) + r".*?" + re.escape(END), "", text, flags=re.S)


def inject(text: str, block: str, article: str) -> str:
    text = strip_block(text)
    if not block:
        return text
    if FOOTER_MARKER not in text:
        raise SystemExit(f"{article}: {FOOTER_MARKER} not found; cannot place related spotlight")
    return text.replace(FOOTER_MARKER, block + FOOTER_MARKER, 1)


def main() -> int:
    deploy = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    if not MANIFEST.exists():
        print("No content manifest; skipping related-articles rendering.")
        return 0
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    published = manifest.get("published", [])
    items = [
        {
            "article": str(it.get("article", "")),
            "category": str(it.get("category", "")),
            "title": str(it.get("title", "")),
            "subtitle": str(it.get("subtitle", "")),
            "axes": str(it.get("axes", "")),
        }
        for it in published
        if it.get("article")
    ]

    rendered = 0
    for it in items:
        page = deploy / it["article"]
        if not page.exists():
            continue
        picks = pick_related(it["article"], it["category"], items)
        block = render_section(picks)
        before = page.read_text(encoding="utf-8")
        after = inject(before, block, it["article"])
        if after != before:
            page.write_text(after, encoding="utf-8")
        if block:
            rendered += 1

    print(f"Related-articles spotlight rendered on {rendered} page(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
