#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"
AFFILIATE = ROOT / "data" / "affiliate_catalog.json"


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.h1=0; self.external=[]; self.meta_description=""; self.title=""; self._title=False
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag == "h1": self.h1 += 1
        if tag == "title": self._title=True
        if tag == "meta" and attrs.get("name", "").lower()=="description": self.meta_description=attrs.get("content", "").strip()
        if tag == "a":
            href=attrs.get("href", "")
            if href.startswith(("https://","http://")): self.external.append(href)
    def handle_endtag(self, tag):
        if tag == "title": self._title=False
    def handle_data(self, data):
        s=data.strip()
        if not s: return
        self.text.append(s)
        if self._title: self.title += s


def load(path: Path, errors: list[str]) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        return {}


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value[:10], "%Y-%m-%d")
        return True
    except Exception:
        return False


def audit_research(path: Path, errors: list[str], warnings: list[str]) -> None:
    data=load(path, errors)
    policy=data.get("policy", {})
    if policy.get("raw_review_text_stored") is not False:
        errors.append(f"{path.relative_to(ROOT)}: raw_review_text_stored must be false")
    researched=str(data.get("researched_at", ""))
    if researched and not valid_date(researched):
        errors.append(f"{path.relative_to(ROOT)}: invalid researched_at {researched}")
    products=data.get("products", [])
    if not isinstance(products, list) or not products:
        warnings.append(f"{path.relative_to(ROOT)}: no product records")
        return
    for product in products:
        name=str(product.get("name", "unnamed"))
        snap=product.get("review_snapshot")
        if not isinstance(snap, dict):
            continue
        count=snap.get("count")
        rating=snap.get("rating")
        checked=str(snap.get("checked_at", ""))
        if not isinstance(count, int) or count < 0:
            errors.append(f"{path.relative_to(ROOT)} / {name}: invalid review count {count}")
        if not isinstance(rating, (int,float)) or not (0 <= float(rating) <= 5):
            errors.append(f"{path.relative_to(ROOT)} / {name}: invalid rating {rating}")
        if count == 0 and rating not in (0, 0.0):
            errors.append(f"{path.relative_to(ROOT)} / {name}: rating must be 0 when count is 0")
        if checked and not valid_date(checked):
            errors.append(f"{path.relative_to(ROOT)} / {name}: invalid checked_at {checked}")
        if not product.get("official_source"):
            warnings.append(f"{path.relative_to(ROOT)} / {name}: official_source missing")


def main() -> int:
    errors=[]; warnings=[]
    manifest=load(MANIFEST, errors)
    affiliate=load(AFFILIATE, errors)
    catalog_articles=set(affiliate.get("articles", {}))
    published=manifest.get("published", [])

    if len(published) < 10:
        warnings.append(f"Published article count is only {len(published)}")

    fake_firsthand=("実際に使ってみた","実際に使用してみた","私が使った","私が試した","使ってみました")

    for item in published:
        article_name=item.get("article", "")
        research_name=item.get("research", "")
        if article_name not in catalog_articles:
            errors.append(f"Affiliate catalog missing published article: {article_name}")
        article=ROOT/article_name
        if article.exists():
            source=article.read_text(encoding="utf-8")
            parser=TextParser(); parser.feed(source)
            body="".join(parser.text)
            if parser.h1 != 1:
                errors.append(f"{article_name}: expected exactly one h1, found {parser.h1}")
            if len(body) < 1200:
                warnings.append(f"{article_name}: visible text is short ({len(body)} chars)")
            if len(parser.external) < 2:
                warnings.append(f"{article_name}: fewer than 2 external source links")
            if 'id="sources"' not in source:
                warnings.append(f"{article_name}: sources section id missing")
            if any(phrase in body for phrase in fake_firsthand):
                errors.append(f"{article_name}: possible unsupported firsthand claim")
            if len(parser.meta_description) < 45:
                warnings.append(f"{article_name}: meta description may be too short")
        if research_name:
            path=ROOT/research_name
            if path.exists(): audit_research(path, errors, warnings)

    if warnings:
        print("CONTENT AUDIT WARNINGS")
        for w in sorted(set(warnings)): print(" -", w)
    if errors:
        print("CONTENT AUDIT FAILED")
        for e in sorted(set(errors)): print(" -", e)
        return 1
    print(f"CONTENT AUDIT PASSED: {len(published)} published article(s), {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
