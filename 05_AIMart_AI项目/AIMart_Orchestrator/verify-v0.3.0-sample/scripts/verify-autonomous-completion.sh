#!/usr/bin/env bash
set +e
TARGET_VERSION="${1:-}"
if [ -z "$TARGET_VERSION" ]; then
  TARGET_VERSION="v$(node -e "const p=require('./package.json'); process.stdout.write(p.version)")"
fi
case "$TARGET_VERSION" in v*) ;; *) TARGET_VERSION="v$TARGET_VERSION" ;; esac
REPORT_DIR="codex_runs"
mkdir -p "$REPORT_DIR"
REPORT_PATH="$REPORT_DIR/verify-autonomous-completion-$TARGET_VERSION.md"
RESULT_LINES=()
FAIL_COUNT=0
add_result() {
  local gate="$1" status="$2" details="$3"
  RESULT_LINES+=("| $gate | $status | $details |")
  [ "$status" = "FAIL" ] && FAIL_COUNT=$((FAIL_COUNT + 1))
}
run_command_gate() {
  local gate="$1"; shift
  echo "[Autonomous Completion Gate] $gate"
  "$@"
  local code=$?
  if [ "$code" -eq 0 ]; then add_result "$gate" "PASS" "exit 0"; else add_result "$gate" "FAIL" "exit $code"; fi
}
run_script_gate() {
  local gate="$1" script="$2"
  bash "scripts/$script" "$TARGET_VERSION"
  local code=$?
  if [ "$code" -eq 0 ]; then add_result "$gate" "PASS" "ok"; else add_result "$gate" "FAIL" "exit $code"; fi
}
run_command_gate "pnpm test" pnpm test
run_command_gate "pnpm lint" pnpm lint
run_command_gate "pnpm build" pnpm build
run_script_gate "verify-release" "verify-release.sh"
run_script_gate "verify-source-zip" "verify-source-zip.sh"
run_script_gate "verify-sample-pack" "verify-sample-pack.sh"
run_script_gate "verify-history-releases" "verify-history-releases.sh"
for path in IMPLEMENTATION_REPORT.md RELEASE_NOTES.md FINAL_DELIVERY_CHECK.md V0.3.0_IMPLEMENTATION_REPORT.md V0.3.0_RELEASE_NOTES.md V0.3.0_FINAL_DELIVERY_CHECK.md V0.3.0_KNOWN_ISSUES.md; do
  [ -f "$path" ] && add_result "final delivery document $path" "PASS" "exists" || add_result "final delivery document $path" "FAIL" "missing"
done
GIT_STATUS="$(git status --short --branch 2>&1 | tr '\n' ';')"
add_result "git status" "PASS" "$GIT_STATUS"
HEAD_COMMIT="$(git rev-parse HEAD 2>/dev/null)"
TAG_COMMIT="$(git rev-parse "$TARGET_VERSION" 2>/dev/null)"
if [ -n "$HEAD_COMMIT" ] && [ "$HEAD_COMMIT" = "$TAG_COMMIT" ]; then
  add_result "target version tag" "PASS" "$TARGET_VERSION -> $HEAD_COMMIT"
else
  add_result "target version tag" "FAIL" "$TARGET_VERSION does not point to HEAD"
fi
if [ "$FAIL_COUNT" -eq 0 ]; then FINAL="PASS"; else FINAL="FAIL"; fi
{
  echo "# Autonomous Completion Gate Report"
  echo
  echo "TargetVersion: $TARGET_VERSION"
  echo
  echo "| Gate | Status | Details |"
  echo "|---|---|---|"
  printf "%s\n" "${RESULT_LINES[@]}"
  echo
  echo "Final result: $FINAL"
} > "$REPORT_PATH"
echo "[Autonomous Completion Gate] $FINAL report=$REPORT_PATH"
[ "$FINAL" = "PASS" ]