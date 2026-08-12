#!/usr/bin/env python3
"""Build the production directory for レビュー総選挙."""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ROOT_PUBLIC_FILES = [
    "styles.css", "site.js", "robots.txt", "sitemap.xml", "favicon.svg",
    "manifest.webmanifest", "_headers", "_redirects",
]


def run(script: str, *args: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], check=True)


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def main() -> None:
    # Deterministic content and editorial QA come first.
    run("sync_content.py")
    run("validate_site.py")
    run("audit_content_quality.py")

    # Resolve affiliate links. With no credentials this safely generates zero active links.
    run("build_affiliate_links.py")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for page in ROOT.glob("*.html"):
        copy_if_exists(page, DIST / page.name)
    for name in ROOT_PUBLIC_FILES:
        copy_if_exists(ROOT / name, DIST / name)
    copy_if_exists(ROOT / "assets", DIST / "assets")

    manifest_path = ROOT / "data" / "content_manifest.json"
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

    # Build-time transformations only affect deploy files, not editorial source HTML.
    run("render_affiliate_blocks.py", str(DIST))
    run("finalize_seo.py", str(DIST))
    run("inject_services.py", str(DIST))

    print(f"Production dist built: {DIST}")
    print(f"HTML pages: {len(list(DIST.glob('*.html')))}")
    print(f"Published articles: {len(manifest.get('published', []))}")


if __name__ == "__main__":
    main()
