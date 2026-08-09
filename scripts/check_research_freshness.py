from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "content_manifest.json"


def collect_checked_dates(value, found: list[date]):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "checked_at" and isinstance(child, str):
                try:
                    found.append(date.fromisoformat(child[:10]))
                except ValueError:
                    pass
            else:
                collect_checked_dates(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_checked_dates(child, found)


def main(days: int, report_path: Path) -> int:
    today = date.today()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stale = []
    missing_dates = []

    for item in manifest.get("published", []):
        research_path = ROOT / item["research"]
        payload = json.loads(research_path.read_text(encoding="utf-8"))
        checked_dates: list[date] = []
        collect_checked_dates(payload, checked_dates)
        if not checked_dates:
            missing_dates.append((item["id"], item["title"], item["research"]))
            continue
        oldest = min(checked_dates)
        age = (today - oldest).days
        if age >= days:
            stale.append((item["id"], item["title"], item["research"], oldest.isoformat(), age))

    lines = [
        "# Research data refresh report",
        "",
        f"Generated: {today.isoformat()}",
        f"Threshold: {days} days",
        "",
    ]
    if stale:
        lines += ["## Stale research", ""]
        for item_id, title, research, checked, age in stale:
            lines.append(f"- **{item_id} {title}** — oldest checked_at `{checked}` ({age} days) — `{research}`")
        lines.append("")
    if missing_dates:
        lines += ["## Missing checked_at", ""]
        for item_id, title, research in missing_dates:
            lines.append(f"- **{item_id} {title}** — `{research}`")
        lines.append("")
    if not stale and not missing_dates:
        lines += ["All published research datasets are within the freshness threshold.", ""]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(report_path.read_text(encoding="utf-8"))
    return 1 if stale or missing_dates else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--report", default="research-freshness-report.md")
    args = parser.parse_args()
    raise SystemExit(main(args.days, Path(args.report)))
