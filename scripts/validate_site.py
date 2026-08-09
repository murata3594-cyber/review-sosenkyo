from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
IGNORED=("http://","https://","#","mailto:","tel:","javascript:","data:")
required=["index.html","article.html","rankings.html","category.html","methodology.html","about.html","disclosure.html","privacy.html","styles.css","site.js"]
errors=[]
for name in required:
    if not (ROOT/name).exists(): errors.append(f"Missing required file: {name}")
files={str(p.relative_to(ROOT)).replace("\\\\","/") for p in ROOT.rglob("*") if p.is_file()}
html=list(ROOT.glob("*.html"))
for page in html:
    text=page.read_text(encoding="utf-8")
    if "<title>" not in text.lower(): errors.append(f"{page.name}: missing <title>")
    for value in re.findall(r'(?:href|src)="([^"]+)"',text):
        if value.startswith(IGNORED): continue
        target=value.split("#",1)[0].split("?",1)[0]
        if target and target not in files: errors.append(f"{page.name}: broken local reference -> {target}")
if errors:
    print("Site validation FAILED")
    for e in errors: print(" -",e)
    sys.exit(1)
print(f"Site validation PASSED: {len(html)} HTML pages checked.")
