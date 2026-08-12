#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "affiliate.json"
CATALOG = ROOT / "data" / "affiliate_catalog.json"
OUTPUT = ROOT / "data" / "generated" / "affiliate_links.json"

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


def amazon_url(asin: str, tag: str) -> str:
    if not ASIN_RE.fullmatch(asin):
        raise ValueError(f"invalid ASIN: {asin}")
    return f"https://www.amazon.co.jp/dp/{asin}/ref=nosim?tag={urllib.parse.quote(tag, safe='-')}"


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    generated = {"enabled": bool(cfg.get("enabled")), "articles": {}}

    amazon_cfg = cfg["providers"]["amazon"]
    amazon_tag = os.getenv(amazon_cfg.get("associate_tag_env", ""), "").strip()

    for article, entry in catalog.get("articles", {}).items():
        out_offers = []
        for offer in entry.get("offers", []):
            provider = offer.get("provider")
            url = ""
            active = False
            reason = "provider disabled or credentials missing"

            if provider == "amazon" and amazon_cfg.get("enabled") and amazon_tag:
                asin = str(offer.get("asin", "")).strip().upper()
                if asin:
                    url = amazon_url(asin, amazon_tag)
                    active = True
                    reason = ""
            elif provider in {"rakuten", "a8", "valuecommerce"}:
                stored_url = str(offer.get("stored_url", "")).strip()
                if cfg["providers"].get(provider, {}).get("enabled") and stored_url.startswith("https://"):
                    url = stored_url
                    active = True
                    reason = ""

            out_offers.append({
                "label": offer.get("label", ""),
                "provider": provider,
                "url": url,
                "active": active,
                "note": offer.get("note", ""),
                "inactive_reason": reason if not active else ""
            })

        generated["articles"][article] = {
            "theme": entry.get("theme", ""),
            "offers": out_offers
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    active_count = sum(o["active"] for a in generated["articles"].values() for o in a["offers"])
    print(f"Affiliate links generated: {active_count} active offer(s).")
    if not cfg.get("enabled"):
        print("Affiliate system is intentionally disabled until provider IDs are configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
