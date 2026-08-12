#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "services.json"


def env_for(cfg: dict, key: str) -> str:
    return os.getenv(str(cfg.get(key, "")), "").strip()


def replace_marker(text: str, name: str, content: str) -> tuple[str, str]:
    start = f"<!-- {name}_START -->"
    end = f"<!-- {name}_END -->"
    text = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
    return text, start + content + end if content else ""


def inject_head(text: str, marker: str, *, near_top: bool = False) -> str:
    if not marker:
        return text
    if near_top:
        match = re.search(r"<head(?:\s[^>]*)?>", text, flags=re.I)
        if match:
            return text[:match.end()] + marker + text[match.end():]
    if "</head>" not in text:
        return text
    return text.replace("</head>", marker + "</head>", 1)


def inject_after_body_start(text: str, marker: str) -> str:
    if not marker:
        return text
    match = re.search(r"<body(?:\s[^>]*)?>", text, flags=re.I)
    if not match:
        return text
    return text[:match.end()] + marker + text[match.end():]


def valid_a8_tag(tag: str) -> bool:
    if not tag:
        return False
    lowered = tag.lower()
    # Keep the A8-issued tag byte-for-byte inside our wrapper comments; only reject
    # strings that could escape the document head or inject a second document body.
    if "</head" in lowered or "<body" in lowered or "</body" in lowered:
        return False
    return "<script" in lowered or "<link" in lowered


def main() -> int:
    deploy = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    ga4 = env_for(cfg["analytics"]["ga4"], "measurement_id_env")
    verify = env_for(cfg["search_console"], "google_site_verification_env")
    publisher = env_for(cfg["adsense"], "publisher_id_env")
    ads_txt = env_for(cfg["adsense"], "ads_txt_record_env")
    contact = env_for(cfg["contact"], "email_env")
    a8_cfg = cfg.get("a8", {})
    a8_tag = env_for(a8_cfg, "link_manager_tag_env")

    ga4_ok = bool(re.fullmatch(r"G-[A-Z0-9]+", ga4))
    publisher_ok = bool(re.fullmatch(r"ca-pub-\d+", publisher))
    email_ok = bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", contact))
    a8_ok = bool(a8_cfg.get("inject_exact_tag", True) and valid_a8_tag(a8_tag))

    for page in deploy.glob("*.html"):
        text = page.read_text(encoding="utf-8")

        text, _ = replace_marker(text, "GA4", "")
        text, _ = replace_marker(text, "GOOGLE_VERIFY", "")
        text, _ = replace_marker(text, "ADSENSE", "")
        text, _ = replace_marker(text, "A8_LINK_MANAGER", "")
        text, _ = replace_marker(text, "GLOBAL_AFFILIATE_DISCLOSURE", "")

        if a8_ok:
            # A8 requires its Link Manager tag to be placed in the document head.
            # Do not rewrite, minify or otherwise alter the A8-issued snippet.
            text = inject_head(
                text,
                f"<!-- A8_LINK_MANAGER_START -->{a8_tag}<!-- A8_LINK_MANAGER_END -->",
                near_top=True,
            )
            if a8_cfg.get("global_pr_disclosure", True):
                disclosure = (
                    '<div class="global-affiliate-disclosure" role="note">'
                    '<strong>PR</strong> 当サイトはアフィリエイト広告を利用しています。'
                    '</div>'
                )
                text = inject_after_body_start(
                    text,
                    '<!-- GLOBAL_AFFILIATE_DISCLOSURE_START -->'
                    + disclosure
                    + '<!-- GLOBAL_AFFILIATE_DISCLOSURE_END -->',
                )

        if ga4_ok:
            code = (
                f'<script async src="https://www.googletagmanager.com/gtag/js?id={html.escape(ga4, quote=True)}"></script>'
                '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());'
                f'gtag("config","{html.escape(ga4, quote=True)}",{{anonymize_ip:true}});</script>'
            )
            text = inject_head(text, f"<!-- GA4_START -->{code}<!-- GA4_END -->")

        if verify:
            meta = f'<meta name="google-site-verification" content="{html.escape(verify, quote=True)}">'
            text = inject_head(text, f"<!-- GOOGLE_VERIFY_START -->{meta}<!-- GOOGLE_VERIFY_END -->")

        if publisher_ok:
            code = f'<script async crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={html.escape(publisher, quote=True)}"></script>'
            text = inject_head(text, f"<!-- ADSENSE_START -->{code}<!-- ADSENSE_END -->")

        if page.name == "contact.html":
            contact_block = (
                f'<p><a class="affiliate-btn" style="background:#4b8dff;color:#fff" href="mailto:{html.escape(contact, quote=True)}">メールで問い合わせる</a></p>'
                f'<p style="font-size:11px;color:#8296a7">連絡先：{html.escape(contact)}</p>'
            ) if email_ok else '<p>現在、独自ドメイン取得に合わせて専用窓口を準備しています。窓口有効化後、このページに連絡先を表示します。</p>'
            text = re.sub(
                r'<!-- CONTACT_METHOD_START -->.*?<!-- CONTACT_METHOD_END -->',
                '<!-- CONTACT_METHOD_START -->' + contact_block + '<!-- CONTACT_METHOD_END -->',
                text,
                flags=re.S,
            )

        page.write_text(text, encoding="utf-8")

    ads_path = deploy / "ads.txt"
    if ads_txt:
        ads_path.write_text(ads_txt.rstrip() + "\n", encoding="utf-8")
    elif ads_path.exists():
        ads_path.unlink()

    if a8_tag and not a8_ok:
        print("A8 Link Manager tag was present but rejected by the safety check; A8 injection remains off.")
    print(
        f"Services: GA4={'on' if ga4_ok else 'off'}, verification={'on' if bool(verify) else 'off'}, "
        f"AdSense={'on' if publisher_ok else 'off'}, contact={'on' if email_ok else 'off'}, A8={'on' if a8_ok else 'off'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
