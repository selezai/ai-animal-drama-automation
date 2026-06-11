#!/usr/bin/env python3
"""
Update analytics health state for the Collect Analytics workflow.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.analytics_health import (
    ANALYTICS_HEALTH_PATH,
    ISSUE_TITLE,
    LATEST_ANALYTICS_RUN_PATH,
    fallback_run_result,
    issue_body,
    load_health,
    load_latest_run,
    save_health,
    update_health_state,
)


def main() -> None:
    workflow_outcome = os.getenv("ANALYTICS_STEP_OUTCOME", "success")
    latest_run_path = Path(os.getenv("LATEST_ANALYTICS_RUN_PATH", str(LATEST_ANALYTICS_RUN_PATH)))
    health_path = Path(os.getenv("ANALYTICS_HEALTH_PATH", str(ANALYTICS_HEALTH_PATH)))
    body_path = Path(os.getenv("ANALYTICS_ISSUE_BODY_PATH", str(Path(tempfile.gettempdir()) / "analytics_issue_body.md")))

    run_result = load_latest_run(latest_run_path) if latest_run_path.exists() else fallback_run_result(workflow_outcome)
    previous = load_health(health_path)
    health = update_health_state(run_result, workflow_outcome=workflow_outcome, previous=previous)
    save_health(health, health_path)

    body_path.write_text(issue_body(health, run_result))
    _write_github_output({
        "notification_required": _bool_string(health["notification_required"]),
        "recovered": _bool_string(health["recovered"]),
        "consecutive_problem_runs": str(health["consecutive_problem_runs"]),
        "last_problem": _bool_string(health["last_problem"]),
        "issue_title": ISSUE_TITLE,
        "issue_body_path": str(body_path),
    })
    _write_step_summary(health, run_result)
    print(json.dumps(health, indent=2))


def _write_github_output(values: dict[str, str]) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")


def _write_step_summary(health: dict, run_result: dict) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a") as f:
        f.write("## Analytics Health\n\n")
        f.write(f"- Status: `{health.get('last_status')}`\n")
        f.write(f"- Consecutive problem runs: `{health.get('consecutive_problem_runs')}`\n")
        f.write(f"- Notification required: `{_bool_string(health.get('notification_required'))}`\n")
        f.write(f"- Recovered: `{_bool_string(health.get('recovered'))}`\n")
        f.write(f"- Posts seen: `{run_result.get('posts_seen', 0)}`\n")
        f.write(f"- Snapshots added: `{run_result.get('snapshots_added', 0)}`\n")


def _bool_string(value: object) -> str:
    return "true" if bool(value) else "false"


if __name__ == "__main__":
    main()
