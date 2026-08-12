from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "content_manifest.json"
BASE_REQUIRED = [
    "index.html", "rankings.html", "category.html", "methodology.html",
    "about.html", "disclosure.html", "privacy.html", "contact.html",
    "styles.css", "site.js", "robots.txt", "sitemap.xml",
    "data/content_manifest.json", "data/topic_queue.json", "data/affiliate_catalog.json",
    "config/site.json", "config/affiliate.json", "config/services.json",
    "scripts/build_dist.py", "scripts/finalize_seo.py", "scripts/build_affiliate_links.py",
    "scripts/render_affiliate_blocks.py", "scripts/inject_services.py", "scripts/audit_content_quality.py",
    "package.json", "wrangler.jsonc"
]
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:")
# Generated/vendor directories are not repository-authored source and may contain
# token-shaped test strings inside third-party packages (for example Wrangler).
# Keep the secret scan strict for all project-authored files while excluding only
# external/build artefacts.
IGNORED_DIR_NAMES = {".git", "dist", "node_modules", ".wrangler", ".cache", ".tmp", "tmp"}


def is_ignored_path(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES for part in rel.parts)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.images=[]; self.html_lang=None; self.has_viewport=False; self.title_depth=0; self.title_text=[]; self.h1=0
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag == "html": self.html_lang=attrs.get("lang")
        if tag == "meta" and attrs.get("name", "").lower() == "viewport": self.has_viewport=True
        if tag == "img": self.images.append(attrs)
        if tag == "h1": self.h1 += 1
        if "id" in attrs: self.ids.append(attrs["id"])
        if tag == "title": self.title_depth += 1
    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth: self.title_depth -= 1
    def handle_data(self, data):
        if self.title_depth: self.title_text.append(data)


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        return {}


errors=[]; warnings=[]
manifest=load_json(MANIFEST_PATH, errors) if MANIFEST_PATH.exists() else {}
required=list(BASE_REQUIRED)
for item in manifest.get("published", []):
    article=item.get("article"); research=item.get("research")
    if article: required.append(article)
    if research: required.append(research)

for name in dict.fromkeys(required):
    if not (ROOT/name).exists(): errors.append(f"Missing required file: {name}")

for config_name in ("config/site.json","config/affiliate.json","config/services.json","data/affiliate_catalog.json"):
    path=ROOT/config_name
    if path.exists(): load_json(path, errors)
for research in [item.get("research") for item in manifest.get("published", []) if item.get("research")]:
    path=ROOT/research
    if path.exists(): load_json(path, errors)

all_files={
    str(p.relative_to(ROOT)).replace("\\", "/")
    for p in ROOT.rglob("*")
    if p.is_file() and not is_ignored_path(p)
}
html_pages=list(ROOT.glob("*.html"))
for page in html_pages:
    text=page.read_text(encoding="utf-8"); parser=PageParser(); parser.feed(text)
    if not "".join(parser.title_text).strip(): errors.append(f"{page.name}: missing or empty <title>")
    if parser.html_lang != "ja": errors.append(f"{page.name}: <html lang=\"ja\"> is required")
    if not parser.has_viewport: errors.append(f"{page.name}: missing viewport meta tag")
    if page.name != "404.html" and parser.h1 != 1: errors.append(f"{page.name}: exactly one h1 required, found {parser.h1}")
    for dup in sorted({x for x in parser.ids if parser.ids.count(x)>1}): errors.append(f"{page.name}: duplicate id -> #{dup}")
    for image in parser.images:
        if not image.get("alt", "").strip(): warnings.append(f"{page.name}: image missing alt -> {image.get('src', '(no src)')}")
    ids=set(parser.ids)
    for value in re.findall(r'(?:href|src)="([^"]+)"', text):
        if value.startswith(IGNORED_PREFIXES): continue
        if value == "#": continue
        if value.startswith("#"):
            anchor=value[1:]
            if anchor and anchor not in ids: warnings.append(f"{page.name}: missing same-page anchor -> {value}")
            continue
        target=value.split("#",1)[0].split("?",1)[0]
        if target and target not in all_files: errors.append(f"{page.name}: broken local reference -> {target}")

secret_patterns=[
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
for path in ROOT.rglob("*"):
    if not path.is_file() or is_ignored_path(path): continue
    if path.suffix.lower() not in {".html",".js",".json",".md",".txt",".yml",".yaml",".py",".jsonc"}: continue
    try: text=path.read_text(encoding="utf-8")
    except Exception: continue
    if any(rx.search(text) for rx in secret_patterns): errors.append(f"Possible secret committed: {path.relative_to(ROOT)}")

if warnings:
    print("Site validation WARNINGS")
    for warning in sorted(set(warnings)): print(" -", warning)
if errors:
    print("Site validation FAILED")
    for error in sorted(set(errors)): print(" -", error)
    sys.exit(1)
print(f"Site validation PASSED: {len(html_pages)} HTML pages checked; {len(manifest.get('published', []))} published item(s); {len(warnings)} warning(s).")
