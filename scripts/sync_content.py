from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
SITE_CONFIG = ROOT / "config" / "site.json"

# Shared markup blocks. Keeping them in one place stops the header/footer of the
# generated pages from drifting away from the hand-written pages.
HEADER = (
    '<header class="header"><div class="wrap header-row">'
    '<a class="logo" href="index.html" aria-label="レビュー総選挙 ホーム">'
    '<img src="assets/brand-review-sosenkyo-v16.webp" alt="レビュー総選挙" width="1400" height="509" decoding="async" loading="eager"></a>'
    '<nav class="nav"><a href="index.html">トップ</a><a href="index.html#latest">新着レビュー</a>'
    '<a href="rankings.html">調査一覧</a><a href="category.html">カテゴリー</a>'
    '<a href="methodology.html">調査方法</a></nav></div></header>'
)

# 1-6: the trust links used to be injected by site.js at runtime. ASP reviewers
# (A8 / Amazon Associates / Moshimo) check for them in the served HTML, so every
# page now ships them statically.
FOOTER = (
    '<footer class="footer"><div class="wrap footer-grid">'
    '<div><a class="logo" href="index.html" aria-label="レビュー総選挙 ホーム">'
    '<img src="assets/brand-review-sosenkyo-v16.webp" alt="レビュー総選挙" width="1400" height="509" loading="lazy" decoding="async"></a>'
    '<p>口コミを読む負担を減らし、選ぶための根拠を整理する。</p></div>'
    '<div><strong>CONTENTS</strong><a href="rankings.html">調査一覧</a><a href="category.html">カテゴリー</a><a href="about.html">このサイトについて</a></div>'
    '<div><strong>POLICY</strong><a href="methodology.html">調査方法</a><a href="disclosure.html">広告・アフィリエイト方針</a><a href="privacy.html">プライバシーポリシー</a></div>'
    '</div><div class="wrap"><nav class="legal-links" aria-label="サイト情報">'
    '<a href="about.html">運営者情報</a><a href="methodology.html">調査方法</a>'
    '<a href="disclosure.html">広告・アフィリエイト方針</a><a href="privacy.html">プライバシーポリシー</a>'
    '<a href="contact.html">お問い合わせ</a></nav></div></footer>'
)

MOBILE_NAV = (
    '<nav class="mobile-nav"><a href="index.html"><span aria-hidden="true">⌂</span>トップ</a>'
    '<a href="index.html#latest"><span aria-hidden="true">◎</span>新着レビュー</a>'
    '<a href="rankings.html"><span aria-hidden="true">□</span>調査一覧</a>'
    '<a href="methodology.html"><span aria-hidden="true">i</span>調査方法</a></nav>'
)

CATEGORY_META = {
    "kitchen": {"label": "キッチン・家事", "icon": "🍽️", "image": "assets/detergent.svg",
                "lead": "食洗機洗剤・浄水カートリッジ・スポンジ・保存用品など、毎日使う消耗品を比較します。"},
    "cleaning": {"label": "掃除・洗濯・バス", "icon": "🧺", "image": "assets/washer.svg",
                 "lead": "洗濯槽クリーナー、浴室洗剤、フロアシート、ハンディモップなどの掃除用品を比較します。"},
    "pet": {"label": "生活・ペット", "icon": "🐈", "image": "assets/catlitter.svg",
            "lead": "猫砂、システムトイレ用シート、ペットシーツなど、交換頻度と吸収性能で選ぶ商品を比較します。"},
}
CATEGORY_ORDER = ["kitchen", "cleaning", "pet"]


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_config() -> dict:
    return json.loads(SITE_CONFIG.read_text(encoding="utf-8"))


def base_url() -> str:
    return str(load_config()["production_url"]).rstrip("/") + "/"


def item_row(item: dict, status: str = "公開済み") -> str:
    return (
        f'<a class="rank-list-row" href="{item["article"]}"><span class="num">{item["number"]}</span>'
        f'<span class="topic"><b>{item["title"]}</b><br><small>{item["subtitle"]}</small></span>'
        f'<span class="subcat">{item["axes"]}</span><span class="reviews"><span class="status">{status}</span></span>'
        '<span class="readmore">読む →</span></a>'
    )


def search_key(item: dict, status: str) -> str:
    """Plain-text haystack used by the dependency-free rankings filter."""
    parts = [item.get("title", ""), item.get("subtitle", ""), item.get("axes", ""),
             item.get("number", ""), status, CATEGORY_META.get(item.get("category", ""), {}).get("label", "")]
    return " ".join(str(p) for p in parts if p).replace('"', "")


# 1-8: rankings.html accepts ?q= and filters client side. No library, no build
# step, and the full list still renders when JavaScript is unavailable.
RANKINGS_FILTER_SCRIPT = """<script>
(function(){
  var form=document.getElementById('rank-search-form');
  var input=document.getElementById('rank-search');
  var status=document.getElementById('rank-search-status');
  if(!form||!input||!status)return;
  var rows=[].slice.call(document.querySelectorAll('[data-search]'));
  function normalize(value){
    return String(value||'').toLowerCase().replace(/[\\u3000\\s]+/g,'');
  }
  function apply(query){
    var needle=normalize(query);
    var shown=0;
    rows.forEach(function(row){
      var hit=!needle||normalize(row.getAttribute('data-search')).indexOf(needle)!==-1;
      row.style.display=hit?'':'none';
      if(hit)shown++;
    });
    if(!needle){status.textContent='';return;}
    status.textContent=shown?('「'+query+'」に一致するテーマ '+shown+'件'):('「'+query+'」に一致するテーマはありません。キーワードを短くしてお試しください。');
  }
  var initial=new URLSearchParams(window.location.search).get('q')||'';
  if(initial){input.value=initial;}
  apply(initial);
  input.addEventListener('input',function(){apply(input.value);});
  form.addEventListener('submit',function(event){
    event.preventDefault();
    apply(input.value);
    var url=input.value?('rankings.html?q='+encodeURIComponent(input.value)):'rankings.html';
    if(window.history&&window.history.replaceState){window.history.replaceState(null,'',url);}
  });
})();
</script>"""


def render_rankings(data: dict) -> str:
    rows = []
    for item in data["published"]:
        rows.append(item_row(item).replace(
            '<a class="rank-list-row"',
            f'<a class="rank-list-row" data-search="{search_key(item, "公開済み")}"', 1))
    for item in data.get("next", []):
        rows.append(
            f'<div class="rank-list-row" data-search="{search_key(item, item["status"])}"><span class="num">{item["number"]}</span>'
            f'<span class="topic"><b>{item["title"]}</b><br><small>{item["subtitle"]}</small></span>'
            f'<span class="subcat">{item["axes"]}</span><span class="reviews"><span class="status wait">{item["status"]}</span></span>'
            '<span class="readmore">準備中</span></div>'
        )
    rows_html = "\n".join(rows)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>調査テーマ一覧｜レビュー総選挙</title><meta name="description" content="レビュー総選挙が公開した比較記事と、調査中・候補のテーマをまとめた一覧です。キーワード検索で気になる日用品の比較をすぐに探せます。"><link rel="stylesheet" href="styles.css"></head><body>
{HEADER}
<section class="section"><div class="wrap"><nav class="breadcrumb" aria-label="パンくずリスト"><ol><li><a href="index.html">トップ</a></li><li><span aria-current="page">調査一覧</span></li></ol></nav><div class="sec-kicker">RESEARCH INDEX</div><h1 class="page-head-title" style="margin-top:5px">調査テーマ一覧</h1><p>公開済み、調査中、次に調べる候補を同じ一覧で管理しています。</p>
<form class="search-box" id="rank-search-form" role="search" action="rankings.html" method="get" style="margin-top:18px"><input type="search" id="rank-search" name="q" aria-label="調査テーマを検索" placeholder="例：ペットシーツ、浴室洗剤、スポンジ"><button type="submit">絞り込む</button></form>
<p id="rank-search-status" role="status" aria-live="polite" style="margin:10px 0 0;color:var(--muted);font-size:var(--fs-small)"></p>
<div class="rank-list" style="margin-top:22px"><div class="rank-list-head"><span>No.</span><span>テーマ</span><span>比較軸</span><span>状態</span><span></span></div>
{rows_html}
</div></div></section>
{FOOTER}
{MOBILE_NAV}<script src="site.js"></script>{RANKINGS_FILTER_SCRIPT}</body></html>'''


def render_category(data: dict) -> str:
    """1-7: category.html is generated from the manifest so its status labels can
    never claim '調査中' for an article that is already published."""
    published = data.get("published", [])
    nexts = data.get("next", [])

    cards = []
    for key in CATEGORY_ORDER:
        meta = CATEGORY_META[key]
        count = sum(1 for x in published if x.get("category") == key)
        cards.append(
            f'<a class="cat" href="#{key}"><img src="{meta["image"]}" alt="{meta["label"]}の比較イメージ" width="640" height="420" loading="lazy" decoding="async">'
            f'<div class="cat-copy"><b>{meta["label"]}</b><br><span>公開済み{count}テーマ</span></div></a>'
        )
    cards_html = "".join(cards)

    sections = []
    for key in CATEGORY_ORDER:
        meta = CATEGORY_META[key]
        items = [x for x in published if x.get("category") == key]
        tiles = "".join(
            f'<a class="quick" href="{item["article"]}"><div class="icon">{meta["icon"]}</div>'
            f'<b>{item["title"]}</b><small>公開済み</small></a>'
            for item in items
        )
        sections.append(
            f'<div class="sectionbox" id="{key}"><h2>{meta["label"]}（公開済み{len(items)}テーマ）</h2>'
            f'<p>{meta["lead"]}</p><div class="quick-grid" style="margin-top:14px">{tiles}</div></div>'
        )

    next_tiles = "".join(
        f'<a class="quick" href="rankings.html"><div class="icon">{CATEGORY_META.get(item.get("category", ""), {}).get("icon", "🔎")}</div>'
        f'<b>{item["title"]}</b><small>{item["status"]}</small></a>'
        for item in nexts
    )
    next_section = (
        f'<div class="sectionbox" id="upcoming"><h2>これから調査するテーマ</h2>'
        f'<p>調査中・再調査待ちのテーマです。公開時期はメーカーのリニューアル時期に合わせています。</p>'
        f'<div class="quick-grid" style="margin-top:14px">{next_tiles}</div></div>'
    ) if next_tiles else ""

    sections_html = "\n".join(sections)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>カテゴリー｜レビュー総選挙</title><meta name="description" content="レビュー総選挙の調査カテゴリー一覧。キッチン・家事、掃除・洗濯・バス、生活・ペット用品の公開済み比較記事を、分野ごとにまとめています。"><link rel="stylesheet" href="styles.css"></head><body>
{HEADER}
<section class="section"><div class="wrap"><nav class="breadcrumb" aria-label="パンくずリスト"><ol><li><a href="index.html">トップ</a></li><li><span aria-current="page">カテゴリー</span></li></ol></nav><div class="sec-kicker">CATEGORY</div><h1 class="page-head-title" style="margin-top:5px">カテゴリーから探す</h1><p>レビューが蓄積しやすく、購入前に比較の意味がある生活用品から優先して調査します。一覧はマニフェストから自動同期しているため、表示している状態は実際の公開状況と一致します。</p>
<div class="categories" style="margin-top:22px">{cards_html}</div>
{sections_html}
{next_section}
<div class="sectionbox"><h2>初期段階では扱わない領域</h2><p>医薬品・健康食品・金融商品など、購入判断に専門的な安全性評価や法的配慮が大きく関わる領域は初期対象から外します。まずは使用感を比較しやすい生活消耗品へ集中します。</p></div>
</div></section>
{FOOTER}
{MOBILE_NAV}<script src="site.js"></script></body></html>'''


def article_dates(data: dict) -> dict[str, str]:
    return {item["article"]: str(item.get("published", data.get("updated_at", "")))[:10]
            for item in data.get("published", [])}


def render_sitemap(data: dict) -> str:
    """1-10: every entry carries <lastmod> so crawlers can skip unchanged pages."""
    root = base_url()
    site_updated = str(data.get("updated_at", ""))[:10]
    dates = article_dates(data)
    paths = [""] + [item["article"] for item in data["published"]] + [
        "rankings.html", "category.html", "methodology.html", "about.html", "disclosure.html", "privacy.html", "contact.html"
    ]
    rows = []
    for path in paths:
        lastmod = dates.get(path, site_updated)
        rows.append(f"  <url><loc>{root}{path}</loc><lastmod>{lastmod}</lastmod></url>")
    urls = "\n".join(rows)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
'''


def render_robots() -> str:
    """1-10: the committed robots.txt used to advertise a github.io sitemap while
    sitemap.xml pointed at the workers.dev host, and it allowed indexing while
    config/site.json had indexing_enabled=false. Both now derive from the config,
    exactly like the copy finalize_seo.py writes into dist/."""
    cfg = load_config()
    base = str(cfg["production_url"]).rstrip("/")
    if cfg.get("indexing_enabled"):
        return f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n"
    return "User-agent: *\nDisallow: /\n"


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
        ROOT / "category.html": render_category(data),
        ROOT / "sitemap.xml": render_sitemap(data),
        ROOT / "robots.txt": render_robots(),
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
