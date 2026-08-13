#!/usr/bin/env python3
"""Finalize canonical, social metadata, structured data, robots and sitemap."""
from __future__ import annotations

from pathlib import Path
import html as html_lib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "site.json"
MANIFEST = ROOT / "data" / "content_manifest.json"


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def canonical_url(base: str, filename: str) -> str:
    return base + "/" if filename == "index.html" else f"{base}/{filename}"


def extract(pattern: str, text: str) -> str:
    m = re.search(pattern, text, flags=re.I | re.S)
    return html_lib.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""


def article_date(item: dict) -> str:
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


def schema_for(filename: str, title: str, description: str, url: str, cfg: dict, manifest: dict) -> dict:
    publisher = {"@type": "Organization", "name": cfg.get("publisher_name", cfg.get("site_name", "レビュー総選挙"))}
    if filename == "index.html":
        return {"@context":"https://schema.org","@type":"WebSite","name":cfg.get("site_name","レビュー総選挙"),"url":url,"description":description,"inLanguage":"ja-JP","publisher":publisher}
    item = next((x for x in manifest.get("published", []) if x.get("article") == filename), None)
    if item:
        return {"@context":"https://schema.org","@type":"Article","headline":title,"description":description,"url":url,"mainEntityOfPage":url,"dateModified":article_date(item),"inLanguage":"ja-JP","publisher":publisher,"about":item.get("title","")}
    return {"@context":"https://schema.org","@type":"WebPage","name":title,"description":description,"url":url,"inLanguage":"ja-JP","isPartOf":{"@type":"WebSite","name":cfg.get("site_name","レビュー総選挙"),"url":canonical_url(str(cfg["production_url"]).rstrip("/"),"index.html")}}


def ensure_shared_assets(source: str) -> str:
    head_bits = []
    if not re.search(r'<link\s+[^>]*rel=["\'](?:icon|shortcut icon)["\']', source, flags=re.I):
        head_bits.append('<link rel="icon" href="favicon.svg" type="image/svg+xml">')
    if not re.search(r'<meta\s+name=["\']theme-color["\']', source, flags=re.I):
        head_bits.append('<meta name="theme-color" content="#07111d">')
    if head_bits and "</head>" in source:
        source = source.replace("</head>", "".join(head_bits) + "</head>", 1)
    if not re.search(r'<script\s+[^>]*src=["\']site\.js(?:\?[^"\']*)?["\']', source, flags=re.I) and "</body>" in source:
        source = source.replace("</body>", '<script src="site.js"></script></body>', 1)
    return source


def inject_head_meta(source: str, filename: str, url: str, cfg: dict, manifest: dict) -> str:
    source = ensure_shared_assets(source)
    title = extract(r"<title>(.*?)</title>", source) or cfg.get("site_name", "レビュー総選挙")
    description = extract(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', source)
    patterns = [
        r'<link\s+rel=["\']canonical["\'][^>]*>\s*',
        r'<meta\s+property=["\']og:(?:url|title|description|type|site_name)["\'][^>]*>\s*',
        r'<meta\s+name=["\']twitter:(?:card|title|description)["\'][^>]*>\s*',
        r'<meta\s+name=["\']robots["\'][^>]*>\s*',
        r'<!-- SEO_JSONLD_START -->.*?<!-- SEO_JSONLD_END -->',
    ]
    for pattern in patterns:
        source = re.sub(pattern, "", source, flags=re.I | re.S)
    robots = "index,follow,max-image-preview:large" if cfg.get("indexing_enabled") else "noindex,nofollow"
    og_type = "article" if filename.startswith("article") else "website"
    schema = schema_for(filename, title, description, url, cfg, manifest)
    meta = (
        f'<link rel="canonical" href="{html_lib.escape(url, quote=True)}">'
        f'<meta name="robots" content="{robots}">'
        f'<meta property="og:site_name" content="{html_lib.escape(str(cfg.get("site_name", "レビュー総選挙")), quote=True)}">'
        f'<meta property="og:type" content="{og_type}">'
        f'<meta property="og:title" content="{html_lib.escape(title, quote=True)}">'
        f'<meta property="og:description" content="{html_lib.escape(description, quote=True)}">'
        f'<meta property="og:url" content="{html_lib.escape(url, quote=True)}">'
        '<meta name="twitter:card" content="summary">'
        f'<meta name="twitter:title" content="{html_lib.escape(title, quote=True)}">'
        f'<meta name="twitter:description" content="{html_lib.escape(description, quote=True)}">'
        '<!-- SEO_JSONLD_START --><script type="application/ld+json">'
        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        + '</script><!-- SEO_JSONLD_END -->'
    )
    if "</head>" not in source:
        raise ValueError(f"{filename}: missing </head>")
    return source.replace("</head>", meta + "</head>", 1)


def render_sitemap(base: str, deploy_dir: Path, manifest: dict) -> str:
    paths = [""] + [item["article"] for item in manifest.get("published", [])] + ["rankings.html","category.html","methodology.html","about.html","disclosure.html","privacy.html","contact.html"]
    unique=[]; seen=set()
    for path in paths:
        if path in seen: continue
        seen.add(path)
        if path and not (deploy_dir/path).exists(): continue
        unique.append(path)
    rows="\n".join(f"  <url><loc>{base}/{path}</loc></url>" if path else f"  <url><loc>{base}/</loc></url>" for path in unique)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


def main() -> int:
    deploy_dir = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/"dist"
    cfg=load_config(); manifest=load_manifest(); base=str(cfg["production_url"]).rstrip("/")
    for page in sorted(deploy_dir.glob("*.html")):
        source=page.read_text(encoding="utf-8")
        page.write_text(inject_head_meta(source,page.name,canonical_url(base,page.name),cfg,manifest),encoding="utf-8")
    robots=f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n" if cfg.get("indexing_enabled") else "User-agent: *\nDisallow: /\n"
    (deploy_dir/"robots.txt").write_text(robots,encoding="utf-8")
    (deploy_dir/"sitemap.xml").write_text(render_sitemap(base,deploy_dir,manifest),encoding="utf-8")
    print(f"SEO finalized for {base}; indexing={'enabled' if cfg.get('indexing_enabled') else 'disabled'}; pages={len(list(deploy_dir.glob('*.html')))}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
