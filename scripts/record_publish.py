#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "post_publish_log.json"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--article", required=True)
    p.add_argument("--agent", default="AI")
    p.add_argument("--commit", default="")
    p.add_argument("--notes", default="")
    a = p.parse_args()

    data = json.loads(LOG.read_text(encoding="utf-8"))
    entries = data.setdefault("entries", [])
    if any(str(x.get("id")) == a.id and str(x.get("article")) == a.article for x in entries):
        print(json.dumps({"result":"existing"}, ensure_ascii=False))
        return 0
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    item = {
        "id": a.id,
        "title": a.title,
        "article": a.article,
        "published_at": now,
        "published_by": a.agent,
        "commit": a.commit,
        "status": "AWAITING_OWNER_REVIEW",
        "notes": a.notes
    }
    entries.append(item)
    LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"result":"recorded","entry":item}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
