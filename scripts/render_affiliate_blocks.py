#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated" / "affiliate_links.json"
START = "<!-- AFFILIATE_BLOCK_START -->"
END = "<!-- AFFILIATE_BLOCK_END -->"
AMAZON_DISCLOSURE = "Amazonのアソシエイトとして、レビュー総選挙は適格販売により収入を得ています。"


def strip_block(text: str) -> str:
    return re.sub(re.escape(START) + r".*?" + re.escape(END), "", text, flags=re.S)


def render(article: dict) -> tuple[str, bool]:
    cards = []
    has_amazon = False
    for product in article.get("products", []):
        buttons = []
        for offer in product.get("offers", []):
            if not offer.get("active") or not str(offer.get("url", "")).startswith("https://"):
                continue
            provider = offer.get("provider")
            label = "Amazonで見る" if provider == "amazon" else "楽天市場で見る" if provider == "rakuten" else "販売ページを見る"
            buttons.append(
                f'<a class="affiliate-btn affiliate-{html.escape(str(provider))}" href="{html.escape(str(offer["url"]), quote=True)}" '
                'target="_blank" rel="nofollow sponsored noopener noreferrer">'
                f'{label}</a>'
            )
            has_amazon = has_amazon or provider == "amazon"
        if buttons:
            note = html.escape(str(product.get("note", "")))
            cards.append(
                '<div class="affiliate-product">'
                f'<div><b>{html.escape(str(product.get("label", "")))}</b><small>{note}</small></div>'
                f'<div class="affiliate-buttons">{"".join(buttons)}</div>'
                '</div>'
            )
    if not cards:
        return "", False
    body = (
        START
        + '<section class="sectionbox affiliate-block" id="buy"><div class="affiliate-kicker">PR / AFFILIATE</div>'
        + '<h2>販売ページを確認する</h2><p class="affiliate-note">購入先によって価格・在庫・ポイントは変動します。最新情報はリンク先で確認してください。広告リンクの有無は記事の評価・順位に影響しません。</p>'
        + '<div class="affiliate-assurance" aria-label="広告掲載方針"><span>評価は広告と独立</span><span>掲載先を明示</span><span>価格は遷移先で確認</span></div>'
        + ''.join(cards)
        + '</section>'
        + END
    )
    return body, has_amazon


def inject_before_main_end(text: str, block: str) -> str:
    text = strip_block(text)
    if not block:
        return text
    if "</main>" not in text:
        return text
    return text.replace("</main>", block + "</main>", 1)


def inject_amazon_disclosure(index: Path, enabled: bool) -> None:
    text = index.read_text(encoding="utf-8")
    text = re.sub(r'<!-- AMAZON_DISCLOSURE_START -->.*?<!-- AMAZON_DISCLOSURE_END -->', "", text, flags=re.S)
    if enabled:
        block = (
            '<!-- AMAZON_DISCLOSURE_START -->'
            f'<p class="amazon-disclosure">{AMAZON_DISCLOSURE}</p>'
            '<!-- AMAZON_DISCLOSURE_END -->'
        )
        if "</footer>" in text:
            text = text.replace("</footer>", block + "</footer>", 1)
    index.write_text(text, encoding="utf-8")


def main() -> int:
    deploy = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    if not DATA.exists():
        print("No generated affiliate data; skipping affiliate rendering.")
        return 0
    data = json.loads(DATA.read_text(encoding="utf-8"))
    any_amazon = False
    rendered = 0
    for filename, article in data.get("articles", {}).items():
        page = deploy / filename
        if not page.exists():
            continue
        block, has_amazon = render(article)
        text = page.read_text(encoding="utf-8")
        updated = inject_before_main_end(text, block)
        page.write_text(updated, encoding="utf-8")
        if block:
            rendered += 1
        any_amazon = any_amazon or has_amazon
    index = deploy / "index.html"
    if index.exists():
        inject_amazon_disclosure(index, any_amazon)
    print(f"Affiliate blocks rendered on {rendered} page(s); Amazon disclosure={'on' if any_amazon else 'off'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
