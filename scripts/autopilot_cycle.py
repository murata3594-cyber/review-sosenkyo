#!/usr/bin/env python3
"""レビュー総選挙 autopilot — decide what one unattended cycle should do.

Publishing here was already deterministic and evidence-first: a research ledger
plus a manifest drive a reproducible build. What was missing is the upstream
half. Nothing in this repository ever *started* a comparison — the scheduled
jobs only audited what a human had already produced, so the medium could go
quiet indefinitely without anything reporting a problem.

This script supplies the deterministic decision layer of
`automation_mode: scheduled_agent`: whether a cycle may run, what it works on,
and which gates its output must clear. The research and writing themselves stay
with the agent.

Exit codes
----------
0  a work order was produced
2  the cycle is blocked (fail-closed)
3  nothing to do right now (not an error)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "automation_policy.json"
QUEUE = ROOT / "data" / "topic_queue.json"
MANIFEST = ROOT / "data" / "content_manifest.json"
WORK_ORDER = ROOT / "data" / "autopilot_work_order.json"
RUNTIME_CLIENT = ROOT / "scripts" / "acr_runtime.py"

JST = timezone(timedelta(hours=9))

# Matches the threshold research-freshness.yml passes to check_research_freshness.py.
RESEARCH_FRESHNESS_DAYS = 30


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def today_jst() -> date:
    stamp = os.environ.get("ACR_NOW")
    if stamp:
        return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc).astimezone(JST).date()
    return datetime.now(JST).date()


def runtime_gate(for_run: bool):
    args = [sys.executable, str(RUNTIME_CLIENT), "gate", "--strict"]
    if for_run:
        args.append("--for-run")
    proc = subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT))
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"check": "acr.gate", "status": "FAIL",
                   "errors": ["acr_gate_unreadable"], "raw": proc.stdout[-400:]}
    return proc.returncode == 0, payload


def collect_checked_dates(value, found):
    """Mirrors scripts/check_research_freshness.py so both agree on 'stale'."""
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


def parse_resume_date(value):
    """Accept an ISO date, or prose that begins with one (e.g. '2026-10-01再調査')."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def pick_researching_topic(queue):
    for topic in queue.get("topics", []):
        if topic.get("status") == "RESEARCHING" and not topic.get("claimed_by"):
            return topic
    return None


def pick_due_renewal(queue, today):
    due = []
    for topic in queue.get("topics", []):
        if topic.get("status") != "HOLD_RENEWAL":
            continue
        resume = parse_resume_date(topic.get("resume_after"))
        if resume and resume <= today:
            due.append((resume, topic))
    due.sort(key=lambda pair: pair[0])
    return due[0][1] if due else None


def pick_due_planned(manifest, today):
    due = []
    for item in manifest.get("next", []):
        resume = parse_resume_date(item.get("status"))
        if resume and resume <= today:
            due.append((resume, item))
    due.sort(key=lambda pair: pair[0])
    return due[0][1] if due else None


def pick_stale_research(manifest, today):
    worst = None
    for item in manifest.get("published", []):
        research = item.get("research")
        if not research:
            continue
        path = ROOT / research
        if not path.exists():
            return {"id": item.get("id"), "title": item.get("title"),
                    "article": item.get("article"), "research": research,
                    "reason": "research ledger file is missing", "age_days": None}
        found = []
        collect_checked_dates(load(path), found)
        if not found:
            return {"id": item.get("id"), "title": item.get("title"),
                    "article": item.get("article"), "research": research,
                    "reason": "research ledger has no checked_at", "age_days": None}
        age = (today - min(found)).days
        if age >= RESEARCH_FRESHNESS_DAYS:
            if worst is None or age > worst["age_days"]:
                worst = {"id": item.get("id"), "title": item.get("title"),
                         "article": item.get("article"), "research": research,
                         "reason": f"oldest checked_at is {age}d old "
                                   f"(threshold {RESEARCH_FRESHNESS_DAYS}d)",
                         "age_days": age}
    return worst


def build_work_order(policy, queue, kind, subject, reason, gate_payload):
    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": "murata3594-cyber/review-sosenkyo",
        "profile": "review_media",
        "automation_mode": "scheduled_agent",
        "work_kind": kind,
        "subject": subject,
        "selection_reason": reason,
        "rules": queue.get("rules", {}),
        "auto_publish_if": policy.get("auto_publish_if", []),
        "hold_if": policy.get("hold_if", []),
        "max_new_articles_per_agent_run": policy.get("max_new_articles_per_agent_run", 1),
        "runtime_gate": gate_payload,
        "release_rule": (
            "unified_feedback_gate PASS AND acr_runtime gate PASS AND "
            "required_local_gates PASS AND post_publish_verification PASS"
        ),
        "on_unverifiable_claim":
            "leave the topic in RESEARCHING or NEEDS_REVIEW with a reason; do not publish",
    }


def cmd_plan(args) -> int:
    policy = load(POLICY)
    queue = load(QUEUE)
    manifest = load(MANIFEST)
    today = today_jst()

    ok, gate_payload = runtime_gate(for_run=not args.ci)
    if not ok:
        print(json.dumps({"decision": "BLOCKED", "reason": "acr_gate_fail",
                          "runtime_gate": gate_payload}, ensure_ascii=False, indent=2))
        return 2

    kind = subject = reason = None

    topic = pick_researching_topic(queue)
    if topic:
        kind = "new_comparison_article"
        subject = {"topic_id": topic.get("id"), "topic": topic.get("topic"),
                   "comparison_axes": topic.get("comparison_axes"),
                   "next_action": topic.get("next_action")}
        reason = "unclaimed RESEARCHING topic"

    if subject is None:
        renewal = pick_due_renewal(queue, today)
        if renewal:
            kind = "renewal_recheck"
            subject = {"topic_id": renewal.get("id"), "topic": renewal.get("topic"),
                       "research": renewal.get("research"),
                       "resume_after": renewal.get("resume_after"),
                       "next_action": renewal.get("next_action")}
            reason = "HOLD_RENEWAL topic whose resume_after date has arrived"

    if subject is None:
        planned = pick_due_planned(manifest, today)
        if planned:
            kind = "planned_article"
            subject = {"topic_id": planned.get("id"), "title": planned.get("title"),
                       "subtitle": planned.get("subtitle"), "axes": planned.get("axes"),
                       "scheduled": planned.get("status")}
            reason = "manifest 'next' entry whose scheduled date has arrived"

    if subject is None:
        stale = pick_stale_research(manifest, today)
        if stale:
            kind = "refresh_stale_research"
            subject = stale
            reason = "published comparison whose research ledger is past the freshness threshold"

    if subject is None:
        print(json.dumps({"decision": "NO_WORK",
                          "reason": "nothing researching, nothing due, nothing stale"},
                         ensure_ascii=False, indent=2))
        return 3

    order = build_work_order(policy, queue, kind, subject, reason, gate_payload)
    out = Path(args.out) if args.out else WORK_ORDER
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(order, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(order, ensure_ascii=False, indent=2))
    return 0


def cmd_prompt(args) -> int:
    path = Path(args.work_order) if args.work_order else WORK_ORDER
    if not path.exists():
        print(f"missing work order: {path}", file=sys.stderr)
        return 2
    order = load(path)

    lines = [
        "あなたはレビュー総選挙の無人運転サイクルを実行するエージェントです。",
        "根拠台帳（data/research/*.json）とmanifestを正本とする、決定論的な公開システムです。",
        "公開ゲートは fail-closed です。根拠が足りなければ公開せず RESEARCHING / NEEDS_REVIEW に留めます。",
        "",
        f"作業種別: {order.get('work_kind')}",
        f"選定理由: {order.get('selection_reason')}",
        "",
        "対象:",
        json.dumps(order.get("subject", {}), ensure_ascii=False, indent=2),
        "",
        "この媒体の絶対規則:",
        "  - 架空の実体験・使用感を書かない。実際に使っていないものを「使った」と書かない。",
        "  - レビュー件数・評価・価格・在庫は必ず checked_at 付きで根拠台帳へ記録する。",
        "  - 同一商品であることをSKU/型番レベルで確認する。別サイズ・別世代を混ぜない。",
        "  - 大量の生レビュー本文をこの公開リポジトリへ保存しない。",
        "  - 医療・金融・法務の高リスク断定をしない。",
        "  - アフィリエイトは資格情報があるプロバイダのみ。開示表記を省略しない。",
        "",
        "公開してよい条件（すべて満たすこと）:",
    ]
    for cond in order.get("auto_publish_if", []):
        lines.append(f"  - {cond}")
    lines += ["", "一つでも該当したら公開せず保留する条件:"]
    for cond in order.get("hold_if", []):
        lines.append(f"  - {cond}")
    lines += [
        "",
        "手順:",
        "  1. 作業開始前に data/topic_queue.json の該当トピックへ claimed_by / claimed_at を設定する。",
        "  2. data/research/<slug>-<YYYY-MM-DD>.json に根拠台帳を作る（checked_at 必須）。",
        "  3. 記事HTMLを作る。",
        "  4. data/affiliate_catalog.json に商品候補を登録する。",
        "  5. data/content_manifest.json へ1件追加する。",
        "  6. 以下を **この順序で** 実行し、落ちたら公開しない。",
        "     python scripts/build_dist.py",
        "     python scripts/validate_site.py",
        "     python scripts/audit_content.py",
        "     python scripts/audit_content_quality.py",
        "     python scripts/check_research_freshness.py --days 30",
        "  7. python scripts/record_publish.py で公開記録を残す。",
        "  8. python scripts/acr_runtime.py receipt ... で公開証跡を出す。",
        "  9. 公開後に python scripts/post_publish_verify.py を実行し、",
        "     post_publish_verification が PASS になるまで完了と見なさない。",
        "",
        "保留する場合は、data/topic_queue.json の該当トピックへ理由を日本語で明記し、",
        "python scripts/acr_runtime.py heartbeat --stage cycle_end --status hold --detail '<理由>' を実行する。",
        "",
        f"リリース規則: {order.get('release_rule')}",
    ]
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="レビュー総選挙 autopilot cycle planner")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("plan")
    pl.add_argument("--out")
    pl.add_argument("--ci", action="store_true")
    pl.set_defaults(func=cmd_plan)

    pr = sub.add_parser("prompt")
    pr.add_argument("--work-order")
    pr.add_argument("--out")
    pr.set_defaults(func=cmd_prompt)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
