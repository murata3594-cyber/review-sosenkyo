#!/usr/bin/env python3
"""Autonomous Content Runtime (ACR) shared client.

Canonical source: murata3594-cyber/military-v3 : scripts/acr_runtime.py
Vendored byte-identical into every media repository so that an unattended run
never depends on cross-repository network access to make a local decision.

Design rules
------------
* Standard library only. No network calls, no third-party imports.
* Deterministic: same inputs -> same canonical hashes.
* Fail-closed: unknown/missing state is a failure, never an implicit pass.
* Every subcommand exits 0 on PASS and 2 on FAIL so CI can gate on it.

Subcommands
-----------
  selfcheck                 print vendored client version and content hash
  adapter-validate          validate UNIFIED_PRODUCTION_SYSTEM.json
  state-init                create data/automation_runtime.json from the adapter
  state-show                print current runtime state
  state-validate            validate runtime state against the embedded schema
  heartbeat                 record a stage outcome and refresh the heartbeat
  pause / resume            set or clear paused_reason
  receipt                   emit a publish receipt into data/run_receipts/
  verify-receipt            check a receipt has a complete evidence chain
  kpi                       recompute rolling KPI from receipts
  gate                      the unattended-run precondition gate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLIENT_VERSION = "2.0.0"
STATE_SCHEMA_VERSION = "2.0.0"
RECEIPT_SCHEMA_VERSION = "2.0.0"

AUTOMATION_MODES = {
    # A human or scheduler starts an agent; the agent then runs to publish on its own.
    "agent_driven",
    # A commit/event into the repository drives build and publish.
    "event_driven",
    # A cron-scheduled agent run: unattended discovery through publish.
    "scheduled_agent",
    # A long-running local daemon owns the cycle.
    "scheduled_daemon",
}

RUNTIME_STATUSES = {"RUNNING", "IDLE", "PAUSED", "FAILED", "HOLD", "UNCONFIGURED"}
STAGE_STATUSES = {"ok", "fail", "skip", "hold"}

ADAPTER_FILE = "UNIFIED_PRODUCTION_SYSTEM.json"
STATE_FILE = "data/automation_runtime.json"
RECEIPT_DIR = "data/run_receipts"
RECEIPT_INDEX = "data/run_receipt_index.json"

ISO = "%Y-%m-%dT%H:%M:%SZ"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def repo_root() -> Path:
    override = os.environ.get("ACR_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[1]


def now_utc() -> datetime:
    stamp = os.environ.get("ACR_NOW")
    if stamp:
        return datetime.strptime(stamp, ISO).replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(ISO)


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, ISO).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def canonical_hash(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def client_hash() -> str:
    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report(title: str, errors, warnings=None, extra=None) -> int:
    payload = {
        "check": title,
        "status": "PASS" if not errors else "FAIL",
        "errors": list(errors),
        "warnings": list(warnings or []),
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


# --------------------------------------------------------------------------
# adapter
# --------------------------------------------------------------------------

# Keys required by the Unified Production Feedback OS v2 adapter schema
# (schemas/unified_production_adapter.schema.json in the kernel repository).
# ACR does not redefine them; it only requires that they are present and adds
# one additive block of its own, "automation".
REQUIRED_ADAPTER_KEYS = [
    "schema_version",
    "kernel_repository",
    "kernel_branch",
    "required_kernel_version",
    "profiles",
    "default_profile",
    "must_not_fork_kernel",
    "local_release_gates_remain_required",
    "automation",
]

REQUIRED_AUTOMATION_KEYS = [
    "repository",
    "automation_mode",
    "runtime_expected",
    "runtime_owner",
    "max_silence_hours",
    "publish_targets",
    "required_local_gates",
]


def read_adapter(root: Path):
    path = root / ADAPTER_FILE
    if not path.exists():
        return None, [f"missing_adapter:{ADAPTER_FILE}"]
    try:
        return load_json(path), []
    except json.JSONDecodeError as exc:
        return None, [f"adapter_not_json:{exc}"]


def declared_publish_target(root: Path, automation: dict):
    """Read the repository's own source of truth for its production URL.

    A repository states where that lives via automation.publish_target_source,
    because the two media that use this keep it in different places: a bare text
    file in one, a JSON key in the other. When it is declared, publish_targets
    has to agree with it.
    """
    source = automation.get("publish_target_source")
    if not isinstance(source, dict):
        return None, []
    rel = source.get("path")
    if not isinstance(rel, str) or not rel:
        return None, ["adapter_publish_target_source_path_missing"]
    path = root / rel
    if not path.exists():
        return None, [f"publish_target_source_missing:{rel}"]
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"publish_target_source_unreadable:{rel}:{exc}"]
    key = source.get("json_key")
    if key:
        try:
            value = json.loads(raw).get(key)
        except json.JSONDecodeError as exc:
            return None, [f"publish_target_source_not_json:{rel}:{exc}"]
        if not isinstance(value, str):
            return None, [f"publish_target_source_key_missing:{rel}:{key}"]
    else:
        value = raw
    return value.strip().rstrip("/"), []


MAX_SILENCE_HOURS = 168

# What the kernel declares about a medium and what the medium does have to be the
# same thing. These are the fields where a quiet local edit turns monitoring off
# or drops a release gate, so they are compared rather than trusted.
REGISTRY_BOUND_FIELDS = (
    "automation_mode",
    "runtime_expected",
    "runtime_owner",
    "max_silence_hours",
    "publish_targets",
    "required_local_gates",
    "post_publish_verification_required",
    "generated_media_of_real_subjects_allowed",
)

# Adapter keys whose value is a path into THIS repository. kernel_doc, kernel_gate,
# acr_runtime_doc and acr_runtime_registry name paths inside the kernel repository
# by convention and are deliberately not in this set. A local declaration that
# points at nothing is worse than no declaration: it reads as configured.
DECLARED_PATH_KEYS = ("acr_client", "acr_registry_vendored")


def declared_path_issues(root: Path, adapter: dict, automation: dict) -> list[str]:
    """Every path the adapter names must exist in this repository."""
    issues = []
    for key in DECLARED_PATH_KEYS:
        raw = adapter.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            issues.append(f"adapter_declared_path_not_string:{key}")
            continue
        if not (root / raw).is_file():
            issues.append(f"adapter_declared_path_missing:{key}:{raw}")
    # required_local_gates are deliberately not checked here: `gate` already
    # reports required_local_gate_missing for them, and a second reporter would
    # pre-empt it with a vaguer error.
    for gate in (automation.get("excluded_gates") or {}):
        if isinstance(gate, str) and gate.strip() and not (root / gate).is_file():
            issues.append(f"adapter_excluded_gate_missing:{gate}")
    return issues


def registry_agreement_issues(root: Path, adapter: dict, automation: dict) -> list[str]:
    """The medium may not quietly disagree with what the kernel declares for it.

    runtime_expected, the silence budget and the required gate list are each one
    edit away from switching monitoring off or dropping a gate, and until now the
    repository was the only thing that decided them. The kernel's registry is
    vendored in byte-identical and pinned, so the row for this repository is the
    kernel's own declaration rather than a local restatement of it.
    """
    issues = []
    if not automation:
        # The kernel repository itself declares no medium, so there is nothing to
        # agree with. Anything carrying an automation block is an ACR-managed
        # medium and must be bound: dropping the block to escape this check would
        # fail every other automation rule first.
        return []
    rel = adapter.get("acr_registry_vendored")
    if not isinstance(rel, str) or not rel.strip():
        return ["adapter_registry_not_vendored"]
    path = root / rel
    if not path.is_file():
        return []  # already reported by declared_path_issues
    pinned = adapter.get("acr_registry_sha256")
    if not pinned:
        issues.append("adapter_registry_sha256_missing")
    elif pinned != sha256_file(path):
        issues.append("vendored_registry_drift")
    try:
        registry = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return issues + [f"runtime_registry_unreadable:{type(exc).__name__}"]

    repository = automation.get("repository")
    row = (registry.get("repositories") or {}).get(repository)
    if not isinstance(row, dict):
        return issues + [f"runtime_registry_row_missing:{repository}"]

    for field in REGISTRY_BOUND_FIELDS:
        if field not in row:
            continue
        if automation.get(field) != row[field]:
            issues.append(
                f"registry_disagreement:{field}:registry={row[field]!r}:adapter={automation.get(field)!r}"
            )
    required = {str(x) for x in (row.get("required_local_gates") or [])}
    for gate in (automation.get("excluded_gates") or {}):
        if str(gate) in required:
            # Excluding a gate the kernel requires is a release-gate removal
            # dressed up as configuration.
            issues.append(f"excluded_gate_is_registry_required:{gate}")
    return issues


def validate_adapter(root: Path):
    adapter, errors = read_adapter(root)
    if adapter is None:
        return None, errors
    for key in REQUIRED_ADAPTER_KEYS:
        if key not in adapter:
            errors.append(f"adapter_missing_key:{key}")
    automation = adapter.get("automation") or {}
    if not isinstance(automation, dict):
        errors.append("adapter_automation_not_object")
        automation = {}
    for key in REQUIRED_AUTOMATION_KEYS:
        if key not in automation:
            errors.append(f"adapter_automation_missing_key:{key}")
    mode = automation.get("automation_mode")
    if mode is not None and mode not in AUTOMATION_MODES:
        errors.append(f"adapter_unknown_automation_mode:{mode}")
    if adapter.get("must_not_fork_kernel") is not True:
        errors.append("adapter_must_not_fork_kernel_not_true")
    if adapter.get("local_release_gates_remain_required") is not True:
        errors.append("adapter_local_release_gates_not_required")
    profiles = adapter.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        errors.append("adapter_profiles_empty")
    default_profile = adapter.get("default_profile")
    if default_profile and isinstance(profiles, list) and default_profile not in profiles:
        errors.append("adapter_default_profile_not_in_profiles")
    silence = automation.get("max_silence_hours")
    if silence is not None and (not isinstance(silence, int) or isinstance(silence, bool) or silence <= 0):
        errors.append("adapter_max_silence_hours_invalid")
    elif isinstance(silence, int) and silence > MAX_SILENCE_HOURS:
        # A silence budget long enough is the same thing as no monitoring, reached
        # by editing one number rather than by declaring the runtime unmonitored.
        errors.append(f"adapter_max_silence_hours_too_long:{silence}>{MAX_SILENCE_HOURS}")
    gates = automation.get("required_local_gates")
    if gates is not None and (not isinstance(gates, list) or not gates):
        errors.append("adapter_required_local_gates_empty")
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, str) or not gate.strip():
                errors.append("adapter_required_local_gate_not_string")
                break
    expected = adapter.get("acr_client_sha256")
    if expected and expected != client_hash():
        errors.append("vendored_client_drift")
    errors += declared_path_issues(root, adapter, automation)
    errors += registry_agreement_issues(root, adapter, automation)

    # The production URL is generated into canonical links, og:url, JSON-LD,
    # sitemap and RSS from the repository's own config, and post-publish
    # verification checks that host. If publish_targets disagrees with it, the
    # runtime is declaring one production site while the build ships another.
    # This has already happened once; a rule stated only in prose is what let it.
    source_value, source_errors = declared_publish_target(root, automation)
    errors.extend(source_errors)
    if source_value:
        targets = automation.get("publish_targets")
        declared = [str(t).strip().rstrip("/") for t in targets] if isinstance(targets, list) else []
        if source_value not in declared:
            errors.append(f"publish_target_drift:{source_value}!={declared}")
    return adapter, errors


# --------------------------------------------------------------------------
# runtime state
# --------------------------------------------------------------------------

def blank_state(adapter) -> dict:
    automation = adapter.get("automation", {})
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kernel_version": adapter.get("required_kernel_version"),
        "repository": automation.get("repository"),
        "profile": adapter.get("default_profile"),
        "automation_mode": automation.get("automation_mode"),
        "runtime_expected": bool(automation.get("runtime_expected")),
        "runtime_owner": automation.get("runtime_owner"),
        "max_silence_hours": automation.get("max_silence_hours"),
        "status": "UNCONFIGURED",
        "paused_reason": None,
        "heartbeat": {"last_seen_at": None, "source": None, "run_url": None},
        "stages": {},
        "last_success_at": None,
        "last_failure_at": None,
        "last_failure_stage": None,
        "last_publish_commit": None,
        "last_published_url": None,
        "last_published_at": None,
        "consecutive_failures": 0,
        "pending_jobs": [],
        "kpi": {
            "window_days": 30,
            "publishes": 0,
            "post_publish_verified": 0,
            "holds": 0,
            "failures": 0,
            "computed_at": None,
        },
    }


def read_state(root: Path):
    path = root / STATE_FILE
    if not path.exists():
        return None, [f"missing_state:{STATE_FILE}"]
    try:
        return load_json(path), []
    except json.JSONDecodeError as exc:
        return None, [f"state_not_json:{exc}"]


def validate_state(state) -> list:
    errors = []
    if not isinstance(state, dict):
        return ["state_not_object"]
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        errors.append(f"state_schema_version_mismatch:{state.get('schema_version')}")
    for key in ("repository", "profile", "automation_mode", "status"):
        if not state.get(key):
            errors.append(f"state_missing:{key}")
    if state.get("automation_mode") not in AUTOMATION_MODES:
        errors.append(f"state_unknown_automation_mode:{state.get('automation_mode')}")
    if state.get("status") not in RUNTIME_STATUSES:
        errors.append(f"state_unknown_status:{state.get('status')}")
    if not isinstance(state.get("runtime_expected"), bool):
        errors.append("state_runtime_expected_not_bool")
    silence = state.get("max_silence_hours")
    if not isinstance(silence, int) or silence <= 0:
        errors.append("state_max_silence_hours_invalid")
    hb = state.get("heartbeat")
    if not isinstance(hb, dict):
        errors.append("state_heartbeat_not_object")
    stages = state.get("stages")
    if not isinstance(stages, dict):
        errors.append("state_stages_not_object")
    else:
        for name, entry in stages.items():
            if not isinstance(entry, dict):
                errors.append(f"state_stage_not_object:{name}")
                continue
            if entry.get("status") not in STAGE_STATUSES:
                errors.append(f"state_stage_status_invalid:{name}")
            if not parse_iso(entry.get("at")):
                errors.append(f"state_stage_timestamp_invalid:{name}")
    if state.get("status") == "PAUSED" and not state.get("paused_reason"):
        errors.append("state_paused_without_reason")
    if state.get("status") != "PAUSED" and state.get("paused_reason"):
        errors.append("state_paused_reason_without_paused_status")
    if not isinstance(state.get("consecutive_failures"), int) or state["consecutive_failures"] < 0:
        errors.append("state_consecutive_failures_invalid")
    if not isinstance(state.get("pending_jobs"), list):
        errors.append("state_pending_jobs_not_list")
    for field in ("last_success_at", "last_failure_at", "last_published_at"):
        value = state.get(field)
        if value and not parse_iso(value):
            errors.append(f"state_timestamp_invalid:{field}")
    return errors


NEVER_RUN = "never_run"


def has_run(state) -> bool:
    """True once the runtime has actually reported something."""
    return bool((state.get("heartbeat") or {}).get("last_seen_at")
                or state.get("last_success_at")
                or state.get("last_failure_at"))


def stale_reason(state, when: datetime):
    """Return a reason string when an expected runtime is not reporting.

    Two very different conditions are deliberately kept apart:

    * NEVER_RUN - the runtime is declared but has never reported. This is the
      state of a freshly installed adapter. It must never be shown as healthy,
      but it must not block the run that would bootstrap it either, or the
      first unattended cycle could never start.
    * heartbeat_stale - the runtime reported before and then went silent past
      its budget. That is a failure.
    """
    if not state.get("runtime_expected"):
        return None
    if state.get("status") == "PAUSED":
        return None
    if not has_run(state):
        return NEVER_RUN
    last = parse_iso((state.get("heartbeat") or {}).get("last_seen_at"))
    if last is None:
        return NEVER_RUN
    limit = int(state.get("max_silence_hours") or 0)
    if limit <= 0:
        return "max_silence_hours_not_configured"
    if when - last > timedelta(hours=limit):
        age = int((when - last).total_seconds() // 3600)
        return f"heartbeat_stale:{age}h>{limit}h"
    return None


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_selfcheck(_args) -> int:
    print(json.dumps({
        "check": "acr.selfcheck",
        "status": "PASS",
        "client_version": CLIENT_VERSION,
        "client_sha256": client_hash(),
        "state_schema_version": STATE_SCHEMA_VERSION,
        "receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "repo_root": str(repo_root()),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_adapter_validate(_args) -> int:
    root = repo_root()
    adapter, errors = validate_adapter(root)
    extra = {}
    if adapter:
        extra = {
            "repository": adapter.get("automation", {}).get("repository"),
            "profile": adapter.get("default_profile"),
            "required_kernel_version": adapter.get("required_kernel_version"),
            "adapter_sha256": canonical_hash(adapter),
        }
    return report("acr.adapter", errors, extra=extra)


def cmd_state_init(args) -> int:
    root = repo_root()
    adapter, errors = validate_adapter(root)
    if errors:
        return report("acr.state-init", errors)
    path = root / STATE_FILE
    if path.exists() and not args.force:
        return report("acr.state-init", [f"state_already_exists:{STATE_FILE}"])
    state = blank_state(adapter)
    state["status"] = "IDLE" if state["runtime_expected"] else "UNCONFIGURED"
    dump_json(path, state)
    return report("acr.state-init", [], extra={"written": STATE_FILE})


def cmd_state_show(_args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.state-show", errors)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_state_validate(_args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.state-validate", errors)
    errors = validate_state(state)
    adapter, adapter_errors = validate_adapter(root)
    errors.extend(adapter_errors)
    if adapter and not adapter_errors:
        automation = adapter.get("automation", {})
        if state.get("repository") != automation.get("repository"):
            errors.append("state_adapter_repository_mismatch")
        if state.get("profile") != adapter.get("default_profile"):
            errors.append("state_adapter_profile_mismatch")
        if state.get("automation_mode") != automation.get("automation_mode"):
            errors.append("state_adapter_mode_mismatch")
        if state.get("max_silence_hours") != automation.get("max_silence_hours"):
            errors.append("state_adapter_silence_mismatch")
    return report("acr.state-validate", errors)


def cmd_heartbeat(args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.heartbeat", errors)
    when = now_utc()
    stamp = iso(when)
    entry = {"status": args.status, "at": stamp, "detail": args.detail or ""}
    if args.run_url:
        entry["run_url"] = args.run_url
    state.setdefault("stages", {})[args.stage] = entry
    state["heartbeat"] = {
        "last_seen_at": stamp,
        "source": args.source or os.environ.get("ACR_SOURCE") or "unknown",
        "run_url": args.run_url or os.environ.get("ACR_RUN_URL"),
    }
    if args.status == "ok":
        state["last_success_at"] = stamp
        state["consecutive_failures"] = 0
        if state.get("status") not in {"PAUSED", "HOLD"}:
            state["status"] = "RUNNING" if args.stage != "cycle_end" else "IDLE"
    elif args.status == "fail":
        state["last_failure_at"] = stamp
        state["last_failure_stage"] = args.stage
        state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
        if state.get("status") != "PAUSED":
            state["status"] = "FAILED"
    elif args.status == "hold":
        if state.get("status") != "PAUSED":
            state["status"] = "HOLD"
    errors = validate_state(state)
    if errors:
        return report("acr.heartbeat", errors)
    dump_json(root / STATE_FILE, state)
    return report("acr.heartbeat", [], extra={"stage": args.stage, "recorded_at": stamp,
                                              "runtime_status": state["status"]})


def cmd_pause(args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.pause", errors)
    state["status"] = "PAUSED"
    state["paused_reason"] = args.reason
    dump_json(root / STATE_FILE, state)
    return report("acr.pause", validate_state(state), extra={"paused_reason": args.reason})


def cmd_resume(_args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.resume", errors)
    state["paused_reason"] = None
    state["status"] = "IDLE"
    dump_json(root / STATE_FILE, state)
    return report("acr.resume", validate_state(state))


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")

RECEIPT_EVIDENCE_KEYS = [
    "source_commit",
    "profile_version",
    "feedback_registry_sha256",
    "research_evidence_sha256",
    "visual_provenance_sha256",
    "local_gate_receipt_sha256",
]


def cmd_receipt(args) -> int:
    root = repo_root()
    adapter, errors = validate_adapter(root)
    if errors:
        return report("acr.receipt", errors)
    if not SLUG_RE.match(args.slug or ""):
        return report("acr.receipt", [f"invalid_slug:{args.slug}"])
    when = now_utc()
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "repository": adapter.get("automation", {}).get("repository"),
        "profile": adapter.get("default_profile"),
        "artifact": {"kind": args.kind, "slug": args.slug, "url": args.url},
        "source_commit": args.source_commit,
        "profile_version": args.profile_version or adapter.get("required_kernel_version"),
        "feedback_registry_sha256": args.feedback_sha,
        "benchmark_registry_sha256": args.benchmark_sha,
        "research_evidence_sha256": args.research_sha,
        "visual_provenance_sha256": args.visual_sha,
        "local_gate_receipt_sha256": args.local_gate_sha,
        "kernel_receipt_sha256": args.kernel_receipt_sha,
        "local_gates_passed": [g for g in (args.gate or []) if g],
        "post_publish_verification": {
            "status": args.verification_status,
            "checked_at": iso(when) if args.verification_status != "PENDING" else None,
            "detail": args.verification_detail or "",
        },
        "created_at": iso(when),
    }
    receipt["receipt_sha256"] = canonical_hash(receipt)
    receipt_id = f"{args.slug}-{receipt['receipt_sha256'][:12]}"
    receipt["receipt_id"] = receipt_id
    dump_json(root / RECEIPT_DIR / f"{receipt_id}.json", receipt)

    index_path = root / RECEIPT_INDEX
    index = load_json(index_path) if index_path.exists() else {"schema_version": RECEIPT_SCHEMA_VERSION, "receipts": []}
    index["receipts"] = [r for r in index.get("receipts", []) if r.get("receipt_id") != receipt_id]
    index["receipts"].append({
        "receipt_id": receipt_id,
        "slug": args.slug,
        "url": args.url,
        "created_at": receipt["created_at"],
        "verification_status": args.verification_status,
        "receipt_sha256": receipt["receipt_sha256"],
    })
    index["receipts"].sort(key=lambda r: (r.get("created_at") or "", r.get("receipt_id") or ""))
    index["updated_at"] = iso(when)
    dump_json(index_path, index)

    state, state_errors = read_state(root)
    if not state_errors:
        state["last_publish_commit"] = args.source_commit
        state["last_published_url"] = args.url
        state["last_published_at"] = receipt["created_at"]
        dump_json(root / STATE_FILE, state)
    return report("acr.receipt", [], warnings=state_errors,
                  extra={"receipt_id": receipt_id, "receipt_sha256": receipt["receipt_sha256"]})


def cmd_verify_receipt(args) -> int:
    root = repo_root()
    path = Path(args.path) if args.path else None
    if path is None:
        index_path = root / RECEIPT_INDEX
        if not index_path.exists():
            return report("acr.verify-receipt", [f"missing_index:{RECEIPT_INDEX}"])
        index = load_json(index_path)
        entries = index.get("receipts", [])
        if not entries:
            return report("acr.verify-receipt", ["no_receipts_recorded"])
        path = root / RECEIPT_DIR / f"{entries[-1]['receipt_id']}.json"
    if not path.exists():
        return report("acr.verify-receipt", [f"missing_receipt:{path}"])
    receipt = load_json(path)
    errors = []
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        errors.append(f"receipt_schema_version_mismatch:{receipt.get('schema_version')}")
    for key in RECEIPT_EVIDENCE_KEYS:
        if not receipt.get(key):
            errors.append(f"receipt_missing_evidence:{key}")
    if not (receipt.get("artifact") or {}).get("url"):
        errors.append("receipt_missing_published_url")
    if not receipt.get("local_gates_passed"):
        errors.append("receipt_no_local_gates_recorded")
    verification = receipt.get("post_publish_verification") or {}
    if args.require_verified and verification.get("status") != "PASS":
        errors.append(f"post_publish_verification_not_pass:{verification.get('status')}")
    stored = receipt.get("receipt_sha256")
    recomputed = canonical_hash({k: v for k, v in receipt.items()
                                 if k not in {"receipt_sha256", "receipt_id"}})
    if stored != recomputed:
        errors.append("receipt_hash_mismatch")
    return report("acr.verify-receipt", errors, extra={"receipt_id": receipt.get("receipt_id")})


def cmd_kpi(_args) -> int:
    root = repo_root()
    state, errors = read_state(root)
    if errors:
        return report("acr.kpi", errors)
    when = now_utc()
    window = int(state.get("kpi", {}).get("window_days") or 30)
    cutoff = when - timedelta(days=window)
    publishes = verified = 0
    index_path = root / RECEIPT_INDEX
    if index_path.exists():
        for entry in load_json(index_path).get("receipts", []):
            created = parse_iso(entry.get("created_at"))
            if created and created >= cutoff:
                publishes += 1
                if entry.get("verification_status") == "PASS":
                    verified += 1
    holds = sum(1 for s in state.get("stages", {}).values() if s.get("status") == "hold")
    failures = sum(1 for s in state.get("stages", {}).values() if s.get("status") == "fail")
    state["kpi"] = {
        "window_days": window,
        "publishes": publishes,
        "post_publish_verified": verified,
        "holds": holds,
        "failures": failures,
        "computed_at": iso(when),
    }
    dump_json(root / STATE_FILE, state)
    return report("acr.kpi", [], extra={"kpi": state["kpi"]})


def cmd_gate(args) -> int:
    """Precondition gate for an unattended run and for CI."""
    root = repo_root()
    errors = []
    warnings = []

    adapter, adapter_errors = validate_adapter(root)
    errors.extend(adapter_errors)

    state, state_errors = read_state(root)
    errors.extend(state_errors)
    if state is not None:
        errors.extend(validate_state(state))

    extra = {}
    if state is not None and not state_errors:
        when = now_utc()
        stale = stale_reason(state, when)
        if stale == NEVER_RUN:
            # Reported, never blocking: a runtime that has never run has to be
            # allowed to run once. The central manifest still refuses to call it
            # healthy, so this cannot be mistaken for a working runtime.
            warnings.append("runtime_never_run")
        elif stale:
            (errors if args.strict else warnings).append(f"runtime_stale:{stale}")
        if state.get("status") == "PAUSED":
            if args.for_run:
                errors.append(f"runtime_paused:{state.get('paused_reason')}")
            else:
                warnings.append(f"runtime_paused:{state.get('paused_reason')}")
        limit = int(args.max_consecutive_failures)
        failures = int(state.get("consecutive_failures", 0))
        if failures >= limit:
            errors.append(f"repeated_failure_hard_block:{failures}>={limit}")
        extra = {
            "repository": state.get("repository"),
            "profile": state.get("profile"),
            "automation_mode": state.get("automation_mode"),
            "runtime_status": state.get("status"),
            "consecutive_failures": failures,
            "last_success_at": state.get("last_success_at"),
            "last_published_url": state.get("last_published_url"),
        }

    if adapter and not adapter_errors:
        for gate in adapter.get("automation", {}).get("required_local_gates", []):
            target = root / gate.split()[0]
            if not target.exists():
                errors.append(f"required_local_gate_missing:{gate}")

    return report("acr.gate", errors, warnings, extra)


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Autonomous Content Runtime client")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selfcheck").set_defaults(func=cmd_selfcheck)
    sub.add_parser("adapter-validate").set_defaults(func=cmd_adapter_validate)

    si = sub.add_parser("state-init")
    si.add_argument("--force", action="store_true")
    si.set_defaults(func=cmd_state_init)

    sub.add_parser("state-show").set_defaults(func=cmd_state_show)
    sub.add_parser("state-validate").set_defaults(func=cmd_state_validate)

    hb = sub.add_parser("heartbeat")
    hb.add_argument("--stage", required=True)
    hb.add_argument("--status", required=True, choices=sorted(STAGE_STATUSES))
    hb.add_argument("--detail")
    hb.add_argument("--source")
    hb.add_argument("--run-url")
    hb.set_defaults(func=cmd_heartbeat)

    pa = sub.add_parser("pause")
    pa.add_argument("--reason", required=True)
    pa.set_defaults(func=cmd_pause)

    sub.add_parser("resume").set_defaults(func=cmd_resume)

    rc = sub.add_parser("receipt")
    rc.add_argument("--kind", default="article")
    rc.add_argument("--slug", required=True)
    rc.add_argument("--url", required=True)
    rc.add_argument("--source-commit", required=True)
    rc.add_argument("--profile-version")
    rc.add_argument("--feedback-sha", required=True)
    rc.add_argument("--benchmark-sha")
    rc.add_argument("--research-sha", required=True)
    rc.add_argument("--visual-sha", required=True)
    rc.add_argument("--local-gate-sha", required=True)
    rc.add_argument("--kernel-receipt-sha")
    rc.add_argument("--gate", action="append")
    rc.add_argument("--verification-status", default="PENDING", choices=["PASS", "FAIL", "PENDING"])
    rc.add_argument("--verification-detail")
    rc.set_defaults(func=cmd_receipt)

    vr = sub.add_parser("verify-receipt")
    vr.add_argument("--path")
    vr.add_argument("--require-verified", action="store_true")
    vr.set_defaults(func=cmd_verify_receipt)

    sub.add_parser("kpi").set_defaults(func=cmd_kpi)

    gt = sub.add_parser("gate")
    gt.add_argument("--strict", action="store_true", help="treat a stale heartbeat as a failure")
    gt.add_argument("--for-run", action="store_true", help="gate an unattended run, not just CI")
    gt.add_argument("--max-consecutive-failures", type=int, default=3)
    gt.set_defaults(func=cmd_gate)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
