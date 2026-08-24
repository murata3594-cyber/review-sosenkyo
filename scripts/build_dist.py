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
MANIFEST_PATH = ROOT / "data" / "content_manifest.json"
ASSET_VERSION = "20260824-premium-teaser-v22"
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


def safe_research_path(value: object) -> Path | None:
    """Return a safe public research-ledger path or fail closed."""
    if not isinstance(value, str) or not value:
        return None
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise SystemExit(f"Unsafe research path in manifest: {value}")
    if len(rel.parts) < 3 or rel.parts[0:2] != ("data", "research") or rel.suffix.lower() != ".json":
        raise SystemExit(f"Research path must be data/research/*.json: {value}")
    return rel


def clear_dist() -> None:
    """dist を空にする。ディレクトリ自体は消さない。

    Windows では、そのフォルダを作業ディレクトリにしているプロセスが1つでも
    あると `os.rmdir(dist)` が WinError 32 で失敗する（中身の削除は成功する）。
    ローカルでプレビューサーバやエクスプローラを開いたままにするとビルドが
    丸ごと落ちるため、トップ階層は残して中身だけを作り直す。
    """
    DIST.mkdir(parents=True, exist_ok=True)
    for entry in DIST.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def main() -> None:
    # Deterministic content and editorial QA come first.
    run("sync_content.py")
    run("validate_site.py")
    run("audit_content_quality.py")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    published = manifest.get("published", [])
    expected_articles: set[str] = set()
    research_ledgers: set[Path] = set()

    for item in published:
        article = item.get("article")
        if not isinstance(article, str) or not article:
            raise SystemExit(f"Published manifest entry missing article path: {item.get('id', 'UNKNOWN')}")
        article_path = Path(article)
        if article_path.is_absolute() or ".." in article_path.parts or article_path.suffix.lower() != ".html":
            raise SystemExit(f"Unsafe article path in manifest: {article}")
        expected_articles.add(article_path.as_posix())

        research_path = safe_research_path(item.get("research"))
        if research_path is not None:
            research_ledgers.add(research_path)

    # Resolve affiliate links. With no credentials this safely generates zero active links.
    run("build_affiliate_links.py")

    clear_dist()

    # Public utility pages are copied normally, but article*.html is manifest-gated.
    # This prevents abandoned/draft article files from becoming indexable production pages.
    for page in ROOT.glob("*.html"):
        if page.name.startswith("article"):
            continue
        copy_if_exists(page, DIST / page.name)

    for article in sorted(expected_articles):
        src = ROOT / article
        if not src.exists():
            raise SystemExit(f"Published article source is missing: {article}")
        copy_if_exists(src, DIST / article)

    for name in ROOT_PUBLIC_FILES:
        copy_if_exists(ROOT / name, DIST / name)
    copy_if_exists(ROOT / "assets", DIST / "assets")

    # Publish only the structured evidence ledgers that are explicitly referenced
    # by published manifest entries. Never copy the entire data/ tree.
    for rel in sorted(research_ledgers):
        src = ROOT / rel
        if not src.exists():
            raise SystemExit(f"Published research ledger is missing: {rel.as_posix()}")
        copy_if_exists(src, DIST / rel)

    # Shared assets are cached in production. Version their HTML references so
    # visual releases appear immediately instead of waiting for an old cache.
    for page in DIST.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        text = text.replace('href="styles.css"', f'href="styles.css?v={ASSET_VERSION}"')
        text = text.replace('src="site.js"', f'src="site.js?v={ASSET_VERSION}"')
        page.write_text(text, encoding="utf-8")

    missing_articles = [article for article in sorted(expected_articles) if not (DIST / article).exists()]
    if missing_articles:
        raise SystemExit("Missing published article(s) in dist: " + ", ".join(missing_articles))

    deployed_articles = {
        page.relative_to(DIST).as_posix()
        for page in DIST.rglob("article*.html")
    }
    unexpected_articles = sorted(deployed_articles - expected_articles)
    if unexpected_articles:
        raise SystemExit("Unregistered article(s) leaked into dist: " + ", ".join(unexpected_articles))

    missing_ledgers = [rel.as_posix() for rel in sorted(research_ledgers) if not (DIST / rel).exists()]
    if missing_ledgers:
        raise SystemExit("Missing public research ledger(s) in dist: " + ", ".join(missing_ledgers))

    if not (DIST / "index.html").exists():
        raise SystemExit("dist/index.html is missing")

    # Build-time transformations only affect deploy files, not editorial source HTML.
    run("render_affiliate_blocks.py", str(DIST))
    # v21 / フェーズ2: 結論ボックスの購入導線・根拠表示・固定CTA・長期レビュー比較。
    # アフィリエイトブロックの後に走らせる（同じ affiliate_links.json を読む）。
    run("render_result_modules.py", str(DIST))
    run("finalize_seo.py", str(DIST))
    run("inject_services.py", str(DIST))

    source_orphans = sorted(
        page.name for page in ROOT.glob("article*.html")
        if page.relative_to(ROOT).as_posix() not in expected_articles
    )
    if source_orphans:
        print("Excluded unregistered article source(s): " + ", ".join(source_orphans))

    print(f"Production dist built: {DIST}")
    print(f"HTML pages: {len(list(DIST.rglob('*.html')))}")
    print(f"Published articles: {len(expected_articles)}")
    print(f"Published research ledgers: {len(research_ledgers)}")


if __name__ == "__main__":
    main()
