# v8.67 Month-Cluster Mitigation Plan

Generated: 2026-06-20 17:21:23 +08:00

Evidence: E:\CODEXMACD\HCSJ\matrix\production_readiness\v867_month_cluster_abcd_summary_20260620_170142.md

## Problem

- A/B/C/D share the same weak profile in selected losing-month clusters: 7 profitable active months out of 23 active months, plus 1 no-trade month.
- This is structural behavior of the current signal family, not an isolated B parameter accident.

## Constraints

- Do not modify EA source during the current unattended testing phase.
- Do not promote real-money live while this remains unmitigated.
- Keep v8.67/v8.66 robust main as the demo/forward candidate only.

## Mitigation Options For Next Development Iteration

| option | change type | expected benefit | risk | recommendation |
|---|---|---|---|---|
| Monthly exposure governor | risk layer / schedule-aware reduction | lower damage during known weak regimes | may reduce profit in recovery months | evaluate first in simulation |
| Volatility regime filter | entry filter | avoid low-quality chop clusters | can reduce trade count and profit anchor | test as optional input only |
| Drawdown cooldown after cluster-like losses | risk layer | stop cascading losses | may delay re-entry | low-risk first candidate |
| Parameter micro-ensemble B/D | set-level selection | balance robust vs conservative exposure | operational complexity | demo-only trial, not live |
| No change, monitor only | operations | preserves profit anchor | accepts known cluster drawdown | acceptable only for demo/forward |

## Proposed Next Test Before Source Changes

1. Build a no-source-change set comparison for B vs D on the same month cluster plus recent 2024-2026 windows.
2. If D lowers loss without excessive profit loss, consider a risk-layer rule in the next EA version.
3. If D does not materially improve cluster damage, source-level regime detection is required before live promotion.

## Current Decision

Keep Level 2 demo/forward. Do not approve real-money live.