#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "affiliate.json"
CATALOG = ROOT / "data" / "affiliate_catalog.json"
OUTPUT = ROOT / "data" / "generated" / "affiliate_links.json"
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


def amazon_url(asin: str, tag: str) -> str:
    if not ASIN_RE.fullmatch(asin):
        raise ValueError(f"invalid ASIN: {asin}")
    return f"https://www.amazon.co.jp/dp/{asin}/?tag={urllib.parse.quote(tag, safe='-')}"


def norm(text: str) -> str:
    return re.sub(r"[\s\-‐‑‒–—―・･_/／（）()\[\]【】]", "", text).lower()


def rakuten_resolve(cfg: dict, query: str, must_include: list[str], affiliate_id: str, application_id: str, access_key: str) -> dict | None:
    endpoint = cfg.get("endpoint", "")
    params = {
        "applicationId": application_id,
        "affiliateId": affiliate_id,
        "keyword": query,
        "format": "json",
        "formatVersion": "2",
        "hits": "5",
        "availability": "1",
        "hasReviewFlag": "0",
        "sort": "-reviewCount",
        "elements": "itemName,itemCode,affiliateUrl,itemUrl,mediumImageUrls,reviewCount,reviewAverage",
    }
    url = endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"accessKey": access_key, "User-Agent": "review-sosenkyo-build/1.0"})
    with urllib.request.urlopen(req, timeout=12) as res:
        payload = json.loads(res.read().decode("utf-8"))
    for item in payload.get("items", []):
        name = str(item.get("itemName", ""))
        n = norm(name)
        if all(norm(token) in n for token in must_include):
            affiliate_url = str(item.get("affiliateUrl") or item.get("itemUrl") or "")
            if affiliate_url.startswith("https://"):
                images = item.get("mediumImageUrls") or []
                image = ""
                if images:
                    first = images[0]
                    image = first.get("imageUrl", "") if isinstance(first, dict) else str(first)
                return {
                    "url": affiliate_url,
                    "item_name": name,
                    "item_code": item.get("itemCode", ""),
                    "image": image,
                    "review_count": item.get("reviewCount"),
                    "review_average": item.get("reviewAverage"),
                }
    return None


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    generated = {
        "enabled": bool(cfg.get("enabled")),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": {},
    }

    amazon_cfg = cfg["providers"]["amazon"]
    amazon_tag = os.getenv(amazon_cfg.get("associate_tag_env", ""), "").strip()
    rakuten_cfg = cfg["providers"]["rakuten"]
    rakuten_affiliate = os.getenv(rakuten_cfg.get("affiliate_id_env", ""), "").strip()
    rakuten_app = os.getenv(rakuten_cfg.get("application_id_env", ""), "").strip()
    rakuten_key = os.getenv(rakuten_cfg.get("access_key_env", ""), "").strip()
    rakuten_ready = bool(rakuten_affiliate and rakuten_app and rakuten_key)

    for article, entry in catalog.get("articles", {}).items():
        products_out = []
        for product in entry.get("products", []):
            product_out = {"label": product.get("label", ""), "note": product.get("note", ""), "offers": []}

            amazon = product.get("amazon", {})
            asin = str(amazon.get("asin", "")).strip().upper()
            stored_amazon = str(amazon.get("stored_url", "")).strip()
            a_active = False
            a_url = ""
            a_reason = "Amazon ASIN/公式リンクまたはAssociate Tag未設定"
            if amazon_cfg.get("enabled") and amazon_tag and ASIN_RE.fullmatch(asin):
                a_url = amazon_url(asin, amazon_tag)
                a_active = True
                a_reason = ""
            elif amazon_cfg.get("enabled") and amazon_tag and stored_amazon.startswith("https://www.amazon.co.jp/"):
                a_url = stored_amazon
                a_active = True
                a_reason = ""
            product_out["offers"].append({"provider":"amazon","url":a_url,"active":a_active,"inactive_reason":a_reason})

            rakuten = product.get("rakuten", {})
            r_active = False
            r_url = ""
            r_meta = {}
            r_reason = "楽天API資格情報未設定"
            if rakuten_cfg.get("enabled") and rakuten_ready and rakuten.get("query"):
                try:
                    resolved = rakuten_resolve(
                        rakuten_cfg,
                        str(rakuten["query"]),
                        [str(x) for x in rakuten.get("must_include", [])],
                        rakuten_affiliate,
                        rakuten_app,
                        rakuten_key,
                    )
                    if resolved:
                        r_active = True
                        r_url = resolved.pop("url")
                        r_meta = resolved
                        r_reason = ""
                    else:
                        r_reason = "商品名条件を満たす現行商品を自動確定できず"
                except Exception as exc:
                    r_reason = f"楽天API一時失敗: {type(exc).__name__}"
            product_out["offers"].append({"provider":"rakuten","url":r_url,"active":r_active,"inactive_reason":r_reason,**r_meta})
            products_out.append(product_out)

        generated["articles"][article] = {"theme": entry.get("theme", ""), "products": products_out}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    active_count = sum(
        offer["active"]
        for article in generated["articles"].values()
        for product in article["products"]
        for offer in product["offers"]
    )
    print(f"Affiliate links generated: {active_count} active offer(s).")
    if not amazon_tag:
        print("Amazon remains hidden until AMAZON_ASSOCIATE_TAG + exact ASIN/official URL are configured.")
    if not rakuten_ready:
        print("Rakuten remains hidden until RAKUTEN_AFFILIATE_ID / RAKUTEN_APPLICATION_ID / RAKUTEN_ACCESS_KEY are configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
