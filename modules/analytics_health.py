"""
Health tracking for the analytics feedback loop.

This module keeps notification decisions deterministic and testable. The
workflow owns the actual GitHub Issue calls.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import OUTPUT_DIR

ANALYTICS_DIR = OUTPUT_DIR / "analytics"
ANALYTICS_HEALTH_PATH = ANALYTICS_DIR / "health.json"
LATEST_ANALYTICS_RUN_PATH = ANALYTICS_DIR / "latest_run.json"
ISSUE_TITLE = "Analytics feedback loop needs attention"
PROBLEM_THRESHOLD = 2


def load_latest_run(path: Path = LATEST_ANALYTICS_RUN_PATH) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Latest analytics run must be an object: {path}")
    return data


def save_latest_run(result: dict, path: Path = LATEST_ANALYTICS_RUN_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")


def load_health(path: Path = ANALYTICS_HEALTH_PATH) -> dict:
    if not path.exists():
        return default_health()
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Analytics health must be an object: {path}")
    return data


def save_health(state: dict, path: Path = ANALYTICS_HEALTH_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def default_health() -> dict:
    return {
        "last_checked_at": None,
        "last_status": "unknown",
        "last_error_count": 0,
        "last_problem": False,
        "consecutive_problem_runs": 0,
        "notification_threshold": PROBLEM_THRESHOLD,
        "notification_required": False,
        "recovered": False,
        "problem_summary": "",
    }


def fallback_run_result(workflow_outcome: str) -> dict:
    outcome = (workflow_outcome or "unknown").lower()
    if outcome == "success":
        return {
            "status": "missing_latest_run",
            "errors": ["analytics step succeeded but latest_run.json was not written"],
        }
    return {
        "status": "workflow_failure",
        "errors": [f"analytics workflow step ended with outcome: {workflow_outcome or 'unknown'}"],
    }


def update_health_state(
    run_result: dict,
    workflow_outcome: str = "success",
    previous: dict | None = None,
    now: datetime | None = None,
    threshold: int = PROBLEM_THRESHOLD,
) -> dict:
    current = _coerce_datetime(now) or _utc_now()
    previous = previous or default_health()
    errors = _run_errors(run_result)
    problem = is_problem_run(run_result, workflow_outcome)
    prior_streak = int(previous.get("consecutive_problem_runs", 0) or 0)
    streak = prior_streak + 1 if problem else 0

    return {
        "last_checked_at": current.isoformat(),
        "last_status": str(run_result.get("status") or "unknown"),
        "last_error_count": len(errors),
        "last_problem": problem,
        "consecutive_problem_runs": streak,
        "notification_threshold": threshold,
        "notification_required": problem and streak >= threshold,
        "recovered": bool(previous.get("last_problem")) and not problem,
        "problem_summary": summarize_problem(run_result, workflow_outcome),
    }


def is_problem_run(run_result: dict, workflow_outcome: str = "success") -> bool:
    outcome = (workflow_outcome or "unknown").lower()
    status = str(run_result.get("status") or "unknown").lower()
    if outcome != "success":
        return True
    if status not in {"success", "skipped"}:
        return True
    return bool(_run_errors(run_result))


def summarize_problem(run_result: dict, workflow_outcome: str = "success") -> str:
    errors = _run_errors(run_result)
    if errors:
        return "; ".join(errors[:3])
    outcome = (workflow_outcome or "unknown").lower()
    if outcome != "success":
        return f"analytics workflow step outcome: {workflow_outcome}"
    return ""


def issue_body(health: dict, run_result: dict) -> str:
    errors = _run_errors(run_result)
    lines = [
        "The analytics feedback loop has reported repeated problems.",
        "",
        f"- Status: `{health.get('last_status', 'unknown')}`",
        f"- Consecutive problem runs: `{health.get('consecutive_problem_runs', 0)}`",
        f"- Last checked: `{health.get('last_checked_at', 'unknown')}`",
        f"- Snapshots added: `{run_result.get('snapshots_added', 0)}`",
        f"- Posts seen: `{run_result.get('posts_seen', 0)}`",
    ]
    if errors:
        lines.append("")
        lines.append("Recent errors:")
        lines.extend(f"- {error}" for error in errors[:10])
    lines.append("")
    lines.append("This issue is created by the scheduled Collect Analytics workflow.")
    return "\n".join(lines) + "\n"


def _run_errors(run_result: dict) -> list[str]:
    errors = run_result.get("errors") or []
    if not isinstance(errors, list):
        return [str(errors)]
    return [str(error) for error in errors if error]


def _coerce_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
