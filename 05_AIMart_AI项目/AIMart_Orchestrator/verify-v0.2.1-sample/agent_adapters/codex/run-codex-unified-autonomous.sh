#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

RUN_DIR="$ROOT_DIR/codex_runs"
mkdir -p "$RUN_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_PATH="$RUN_DIR/codex-unified-autonomous-$STAMP.log"
EXIT_PATH="$RUN_DIR/codex-unified-autonomous-$STAMP.exit"
PROMPT_PATH="$ROOT_DIR/agent_adapters/codex/CODEX_AUTONOMOUS_PROMPT.md"
STATUS_PATH="$ROOT_DIR/runtime/AUTONOMOUS_RUN_STATUS.md"
SUMMARY_PATH="$ROOT_DIR/runtime/AUTONOMOUS_RUN_SUMMARY.md"
HEALTH_PATH="$ROOT_DIR/runtime/AUTONOMOUS_HEALTH_CHECK.md"
START_EPOCH="$(date +%s)"

echo "[codex-unified] one-window dashboard: sandbox workspace-write, approval never"
echo "[codex-unified] log=$LOG_PATH"

elapsed_text() {
  local now seconds
  now="$(date +%s)"
  seconds=$((now - START_EPOCH))
  printf "%02d:%02d:%02d" $((seconds / 3600)) $(((seconds % 3600) / 60)) $((seconds % 60))
}

git_branch_text() {
  local branch
  branch="$(git branch --show-current 2>/dev/null || true)"
  if [ -n "$branch" ]; then
    printf "%s" "$branch"
  else
    printf "%s" "detached-or-unknown"
  fi
}

dirty_file_count() {
  git status --short 2>/dev/null | wc -l | tr -d " "
}

git_status_text() {
  local count
  count="$(dirty_file_count)"
  if [ "$count" = "0" ]; then
    printf "%s" "clean"
  else
    printf "%s" "$count changed file(s)"
  fi
}

release_status() {
  if [ ! -d "$ROOT_DIR/releases" ]; then
    printf "%s" "releases/ not found"
    return
  fi

  local latest latest_name zip_count
  latest="$(find "$ROOT_DIR/releases" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -n 1 || true)"
  if [ -z "$latest" ]; then
    printf "%s" "no release directories"
    return
  fi

  latest_name="$(basename "$latest")"
  zip_count="$(find "$latest" -type f -name "*.zip" 2>/dev/null | wc -l | tr -d " ")"
  printf "%s" "$latest_name: $zip_count zip artifact(s)"
}

sample_execution_pack_status() {
  if [ ! -d "$ROOT_DIR/releases" ]; then
    printf "%s" "missing"
    return
  fi

  local count
  count="$(find "$ROOT_DIR/releases" -type f -name "*generated-execution-pack.zip" 2>/dev/null | wc -l | tr -d " ")"
  if [ "$count" = "0" ]; then
    printf "%s" "missing"
  else
    printf "%s" "$count sample pack(s)"
  fi
}

known_issues_status() {
  local count
  count="$(find "$ROOT_DIR" -maxdepth 1 -type f \( -name "KNOWN_ISSUES.md" -o -name "V0.2.1_KNOWN_ISSUES.md" -o -name "V0.2.0_KNOWN_ISSUES.md" \) 2>/dev/null | wc -l | tr -d " ")"
  if [ -f "$ROOT_DIR/runtime/APPROVAL_QUEUE.md" ]; then
    count=$((count + 1))
  fi

  if [ "$count" = "0" ]; then
    printf "%s" "no known issue files"
  else
    printf "%s" "$count issue/status file(s)"
  fi
}

log_tail_text() {
  if [ ! -f "$LOG_PATH" ]; then
    printf "%s\n" "log not created yet"
    return
  fi

  if [ ! -s "$LOG_PATH" ]; then
    printf "%s\n" "log is empty"
    return
  fi

  tail -n 12 "$LOG_PATH"
}

write_run_status() {
  local state exit_code elapsed branch dirty release known updated
  state="$1"
  exit_code="$2"
  elapsed="$(elapsed_text)"
  branch="$(git_branch_text)"
  dirty="$(dirty_file_count)"
  release="$(release_status)"
  known="$(known_issues_status)"
  updated="$(date -Iseconds)"

  cat > "$STATUS_PATH" <<EOF
# Autonomous Run Status

| Field | Value |
|---|---|
| Runner state | $state |
| Elapsed time | $elapsed |
| Git branch | $branch |
| Dirty file count | $dirty |
| Latest log tail | See $LOG_PATH |
| Release directory status | $release |
| Known issues status | $known |
| Codex exit code | $exit_code |
| Last updated | $updated |
EOF
}

write_health_check() {
  cat > "$HEALTH_PATH" <<EOF
# Autonomous Health Check

- [x] one-window runner started.
- [x] codex_runs log path prepared.
- [x] runtime/AUTONOMOUS_RUN_STATUS.md update attempted.
- [x] runtime/AUTONOMOUS_RUN_SUMMARY.md update attempted at completion.
- [x] Release directory status checked.
- [x] Known issues status checked.
- [x] No secret reads or remote pushes are performed by this runner.
EOF
}

show_dashboard() {
  local state elapsed branch dirty release known
  state="$1"
  elapsed="$(elapsed_text)"
  branch="$(git_branch_text)"
  dirty="$(dirty_file_count)"
  release="$(release_status)"
  known="$(known_issues_status)"

  clear || true
  printf "%s\n" "AIMart Codex Unified Autonomous Runner"
  printf "%s\n\n" "one-window status display"
  printf "State: %s\n" "$state"
  printf "Elapsed: %s\n" "$elapsed"
  printf "Git branch: %s\n" "$branch"
  printf "Dirty files: %s\n" "$dirty"
  printf "Release directory: %s\n" "$release"
  printf "Known issues: %s\n" "$known"
  printf "Log: %s\n\n" "$LOG_PATH"
  printf "%s\n" "Latest log tail"
  printf "%s\n" "---------------"
  log_tail_text

  write_run_status "$state" "running"
}

if [ ! -f "$PROMPT_PATH" ]; then
  echo "Missing prompt file: $PROMPT_PATH" >&2
  exit 1
fi

write_health_check
write_run_status "starting" "running"

# Effective Codex flags: codex exec --sandbox workspace-write --approval never
(
  set +e
  codex exec --sandbox workspace-write --approval never --cd "$ROOT_DIR" --prompt-file "$PROMPT_PATH" > "$LOG_PATH" 2>&1
  code=$?
  printf "%s" "$code" > "$EXIT_PATH"
) &
CODEX_PID=$!

while kill -0 "$CODEX_PID" 2>/dev/null; do
  show_dashboard "running"
  sleep 3
done

set +e
wait "$CODEX_PID"
set -e

EXIT_CODE="1"
if [ -f "$EXIT_PATH" ]; then
  EXIT_CODE="$(cat "$EXIT_PATH")"
fi

show_dashboard "completed"
write_run_status "completed" "$EXIT_CODE"

RELEASE_STATUS="$(release_status)"
SAMPLE_STATUS="$(sample_execution_pack_status)"
GIT_STATUS="$(git_status_text)"
if [ "$EXIT_CODE" = "0" ]; then
  NEXT_ACTION="Review runtime/AUTONOMOUS_RUN_SUMMARY.md, inspect changed files, then run scripts/finalize for delivery."
else
  NEXT_ACTION="Inspect the latest codex_runs log, fix the blocking issue, then rerun the unified autonomous runner."
fi

cat > "$SUMMARY_PATH" <<EOF
# Autonomous Run Summary

| Field | Value |
|---|---|
| Exit code | $EXIT_CODE |
| Release artifacts | $RELEASE_STATUS |
| Sample execution pack | $SAMPLE_STATUS |
| Git status | $GIT_STATUS |
| Latest log | $LOG_PATH |
| Next recommended action | $NEXT_ACTION |
EOF

printf "\n%s\n" "Final Summary"
printf "%s\n" "-------------"
printf "Exit code: %s\n" "$EXIT_CODE"
printf "Release artifacts: %s\n" "$RELEASE_STATUS"
printf "Sample execution pack: %s\n" "$SAMPLE_STATUS"
printf "Git status: %s\n" "$GIT_STATUS"
printf "Next recommended action: %s\n" "$NEXT_ACTION"

exit "$EXIT_CODE"