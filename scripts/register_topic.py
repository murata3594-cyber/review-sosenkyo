#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "topic_queue.json"
MANIFEST = ROOT / "data" / "content_manifest.json"
PREFIX = "T"


def norm(value: str) -> str:
    return re.sub(r"[\s\-_/・、。,.]+", "", value).lower()


def reserved_manifest_items() -> list[dict]:
    if not MANIFEST.exists():
        return []
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(data.get("published", [])) + list(data.get("next", []))


def next_id(topics: list[dict], reserved: list[dict]) -> str:
    nums = []
    for item in [*topics, *reserved]:
        m = re.fullmatch(r"T(\d+)", str(item.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return f"{PREFIX}{max(nums, default=0)+1:03d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Register/claim a レビュー総選挙 topic without asking for pre-approval.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--agent", default="AI")
    parser.add_argument("--source", default="owner_rough_brief")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    topics = data.setdefault("topics", [])
    reserved = reserved_manifest_items()
    key = norm(args.topic)

    for item in topics:
        if norm(str(item.get("topic", ""))) == key:
            print(json.dumps({"result":"existing_queue","topic":item}, ensure_ascii=False))
            return 0
    for item in reserved:
        if norm(str(item.get("title", ""))) == key:
            print(json.dumps({"result":"existing_manifest","topic":item}, ensure_ascii=False))
            return 0

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    item = {
        "id": next_id(topics, reserved),
        "topic": args.topic,
        "status": "RESEARCHING",
        "source": args.source,
        "summary": args.summary,
        "claimed_by": args.agent,
        "claimed_at": now,
        "next_action": "verify current SKUs, official specifications and review evidence; publish automatically only after full QA"
    }
    topics.append(item)
    data["updated_at"] = now[:10]
    QUEUE.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"result":"registered","topic":item}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
