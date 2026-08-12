#!/usr/bin/env python3
"""Build a clean Cloudflare Pages deploy directory for レビュー総選挙."""
from __future__ import annotations

from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

ROOT_PUBLIC_FILES = [
    "styles.css",
    "site.js",
    "robots.txt",
    "sitemap.xml",
    "favicon.svg",
    "manifest.webmanifest",
    "_headers",
    "_redirects",
]


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # All root HTML files are public pages. Internal docs/config remain outside dist.
    for page in ROOT.glob("*.html"):
        copy_if_exists(page, DIST / page.name)

    for name in ROOT_PUBLIC_FILES:
        copy_if_exists(ROOT / name, DIST / name)

    copy_if_exists(ROOT / "assets", DIST / "assets")

    # Validate that every published article in the canonical manifest is shipped.
    manifest_path = ROOT / "data" / "content_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        missing = []
        for item in manifest.get("published", []):
            article = item.get("article")
            if article and not (DIST / article).exists():
                missing.append(article)
        if missing:
            raise SystemExit("Missing published article(s) in dist: " + ", ".join(missing))

    if not (DIST / "index.html").exists():
        raise SystemExit("dist/index.html is missing")

    print(f"Cloudflare Pages dist built: {DIST}")
    print(f"HTML pages: {len(list(DIST.glob('*.html')))}")


if __name__ == "__main__":
    main()
