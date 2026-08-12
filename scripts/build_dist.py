#!/usr/bin/env python3
"""Build a clean Cloudflare/GitHub deploy directory for レビュー総選挙."""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys

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

    for page in ROOT.glob("*.html"):
        copy_if_exists(page, DIST / page.name)

    for name in ROOT_PUBLIC_FILES:
        copy_if_exists(ROOT / name, DIST / name)

    copy_if_exists(ROOT / "assets", DIST / "assets")

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

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "finalize_seo.py"), str(DIST)],
        check=True,
    )

    print(f"Deploy dist built: {DIST}")
    print(f"HTML pages: {len(list(DIST.glob('*.html')))}")


if __name__ == "__main__":
    main()
