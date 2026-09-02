#!/usr/bin/env python3
"""Verify that a published レビュー総選挙 article is actually alive on production.

The audit found that every medium could prove a gate had run, but none could
prove the published result still existed and rendered. A publish is therefore
not treated as complete until this check passes and the corresponding ACR
receipt is updated from PENDING to PASS.

Checks, all fail-closed:
  1. the article URL returns 200
  2. the response carries a canonical link that points at the same URL
  3. the hero/og:image referenced by the page is itself reachable
  4. the article appears in the production sitemap

Exit codes: 0 verified, 2 verification failed, 3 nothing to verify.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_DIR = ROOT / "data" / "run_receipts"
RECEIPT_INDEX = ROOT / "data" / "run_receipt_index.json"
SITE_CONFIG = ROOT / "config" / "site.json"

USER_AGENT = "military-now-post-publish-verify/1.0 (+https://github.com/murata3594-cyber/review-sosenkyo)"
TIMEOUT = 20

CANONICAL_RE = re.compile(
    r"""<link[^>]+rel=["']canonical["'][^>]*href=["']([^"']+)["']""", re.I)
CANONICAL_RE_ALT = re.compile(
    r"""<link[^>]+href=["']([^"']+)["'][^>]*rel=["']canonical["']""", re.I)
OG_IMAGE_RE = re.compile(
    r"""<meta[^>]+property=["']og:image["'][^>]*content=["']([^"']+)["']""", re.I)
OG_IMAGE_RE_ALT = re.compile(
    r"""<meta[^>]+content=["']([^"']+)["'][^>]*property=["']og:image["']""", re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url: str, method: str = "GET", retries: int = 2):
    """Return (status, body_text_or_None, error_or_None)."""
    ctx = ssl.create_default_context()
    last_error = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
                body = None
                if method == "GET":
                    raw = resp.read(2_000_000)
                    body = raw.decode(resp.headers.get_content_charset() or "utf-8", "replace")
                return resp.status, body, None
        except urllib.error.HTTPError as exc:
            return exc.code, None, f"http_error:{exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError, ssl.SSLError) as exc:
            last_error = f"network_error:{type(exc).__name__}:{exc}"
    return None, None, last_error


def first_match(patterns, text):
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


def production_url() -> str:
    """This repo keeps the production URL in config/site.json, not a bare text file."""
    if SITE_CONFIG.exists():
        try:
            return str(json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
                       .get("production_url", "")).strip()
        except json.JSONDecodeError:
            return ""
    return ""


def load_receipt(slug: str | None):
    if not RECEIPT_INDEX.exists():
        return None, None
    index = json.loads(RECEIPT_INDEX.read_text(encoding="utf-8"))
    entries = index.get("receipts", [])
    if slug:
        entries = [e for e in entries if e.get("slug") == slug]
    if not entries:
        return None, index
    entry = entries[-1]
    path = RECEIPT_DIR / f"{entry['receipt_id']}.json"
    if not path.exists():
        return None, index
    return (path, json.loads(path.read_text(encoding="utf-8"))), index


def verify(url: str, checks: list) -> list:
    status, body, error = fetch(url)
    if status != 200 or not body:
        checks.append({"check": "article_http_200", "status": "FAIL",
                       "detail": error or f"status={status}"})
        return checks
    checks.append({"check": "article_http_200", "status": "PASS", "detail": url})

    canonical = first_match((CANONICAL_RE, CANONICAL_RE_ALT), body)
    if not canonical:
        checks.append({"check": "canonical_present", "status": "FAIL",
                       "detail": "no rel=canonical link in the published page"})
    else:
        normalized = urljoin(url, canonical)
        same = urlparse(normalized).path.rstrip("/") == urlparse(url).path.rstrip("/")
        checks.append({"check": "canonical_present",
                       "status": "PASS" if same else "FAIL",
                       "detail": normalized})

    image = first_match((OG_IMAGE_RE, OG_IMAGE_RE_ALT), body)
    if not image:
        checks.append({"check": "og_image_present", "status": "FAIL",
                       "detail": "no og:image on the published page"})
    else:
        image_url = urljoin(url, image)
        img_status, _, img_error = fetch(image_url, method="HEAD")
        if img_status is None or img_status >= 400:
            # some object stores reject HEAD; fall back to a ranged GET
            img_status, _, img_error = fetch(image_url, method="GET", retries=1)
        checks.append({"check": "og_image_reachable",
                       "status": "PASS" if img_status == 200 else "FAIL",
                       "detail": f"{image_url} -> {img_status or img_error}"})

    site = production_url()
    if site:
        sitemap = urljoin(site if site.endswith("/") else site + "/", "sitemap.xml")
        sm_status, sm_body, sm_error = fetch(sitemap)
        if sm_status == 200 and sm_body:
            path = urlparse(url).path
            present = path in sm_body or url in sm_body
            checks.append({"check": "listed_in_sitemap",
                           "status": "PASS" if present else "FAIL",
                           "detail": f"{sitemap} contains {path}: {present}"})
        else:
            checks.append({"check": "listed_in_sitemap", "status": "FAIL",
                           "detail": sm_error or f"sitemap status={sm_status}"})
    else:
        checks.append({"check": "listed_in_sitemap", "status": "FAIL",
                       "detail": "config/site.json has no production_url"})
    return checks


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Verify a published article is live")
    p.add_argument("--url", help="verify this URL instead of the newest receipt")
    p.add_argument("--slug", help="verify the newest receipt for this slug")
    p.add_argument("--no-receipt-update", action="store_true")
    args = p.parse_args(argv)

    receipt_pair = None
    url = args.url
    if not url:
        receipt_pair, _ = load_receipt(args.slug)
        if not receipt_pair:
            print(json.dumps({"check": "post_publish_verify", "status": "SKIP",
                              "detail": "no publish receipt to verify"},
                             ensure_ascii=False, indent=2))
            return 3
        url = (receipt_pair[1].get("artifact") or {}).get("url")
        if not url:
            print(json.dumps({"check": "post_publish_verify", "status": "FAIL",
                              "detail": "receipt has no published url"},
                             ensure_ascii=False, indent=2))
            return 2

    checks = verify(url, [])
    failed = [c for c in checks if c["status"] != "PASS"]
    status = "PASS" if not failed else "FAIL"
    detail = "; ".join(f"{c['check']}={c['status']}" for c in checks)

    if receipt_pair and not args.no_receipt_update:
        path, receipt = receipt_pair
        receipt["post_publish_verification"] = {
            "status": status, "checked_at": now_iso(), "detail": detail}
        # receipt_sha256 covers the evidence chain, which the verification result
        # is part of, so it is recomputed rather than left stale.
        body = {k: v for k, v in receipt.items() if k not in {"receipt_sha256", "receipt_id"}}
        import hashlib
        raw = json.dumps(body, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
        receipt["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        index = json.loads(RECEIPT_INDEX.read_text(encoding="utf-8"))
        for entry in index.get("receipts", []):
            if entry.get("receipt_id") == receipt.get("receipt_id"):
                entry["verification_status"] = status
                entry["receipt_sha256"] = receipt["receipt_sha256"]
        index["updated_at"] = now_iso()
        RECEIPT_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")

    print(json.dumps({"check": "post_publish_verify", "status": status,
                      "url": url, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
