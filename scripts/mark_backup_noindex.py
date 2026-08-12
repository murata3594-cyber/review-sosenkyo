#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root=Path(sys.argv[1]).resolve()
for page in root.glob("*.html"):
    text=page.read_text(encoding="utf-8")
    text=re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', '<meta name="robots" content="noindex,nofollow">', text, flags=re.I)
    if not re.search(r'<meta\s+name=["\']robots["\']', text, flags=re.I) and "</head>" in text:
        text=text.replace("</head>", '<meta name="robots" content="noindex,nofollow"></head>', 1)
    page.write_text(text, encoding="utf-8")
(root/"robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
print(f"Backup noindex applied to {len(list(root.glob('*.html')))} HTML files")
