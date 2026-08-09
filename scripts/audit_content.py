from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "content_manifest.json"
QUEUE_PATH = ROOT / "data" / "topic_queue.json"


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        return None


def validate_review_snapshots(value, path: str, errors: list[str]):
    if isinstance(value, dict):
        snapshot_like = path.endswith("review_snapshot") or path.endswith("additional_review_context")
        if snapshot_like and ("rating" in value or "count" in value):
            if not value.get("checked_at"):
                errors.append(f"{path}: checked_at is required for dynamic review data")
            else:
                try:
                    checked = date.fromisoformat(str(value["checked_at"])[:10])
                    if checked > date.today():
                        errors.append(f"{path}: checked_at is in the future: {checked}")
                except ValueError:
                    errors.append(f"{path}: invalid checked_at: {value.get('checked_at')}")

            rating = value.get("rating")
            if rating is not None and (not isinstance(rating, (int, float)) or not 0 <= rating <= 5):
                errors.append(f"{path}: rating must be null or between 0 and 5")

            count = value.get("count")
            if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
                errors.append(f"{path}: count must be null or a non-negative integer")

        for key, child in value.items():
            validate_review_snapshots(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_review_snapshots(child, f"{path}[{index}]", errors)


def require_unique(items, key: str, errors: list[str]):
    seen = {}
    for index, item in enumerate(items):
        value = item.get(key)
        if value in (None, ""):
            errors.append(f"manifest.published[{index}]: missing {key}")
            continue
        if value in seen:
            errors.append(f"manifest: duplicate {key}={value!r} at indexes {seen[value]} and {index}")
        seen[value] = index


def main() -> int:
    errors: list[str] = []
    manifest = load_json(MANIFEST_PATH, errors)
    queue = load_json(QUEUE_PATH, errors)
    if not isinstance(manifest, dict) or not isinstance(queue, dict):
        for error in errors:
            print("ERROR:", error)
        return 1

    published = manifest.get("published")
    if not isinstance(published, list) or not published:
        errors.append("manifest.published must be a non-empty list")
        published = []

    for key in ("id", "number", "article", "research"):
        require_unique(published, key, errors)

    queue_topics = {item.get("id"): item for item in queue.get("topics", []) if isinstance(item, dict)}

    for index, item in enumerate(published):
        prefix = f"manifest.published[{index}]"
        for key in ("id", "number", "category", "title", "subtitle", "axes", "article", "research"):
            if not item.get(key):
                errors.append(f"{prefix}: missing {key}")

        if item.get("category") not in {"kitchen", "cleaning", "pet"}:
            errors.append(f"{prefix}: invalid category {item.get('category')!r}")

        article_rel = item.get("article")
        research_rel = item.get("research")
        article_path = ROOT / article_rel if article_rel else None
        research_path = ROOT / research_rel if research_rel else None
        if article_path and not article_path.exists():
            errors.append(f"{prefix}: missing article file {article_rel}")
        if research_path and not research_path.exists():
            errors.append(f"{prefix}: missing research file {research_rel}")
        elif research_path:
            payload = load_json(research_path, errors)
            if isinstance(payload, dict):
                if not payload.get("researched_at"):
                    errors.append(f"{research_rel}: missing researched_at")
                else:
                    try:
                        researched = date.fromisoformat(str(payload["researched_at"])[:10])
                        if researched > date.today():
                            errors.append(f"{research_rel}: researched_at is in the future")
                    except ValueError:
                        errors.append(f"{research_rel}: invalid researched_at {payload.get('researched_at')}")
                if not payload.get("status"):
                    errors.append(f"{research_rel}: missing status")
                validate_review_snapshots(payload, research_rel, errors)

        queue_item = queue_topics.get(item.get("id"))
        if not queue_item:
            errors.append(f"{prefix}: no matching topic in data/topic_queue.json")
        elif not str(queue_item.get("status", "")).startswith("PUBLISHED"):
            errors.append(f"{prefix}: queue status is not published: {queue_item.get('status')!r}")
        else:
            if queue_item.get("article") != article_rel:
                errors.append(f"{prefix}: queue article mismatch")
            if queue_item.get("research") != research_rel:
                errors.append(f"{prefix}: queue research mismatch")

    next_ids = [item.get("id") for item in manifest.get("next", []) if isinstance(item, dict)]
    published_ids = {item.get("id") for item in published}
    overlap = sorted(published_ids.intersection(next_ids))
    if overlap:
        errors.append(f"manifest: IDs cannot be both published and next: {overlap}")

    if errors:
        print(f"Content audit FAILED: {len(errors)} error(s)")
        for error in errors:
            print(" -", error)
        return 1

    print(f"Content audit PASSED: {len(published)} published article(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
