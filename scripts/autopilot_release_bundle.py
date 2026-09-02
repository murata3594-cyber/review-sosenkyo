#!/usr/bin/env python3
"""Build an exact, hash-bound release bundle for the unattended review cycle."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
SITE = ROOT / "config" / "site.json"

OPERATIONAL_EXCLUDES = {
    "data/automation_runtime.json",
    "data/run_receipt_index.json",
    "data/autopilot_work_order.json",
}
RELEASE_PATTERNS = (
    "article-*.html",
    "data/research/*.json",
    "data/affiliate_catalog.json",
    "data/content_manifest.json",
    "data/topic_queue.json",
    "assets/images/*",
    "index.html",
    "rankings.html",
    "category.html",
    "sitemap.xml",
    "robots.txt",
)


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if p.returncode:
        raise SystemExit(p.stderr.strip() or p.stdout.strip())
    return p.stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def allowed(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in RELEASE_PATTERNS)


def changed_paths(base_head: str) -> list[str]:
    tracked = {
        x.strip() for x in git("diff", "--name-only", "--diff-filter=ACMRTUXB", base_head, "--").splitlines()
        if x.strip()
    }
    untracked = {
        x.strip() for x in git("ls-files", "--others", "--exclude-standard").splitlines()
        if x.strip()
    }
    result = sorted((tracked | untracked) - OPERATIONAL_EXCLUDES)
    result = [x for x in result if not x.startswith("data/run_receipts/")]
    bad = [x for x in result if not allowed(x)]
    if bad:
        raise SystemExit("release bundle contains non-publishable paths: " + ", ".join(bad))
    return result


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def old_manifest(base_head: str) -> dict:
    try:
        return json.loads(git("show", f"{base_head}:data/content_manifest.json"))
    except Exception:
        return {"published": []}


def pick_primary(base_head: str, paths: list[str]) -> dict:
    now = manifest()
    old = old_manifest(base_head)
    old_ids = {str(a.get("id") or "") for a in old.get("published", []) if isinstance(a, dict)}
    current = [a for a in now.get("published", []) if isinstance(a, dict)]
    fresh = [a for a in current if str(a.get("id") or "") not in old_ids]
    candidates = fresh
    if not candidates:
        changed_articles = {x for x in paths if x.startswith("article-") and x.endswith(".html")}
        candidates = [a for a in current if str(a.get("article") or "") in changed_articles]
    if not candidates:
        raise SystemExit("could not identify the comparison article represented by this release bundle")
    if len(candidates) > 1:
        raise SystemExit("one unattended cycle may publish only one comparison: " + ", ".join(str(a.get("id")) for a in candidates))
    a = candidates[0]
    rel = str(a.get("article") or "").lstrip("/")
    site = json.loads(SITE.read_text(encoding="utf-8"))
    base = str(site.get("production_url") or "").strip().rstrip("/") + "/"
    return {
        "id": str(a.get("id") or ""),
        "slug": Path(rel).stem,
        "title": str(a.get("title") or ""),
        "path": rel,
        "research": str(a.get("research") or ""),
        "url": urljoin(base, rel),
    }


def build(base_head: str, out: Path) -> int:
    paths = changed_paths(base_head)
    if not paths:
        raise SystemExit("no publishable changes in this cycle")
    files = []
    for rel in paths:
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit(f"publishable path missing: {rel}")
        files.append({"path": rel, "sha256": sha256(p), "bytes": p.stat().st_size})
    doc = {
        "schema_version": "1.0.0",
        "repository": "murata3594-cyber/review-sosenkyo",
        "base_head": base_head,
        "primary": pick_primary(base_head, paths),
        "files": files,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-head", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    return build(a.base_head, Path(a.out))


if __name__ == "__main__":
    raise SystemExit(main())
