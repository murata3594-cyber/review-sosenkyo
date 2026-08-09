from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html",
    "article.html",
    "rankings.html",
    "category.html",
    "methodology.html",
    "about.html",
    "disclosure.html",
    "privacy.html",
    "styles.css",
    "site.js",
    "robots.txt",
    "sitemap.xml",
]
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.images = []
        self.html_lang = None
        self.has_viewport = False
        self.title_depth = 0
        self.title_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_lang = attrs.get("lang")
        if tag == "meta" and attrs.get("name", "").lower() == "viewport":
            self.has_viewport = True
        if tag == "img":
            self.images.append(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data):
        if self.title_depth:
            self.title_text.append(data)


errors = []
warnings = []
for name in REQUIRED:
    if not (ROOT / name).exists():
        errors.append(f"Missing required file: {name}")

all_files = {
    str(p.relative_to(ROOT)).replace("\\", "/")
    for p in ROOT.rglob("*")
    if p.is_file()
}

html_pages = list(ROOT.glob("*.html"))
for page in html_pages:
    text = page.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(text)

    title = "".join(parser.title_text).strip()
    if not title:
        errors.append(f"{page.name}: missing or empty <title>")
    if parser.html_lang != "ja":
        errors.append(f"{page.name}: <html lang=\"ja\"> is required")
    if not parser.has_viewport:
        errors.append(f"{page.name}: missing viewport meta tag")

    duplicate_ids = sorted({x for x in parser.ids if parser.ids.count(x) > 1})
    for dup in duplicate_ids:
        errors.append(f"{page.name}: duplicate id -> #{dup}")

    for image in parser.images:
        if not image.get("alt", "").strip():
            warnings.append(f"{page.name}: image missing alt -> {image.get('src', '(no src)')}")

    ids = set(parser.ids)
    for value in re.findall(r'(?:href|src)="([^"]+)"', text):
        if value.startswith(IGNORED_PREFIXES):
            continue
        if value == "#":
            continue
        if value.startswith("#"):
            anchor = value[1:]
            if anchor and anchor not in ids:
                warnings.append(f"{page.name}: missing same-page anchor -> {value}")
            continue

        target = value.split("#", 1)[0].split("?", 1)[0]
        if target and target not in all_files:
            errors.append(f"{page.name}: broken local reference -> {target}")

if warnings:
    print("Site validation WARNINGS")
    for warning in warnings:
        print(" -", warning)

if errors:
    print("Site validation FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"Site validation PASSED: {len(html_pages)} HTML pages checked; {len(warnings)} warning(s).")
