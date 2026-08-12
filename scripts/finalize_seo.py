#!/usr/bin/env python3
"""Finalize canonical/OG/robots/sitemap inside the deploy directory."""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "site.json"
MANIFEST = ROOT / "data" / "content_manifest.json"


def load_base_url() -> str:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return str(data["production_url"]).rstrip("/")


def canonical_url(base: str, filename: str) -> str:
    return base + "/" if filename == "index.html" else f"{base}/{filename}"


def inject_head_meta(html: str, url: str) -> str:
    html = re.sub(r'<link\s+rel=["\']canonical["\'][^>]*>\s*', "", html, flags=re.I)
    html = re.sub(r'<meta\s+property=["\']og:url["\'][^>]*>\s*', "", html, flags=re.I)
    meta = f'<link rel="canonical" href="{url}"><meta property="og:url" content="{url}">'
    if "</head>" not in html:
        raise ValueError("missing </head>")
    return html.replace("</head>", meta + "</head>", 1)


def render_sitemap(base: str, deploy_dir: Path) -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = [""] + [item["article"] for item in manifest.get("published", [])] + [
        "rankings.html", "category.html", "methodology.html", "about.html", "disclosure.html", "privacy.html"
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
    rows = "\n".join(f"  <url><loc>{base}/{path}</loc></url>" if path else f"  <url><loc>{base}/</loc></url>" for path in unique)
    return f'''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'''


def main() -> int:
    deploy_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    base = load_base_url()
    for page in sorted(deploy_dir.glob("*.html")):
        html = page.read_text(encoding="utf-8")
        page.write_text(inject_head_meta(html, canonical_url(base, page.name)), encoding="utf-8")
    (deploy_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n",
        encoding="utf-8",
    )
    (deploy_dir / "sitemap.xml").write_text(render_sitemap(base, deploy_dir), encoding="utf-8")
    print(f"SEO finalized for {base}: {len(list(deploy_dir.glob('*.html')))} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
