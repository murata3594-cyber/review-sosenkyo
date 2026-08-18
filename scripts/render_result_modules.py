#!/usr/bin/env python3
"""v21 フェーズ2 収益モジュールを dist のビルド後HTMLへ描画する。

このスクリプトが描画するのは3つ。

1. 2-1 結論ボックスの購入導線
   `.verdict` カードの `data-offer`（data/affiliate_catalog.json の label）を
   data/generated/affiliate_links.json の有効オファーへ解決し、Amazon / 楽天の
   2択までのボタンを出す。アフィリエイトIDが未投入なら有効オファーが0件になる
   ので、ボタンは1つも出力されない（build_affiliate_links.py の fail-closed を
   そのまま利用する）。
2. 2-1 判断根拠の可視化
   `.verdict` カードの `data-product`（data/research/*.json の products[].id）から
   review_snapshot の実値だけを `レビュー4.77 / 77件（2026-08-09時点）` として
   ボタン直下に出す。台帳に無い値は作らない。母数・評価・確認日のいずれかが
   欠けている商品には何も出さない。
3. 2-2 モバイル固定CTAバー / 2-3 初期レビュー vs 数か月後チャート
   バーは有効オファーがある記事にだけ挿入し、body へ .has-sticky-cta を付けて
   高さ分の padding-bottom を予約する（CLSゼロ）。表示条件の制御は site.js。
   チャートは review_snapshot_initial / review_snapshot_longterm が両方そろって
   いる商品だけ描画する。データが無い記事には何も出さない。

編集元のHTMLは書き換えない。dist だけを変換する。
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
CATALOG = ROOT / "data" / "affiliate_catalog.json"
AFFILIATE_LINKS = ROOT / "data" / "generated" / "affiliate_links.json"

VERDICT_RE = re.compile(r'<div class="verdict"((?:\s+[a-zA-Z-]+="[^"]*")*)>(.*?)</div>', re.S)
ATTR_RE = re.compile(r'([a-zA-Z-]+)="([^"]*)"')
PROVIDER_LABEL = {"amazon": "Amazonで見る", "rakuten": "楽天で見る"}
PROVIDER_CLASS = {"amazon": "cta-amazon", "rakuten": "cta-rakuten"}
# 外部の購入リンクは sponsored。出典リンク（noopener noreferrer）とは別物。
CTA_REL = "sponsored nofollow noopener"
AD_NOTE = (
    '<p class="verdict-ad-note">購入ボタンは広告（アフィリエイト）リンクです。'
    'リンク経由の購入で当サイトが収益を得ることがありますが、比較の評価と掲載順には影響しません。'
    '<a href="disclosure.html">広告・アフィリエイト方針</a></p>'
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_rating(rating: float) -> str:
    return f"{round(float(rating), 2):g}"


def snapshot_text(snap: object) -> str:
    """台帳の review_snapshot から表示可能な実値だけを文字列にする。"""
    if not isinstance(snap, dict):
        return ""
    rating = snap.get("rating")
    count = snap.get("count")
    checked = str(snap.get("checked_at", "")).strip()
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return ""
    if not isinstance(rating, (int, float)) or isinstance(rating, bool):
        return ""
    if not (0 <= float(rating) <= 5) or not checked:
        return ""
    return f"レビュー{format_rating(rating)} / {count:,}件（{checked}時点）"


def offer_buttons(product: dict | None) -> tuple[str, str]:
    """有効な購入リンクだけを Amazon → 楽天 の順で最大2件返す。"""
    if not product:
        return "", ""
    by_provider = {}
    for offer in product.get("offers", []):
        url = str(offer.get("url", ""))
        if offer.get("active") and url.startswith("https://"):
            by_provider[offer.get("provider")] = url
    buttons = []
    for provider in ("amazon", "rakuten"):
        url = by_provider.get(provider)
        if not url:
            continue
        buttons.append(
            f'<a class="{PROVIDER_CLASS[provider]}" href="{esc(url)}" target="_blank" '
            f'rel="{CTA_REL}">{PROVIDER_LABEL[provider]}</a>'
        )
    if not buttons:
        return "", ""
    return f'<div class="verdict-cta">{"".join(buttons)}</div>', "".join(buttons)


def longterm_section(ledger: dict) -> str:
    items = []
    for product in ledger.get("products", []):
        initial = product.get("review_snapshot_initial")
        longterm = product.get("review_snapshot_longterm")
        if not isinstance(initial, dict) or not isinstance(longterm, dict):
            continue
        rows = []
        values = []
        for snap, modifier, fallback in (
            (initial, "lt-row-initial", "購入直後"),
            (longterm, "lt-row-longterm", "数か月後"),
        ):
            text = snapshot_text(snap)
            if not text:
                rows = []
                break
            rating = float(snap["rating"])
            values.append(rating)
            width = f"{round(rating / 5 * 100, 1):g}"
            label = str(snap.get("window") or fallback)
            rows.append(
                f'<div class="lt-row {modifier}"><span class="lt-label">{esc(label)}</span>'
                f'<span class="lt-track" aria-hidden="true"><span class="lt-fill" style="width:{width}%"></span></span>'
                f'<span class="lt-value">{format_rating(rating)} / {snap["count"]:,}件</span></div>'
            )
        if not rows:
            continue
        delta = values[1] - values[0]
        sign = "+" if delta > 0 else ""
        checked = esc(str(longterm.get("checked_at", "")))
        items.append(
            '<div class="lt-item">'
            f'<div class="lt-name">{esc(product.get("name", ""))}</div>'
            + "".join(rows)
            + f'<p class="lt-delta">初期比 {sign}{delta:.2f}</p>'
            + f'<p class="lt-basis">投稿時期で分けて集計。確認日 {checked}。母数が異なるため平均の差だけで優劣は決めません。</p>'
            "</div>"
        )
    if not items:
        return ""
    return (
        '<section class="sectionbox longterm-section" id="longterm">'
        "<h2>初期レビューと数か月後レビュー</h2>"
        "<p>同じ商品でも、買った直後の評価と数か月使った後の評価は分かれます。"
        "投稿時期でレビューを分けて集計した結果です。</p>"
        f'<div class="longterm-chart">{"".join(items)}</div>'
        "</section>"
    )


def render_page(text: str, ledger: dict, offers: dict, catalog_labels: set[str], article: str) -> str:
    products = {str(p.get("id")): p for p in ledger.get("products", []) if p.get("id")}
    rendered_cta = [False]
    sticky: list[tuple[str, str, dict]] = []

    def replace(match: re.Match[str]) -> str:
        attrs = dict(ATTR_RE.findall(match.group(1)))
        body = match.group(2)
        # 二重描画の保険。dist は毎回作り直すが、単体実行を重ねても増殖させない。
        if "verdict-cta" in body or "verdict-basis" in body or "verdict-official-link" in body:
            return match.group(0)
        product_id = attrs.get("data-product", "")
        offer_label = attrs.get("data-offer", "")
        extra = ""
        basis = ""
        if product_id:
            if product_id not in products:
                raise SystemExit(f"{article}: data-product not found in research ledger -> {product_id}")
            basis = snapshot_text(products[product_id].get("review_snapshot"))
        if offer_label:
            if offer_label not in catalog_labels:
                raise SystemExit(f"{article}: data-offer not found in affiliate catalog -> {offer_label}")
            block, _ = offer_buttons(offers.get(offer_label))
            if block:
                extra += block
                rendered_cta[0] = True
                if not sticky:
                    name = ""
                    name_match = re.search(r"<b>(.*?)</b>", body, re.S)
                    if name_match:
                        name = re.sub(r"<[^>]+>", "", name_match.group(1)).strip()
                    sticky.append((name or offer_label, basis, offers.get(offer_label, {})))
            elif product_id:
                # 購入ボタンが1つも出せない(アフィリエイトID未設定)場合、読者が迷子にならないよう
                # 研究台帳のofficial_source(メーカー公式ページ)への導線だけは必ず残す。捏造リンクは作らない。
                official = str(products[product_id].get("official_source", "")).strip()
                if official.startswith("https://"):
                    extra += (
                        '<div class="verdict-official-link">'
                        f'<a href="{esc(official)}" target="_blank" rel="noopener noreferrer">'
                        "メーカー公式サイトで詳細を見る →</a></div>"
                    )
        if basis:
            extra += f'<small class="verdict-basis">{esc(basis)}</small>'
        return f'<div class="verdict"{match.group(1)}>{body}{extra}</div>'

    text = VERDICT_RE.sub(replace, text)

    if rendered_cta[0]:
        # 広告表記は結論ボックス（.result-hero）の末尾へ1回だけ置く。
        hero = re.search(r'<section class="result-hero"[^>]*>.*?</section>', text, re.S)
        if not hero:
            raise SystemExit(f"{article}: result-hero section not found; cannot place the ad disclosure")
        block = hero.group(0)
        text = text.replace(block, block[: -len("</section>")] + AD_NOTE + "</section>", 1)

    if sticky:
        name, basis, product = sticky[0]
        _, buttons = offer_buttons(product)
        basis_html = f"<small>{esc(basis)}</small>" if basis else ""
        bar = (
            '<div class="sticky-cta sticky-cta-bar" aria-hidden="true">'
            '<div class="sticky-cta-inner">'
            f'<div class="sticky-cta-label"><b>PR / {esc(name)}</b>{basis_html}</div>'
            f'<div class="sticky-cta-buttons">{buttons}</div>'
            "</div></div>"
        )
        if "<body>" not in text:
            raise SystemExit(f"{article}: <body> tag not found; cannot reserve sticky CTA space")
        text = text.replace("<body>", '<body class="has-sticky-cta">', 1)
        text = text.replace("</body>", bar + "</body>", 1)

    chart = "" if 'id="longterm"' in text else longterm_section(ledger)
    if chart:
        marker = '<section class="sectionbox" id="sources">'
        if marker not in text:
            raise SystemExit(f"{article}: sources section not found; cannot place longterm chart")
        text = text.replace(marker, chart + marker, 1)
    return text


def main() -> int:
    deploy = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    manifest = load_json(MANIFEST)
    catalog = load_json(CATALOG).get("articles", {})
    links = load_json(AFFILIATE_LINKS).get("articles", {})

    cta_pages = 0
    basis_count = 0
    chart_pages = 0
    for item in manifest.get("published", []):
        article = str(item.get("article", ""))
        page = deploy / article
        if not article or not page.exists():
            continue
        research = str(item.get("research", ""))
        ledger = load_json(ROOT / research) if research else {}
        catalog_labels = {str(p.get("label")) for p in catalog.get(article, {}).get("products", [])}
        offers = {str(p.get("label")): p for p in links.get(article, {}).get("products", [])}

        before = page.read_text(encoding="utf-8")
        after = render_page(before, ledger, offers, catalog_labels, article)
        if after != before:
            page.write_text(after, encoding="utf-8")
        if 'class="verdict-cta"' in after:
            cta_pages += 1
        if 'class="longterm-chart"' in after:
            chart_pages += 1
        basis_count += after.count('class="verdict-basis"')

    print(
        f"Result modules rendered: purchase CTA on {cta_pages} page(s), "
        f"{basis_count} evidence line(s), long-term chart on {chart_pages} page(s)."
    )
    if cta_pages == 0:
        print("Purchase buttons stay hidden until affiliate IDs are configured (fail-closed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
