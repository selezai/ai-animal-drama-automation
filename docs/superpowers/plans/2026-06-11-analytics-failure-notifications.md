# Analytics Failure Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use systematic-debugging when issues arise, verification-before-completion before claiming success.

**Goal:** Notify the owner through a GitHub Issue only after repeated analytics feedback-loop problems.

**Architecture:** Store lightweight health state in `output/analytics/health.json` and latest run data in `output/analytics/latest_run.json`. A workflow step runs after analytics collection, updates the health streak idempotently, and creates or updates one GitHub Issue when the problem streak reaches the threshold.

**Tech Stack:** Python stdlib for state updates, GitHub Actions, GitHub CLI `gh`, existing repo JSON persistence.

---

### File Structure

- Create `modules/analytics_health.py`: pure functions for reading run data, computing health state, and writing JSON.
- Create `scripts/update_analytics_health.py`: workflow-friendly CLI that updates health state using the analytics step outcome.
- Modify `modules/analytics_collector.py`: write `latest_run.json` whenever collection returns normally.
- Modify `.github/workflows/collect-analytics.yml`: keep the analytics step non-blocking, update health state with `if: always()`, commit analytics health files, and open/update a GitHub Issue after repeated problems.
- Add `tests/test_analytics_health.py`: unit coverage for streak increments, recovery reset, and threshold notification state.
- Modify `ai-animal-drama-technical-setup.md`: record the notification decision.

### Task 1: Health State Module

**Files:**
- Create: `modules/analytics_health.py`
- Test: `tests/test_analytics_health.py`

- [ ] **Step 1: Write failing tests**

```python
def test_health_increments_on_partial_errors():
    result = update_health_state({"status": "partial", "errors": ["fb failed"]}, "success", now=now)
    assert result["consecutive_problem_runs"] == 1
    assert result["notification_required"] is False
```

- [ ] **Step 2: Implement state update**

```python
problem = workflow_outcome != "success" or run_result.get("status") not in {"success", "skipped"} or bool(run_result.get("errors"))
next_streak = previous_streak + 1 if problem else 0
notification_required = next_streak >= 2
```

- [ ] **Step 3: Verify**

Run: `python3 -m unittest tests.test_analytics_health -v`
Expected: all analytics health tests pass.

### Task 2: Collector Latest Run File

**Files:**
- Modify: `modules/analytics_collector.py`
- Test: `tests/test_analytics_collector.py`

- [ ] **Step 1: Add latest-run path support**

```python
latest_run_path: Path = LATEST_ANALYTICS_RUN_PATH
```

- [ ] **Step 2: Save successful/partial collector result**

```python
save_latest_run(result, latest_run_path)
```

- [ ] **Step 3: Verify**

Run: `python3 -m unittest tests.test_analytics_collector -v`
Expected: collector writes `latest_run.json` without duplicating snapshots.

### Task 3: Workflow Notification

**Files:**
- Create: `scripts/update_analytics_health.py`
- Modify: `.github/workflows/collect-analytics.yml`

- [ ] **Step 1: Keep analytics step observable**

```yaml
- name: Collect analytics
  id: collect
  continue-on-error: true
  run: python main.py analytics
```

- [ ] **Step 2: Update health state**

```yaml
- name: Update analytics health
  if: always()
  env:
    ANALYTICS_STEP_OUTCOME: ${{ steps.collect.outcome }}
  run: python scripts/update_analytics_health.py
```

- [ ] **Step 3: Open/update one issue on repeated failures**

```yaml
gh issue list --state open --search "in:title \"Analytics feedback loop needs attention\"" --json number --jq '.[0].number // empty'
```

- [ ] **Step 4: Preserve hard failure behavior**

```yaml
- name: Fail workflow if analytics failed
  if: steps.collect.outcome == 'failure'
  run: exit 1
```

### Task 4: Full Verification

**Files:**
- All changed files

- [ ] **Step 1: Run unit tests**

Run: `python3 -m unittest discover -s tests -p 'test_*.py' -v`
Expected: all tests pass.

- [ ] **Step 2: Run compile/type checks**

Run: `python3 -m compileall main.py modules scripts`
Expected: compile exits 0.

Run: `npx tsc --noEmit -p remotion/tsconfig.json`
Expected: exits 0.

Run: `git diff --check`
Expected: exits 0.
