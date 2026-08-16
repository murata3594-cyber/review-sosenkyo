#!/usr/bin/env python3
"""Finalize canonical, social metadata, structured data, robots and sitemap.

Source HTML deliberately carries no canonical / OGP / JSON-LD. Everything that
depends on the deployed host is injected here, at build time, so a host change
only needs config/site.json.

Structured data policy (do not relax):
  * No Review / AggregateRating nodes. The ratings shown on the site are
    third-party shop averages; marking them up would breach Google's review
    snippet guidelines.
  * ItemList carries product names (and the official product URL when the
    ledger has one) only. No prices, no scores.
"""
from __future__ import annotations

from pathlib import Path
import html as html_lib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "site.json"
MANIFEST = ROOT / "data" / "content_manifest.json"

# 1-2: #07111d was left over from the abandoned dark corporate direction.
THEME_COLOR = "#fff7f4"
# 1-10: absolute social image. 1400x509 wordmark, verified against assets/.
OG_IMAGE_PATH = "assets/brand-review-sosenkyo-v16.webp"
OG_IMAGE_SIZE = (1400, 509)

_MANIFEST_CACHE: dict | None = None


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_manifest() -> dict:
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is None:
        _MANIFEST_CACHE = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return _MANIFEST_CACHE


def canonical_url(base: str, filename: str) -> str:
    return base + "/" if filename == "index.html" else f"{base}/{filename}"


def absolute(base: str, href: str) -> str:
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("#"):
        return href
    path, _, fragment = href.partition("#")
    url = canonical_url(base, path) if path else base + "/"
    return f"{url}#{fragment}" if fragment else url


def extract(pattern: str, text: str) -> str:
    m = re.search(pattern, text, flags=re.I | re.S)
    return html_lib.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""


def strip_tags(fragment: str) -> str:
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip())


def page_h1(source: str) -> str:
    """1-3: headline must match the visible h1, not the ｜レビュー総選挙 title."""
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", source, flags=re.I | re.S)
    return strip_tags(m.group(1)) if m else ""


def breadcrumb_trail(source: str, base: str) -> list[dict]:
    """1-4: read the visible breadcrumb so markup and page can never disagree."""
    nav = re.search(r'<nav[^>]*class="[^"]*\bbreadcrumb\b[^"]*"[^>]*>(.*?)</nav>', source, flags=re.I | re.S)
    if not nav:
        return []
    trail = []
    for li in re.findall(r"<li\b[^>]*>(.*?)</li>", nav.group(1), flags=re.I | re.S):
        name = strip_tags(li)
        if not name:
            continue
        link = re.search(r'<a\b[^>]*href="([^"]+)"', li, flags=re.I)
        trail.append({"name": name, "url": absolute(base, link.group(1)) if link else None})
    return trail


def article_date(item: dict) -> str:
    """dateModified. Falls back to the ledger research date, then the manifest."""
    research = item.get("research")
    if research:
        path = ROOT / research
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for key in ("checked_at", "checkedAt", "updated_at", "updated", "researched_at"):
                    value = data.get(key)
                    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value):
                        return value[:10]
            except Exception:
                pass
    return str(load_manifest().get("updated_at", "2026-08-12"))[:10]


def published_date(item: dict) -> str:
    """1-3: datePublished is frozen in the manifest. Missing value fails the build."""
    value = item.get("published")
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise SystemExit(
            f"content_manifest.json: '{item.get('article', item.get('id', 'UNKNOWN'))}' "
            f"needs a 'published' date (YYYY-MM-DD); got {value!r}"
        )
    return value


def publisher_node(cfg: dict, base: str) -> dict:
    """1-3: author/publisher is the editorial Organization. Never invent a person."""
    return {
        "@type": "Organization",
        "@id": f"{base}/#organization",
        "name": cfg.get("publisher_name", cfg.get("site_name", "レビュー総選挙")),
        "url": base + "/",
        "logo": {
            "@type": "ImageObject",
            "url": f"{base}/{OG_IMAGE_PATH}",
            "width": OG_IMAGE_SIZE[0],
            "height": OG_IMAGE_SIZE[1],
        },
    }


def website_node(cfg: dict, base: str, description: str = "") -> dict:
    node = {
        "@type": "WebSite",
        "@id": f"{base}/#website",
        "name": cfg.get("site_name", "レビュー総選挙"),
        "url": base + "/",
        "inLanguage": "ja-JP",
        "publisher": {"@id": f"{base}/#organization"},
    }
    if description:
        node["description"] = description
    return node


def breadcrumb_node(trail: list[dict], url: str) -> dict | None:
    if len(trail) < 2:
        return None
    elements = []
    for position, crumb in enumerate(trail, start=1):
        element = {"@type": "ListItem", "position": position, "name": crumb["name"]}
        if crumb["url"]:
            element["item"] = crumb["url"]
        elements.append(element)
    return {"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb", "itemListElement": elements}


def item_list_node(item: dict, url: str) -> dict | None:
    """1-5: names (and official URLs) of the compared products. Nothing else."""
    research = item.get("research")
    if not research:
        return None
    path = ROOT / research
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    elements = []
    for position, product in enumerate(data.get("products", []) or [], start=1):
        name = str(product.get("name", "")).strip()
        if not name:
            continue
        element = {"@type": "ListItem", "position": position, "name": name}
        official = product.get("official_source")
        if isinstance(official, str) and official.startswith(("http://", "https://")):
            element["url"] = official
        elements.append(element)
    if not elements:
        return None
    topic = str(item.get("title", "")).strip()
    return {
        "@type": "ItemList",
        "@id": f"{url}#comparison",
        "name": f"{topic}の比較対象" if topic else "比較対象",
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(elements),
        "itemListElement": elements,
    }


def schema_for(filename: str, source: str, title: str, description: str, url: str, cfg: dict, manifest: dict) -> dict:
    base = str(cfg["production_url"]).rstrip("/")
    org = publisher_node(cfg, base)
    graph: list[dict] = [org]
    trail = breadcrumb_trail(source, base)

    if filename == "index.html":
        site = website_node(cfg, base, description)
        # 1-3: SearchAction points at the rankings filter implemented in 1-8.
        site["potentialAction"] = {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{base}/rankings.html?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        }
        graph.append(site)
        return {"@context": "https://schema.org", "@graph": graph}

    graph.append(website_node(cfg, base))
    item = next((x for x in manifest.get("published", []) if x.get("article") == filename), None)

    if item:
        headline = page_h1(source) or title
        article = {
            "@type": "Article",
            "@id": f"{url}#article",
            "headline": headline,
            "name": headline,
            "description": description,
            "url": url,
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "datePublished": published_date(item),
            "dateModified": article_date(item),
            "inLanguage": "ja-JP",
            "author": {"@id": f"{base}/#organization"},
            "publisher": {"@id": f"{base}/#organization"},
            "isPartOf": {"@id": f"{base}/#website"},
            "image": f"{base}/{OG_IMAGE_PATH}",
        }
        if item.get("title"):
            article["about"] = {"@type": "Thing", "name": item["title"]}
        graph.append(article)
    else:
        graph.append({
            "@type": "WebPage",
            "@id": url,
            "name": page_h1(source) or title,
            "description": description,
            "url": url,
            "inLanguage": "ja-JP",
            "isPartOf": {"@id": f"{base}/#website"},
        })

    crumbs = breadcrumb_node(trail, url)
    if crumbs:
        graph.append(crumbs)
    if item:
        products = item_list_node(item, url)
        if products:
            graph.append(products)
    return {"@context": "https://schema.org", "@graph": graph}


def ensure_shared_assets(source: str) -> str:
    head_bits = []
    if not re.search(r'<link\s+[^>]*rel=["\'](?:icon|shortcut icon)["\']', source, flags=re.I):
        head_bits.append('<link rel="icon" href="favicon.svg" type="image/svg+xml">')
    if not re.search(r'<link\s+[^>]*rel=["\']manifest["\']', source, flags=re.I):
        head_bits.append('<link rel="manifest" href="manifest.webmanifest">')
    if not re.search(r'<meta\s+name=["\']theme-color["\']', source, flags=re.I):
        head_bits.append(f'<meta name="theme-color" content="{THEME_COLOR}">')
    if head_bits and "</head>" in source:
        source = source.replace("</head>", "".join(head_bits) + "</head>", 1)
    if not re.search(r'<script\s+[^>]*src=["\']site\.js(?:\?[^"\']*)?["\']', source, flags=re.I) and "</body>" in source:
        source = source.replace("</body>", '<script src="site.js"></script></body>', 1)
    return source


def inject_head_meta(source: str, filename: str, url: str, cfg: dict, manifest: dict) -> str:
    source = ensure_shared_assets(source)
    base = str(cfg["production_url"]).rstrip("/")
    title = extract(r"<title>(.*?)</title>", source) or cfg.get("site_name", "レビュー総選挙")
    description = extract(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', source)
    patterns = [
        r'<link\s+rel=["\']canonical["\'][^>]*>\s*',
        r'<meta\s+property=["\']og:(?:url|title|description|type|site_name|locale|image(?::\w+)?)["\'][^>]*>\s*',
        r'<meta\s+name=["\']twitter:(?:card|title|description|image)["\'][^>]*>\s*',
        r'<meta\s+name=["\']robots["\'][^>]*>\s*',
        r'<!-- SEO_JSONLD_START -->.*?<!-- SEO_JSONLD_END -->',
    ]
    for pattern in patterns:
        source = re.sub(pattern, "", source, flags=re.I | re.S)
    robots = "index,follow,max-image-preview:large" if cfg.get("indexing_enabled") else "noindex,nofollow"
    og_type = "article" if filename.startswith("article") else "website"
    og_image = f"{base}/{OG_IMAGE_PATH}"
    schema = schema_for(filename, source, title, description, url, cfg, manifest)
    esc = lambda value: html_lib.escape(str(value), quote=True)
    meta = (
        f'<link rel="canonical" href="{esc(url)}">'
        f'<meta name="robots" content="{robots}">'
        f'<meta property="og:site_name" content="{esc(cfg.get("site_name", "レビュー総選挙"))}">'
        f'<meta property="og:locale" content="{esc(cfg.get("locale", "ja_JP"))}">'
        f'<meta property="og:type" content="{og_type}">'
        f'<meta property="og:title" content="{esc(title)}">'
        f'<meta property="og:description" content="{esc(description)}">'
        f'<meta property="og:url" content="{esc(url)}">'
        f'<meta property="og:image" content="{esc(og_image)}">'
        f'<meta property="og:image:width" content="{OG_IMAGE_SIZE[0]}">'
        f'<meta property="og:image:height" content="{OG_IMAGE_SIZE[1]}">'
        f'<meta property="og:image:alt" content="{esc(cfg.get("site_name", "レビュー総選挙"))}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{esc(title)}">'
        f'<meta name="twitter:description" content="{esc(description)}">'
        f'<meta name="twitter:image" content="{esc(og_image)}">'
        '<!-- SEO_JSONLD_START --><script type="application/ld+json">'
        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        + '</script><!-- SEO_JSONLD_END -->'
    )
    if "</head>" not in source:
        raise ValueError(f"{filename}: missing </head>")
    return source.replace("</head>", meta + "</head>", 1)


def render_sitemap(base: str, deploy_dir: Path, manifest: dict) -> str:
    """1-10: every URL gets <lastmod> from the already-parsed ledger dates."""
    site_updated = str(manifest.get("updated_at", ""))[:10]
    published = {item["article"]: item for item in manifest.get("published", []) if item.get("article")}
    paths = [""] + list(published) + [
        "rankings.html", "category.html", "methodology.html", "about.html", "disclosure.html", "privacy.html", "contact.html"
    ]
    unique = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        if path and not (deploy_dir / path).exists():
            continue
        unique.append(path)
    rows = []
    for path in unique:
        loc = f"{base}/{path}" if path else f"{base}/"
        item = published.get(path)
        lastmod = article_date(item) if item else site_updated
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    body = "\n".join(rows)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main() -> int:
    deploy_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    cfg = load_config()
    manifest = load_manifest()
    base = str(cfg["production_url"]).rstrip("/")
    for item in manifest.get("published", []):
        published_date(item)  # fail closed before anything is written
    for page in sorted(deploy_dir.glob("*.html")):
        source = page.read_text(encoding="utf-8")
        page.write_text(inject_head_meta(source, page.name, canonical_url(base, page.name), cfg, manifest), encoding="utf-8")
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n" if cfg.get("indexing_enabled") else "User-agent: *\nDisallow: /\n"
    (deploy_dir / "robots.txt").write_text(robots, encoding="utf-8")
    (deploy_dir / "sitemap.xml").write_text(render_sitemap(base, deploy_dir, manifest), encoding="utf-8")
    print(f"SEO finalized for {base}; indexing={'enabled' if cfg.get('indexing_enabled') else 'disabled'}; pages={len(list(deploy_dir.glob('*.html')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
