# v8.67 Unattended 3h Scope - 2026-06-19

## Goal

Use the unattended window to make measurable progress after B/C `wf20/wf12` and `slippage` validation.

## Non-goals

- Do not claim true `spread` validation unless a real spread-control path is proven.
- Do not edit EA trading logic.
- Do not delete existing MT5 reports or archives.
- Do not promote C above B without deeper evidence.

## Work queue

1. Document real spread-test feasibility.
2. Add `quarter` support to the runner if it can reuse the existing archive/matrix discipline.
3. Run B/C quarter validation on fixed candidates.
4. Generate a combined quarter report.
5. Append `WORK_LOG.md`.

## Stop conditions

- Any MT5 no-report failure in two consecutive quarter cases.
- Any zero-trade quarter.
- Any missing five-piece archive after a completed run.
- `terminal64.exe` remains running after timeout cleanup.
- Any required path or base `.set` file is missing.

## Decision frame

- B remains current mainline unless a later report explicitly proves otherwise.
- C remains equal-depth challenger.
- If quarter shows concentration risk, stop before month-level expansion.
