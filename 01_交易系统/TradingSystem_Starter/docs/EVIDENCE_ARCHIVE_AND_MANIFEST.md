# Evidence Archive and Manifest Convention

## Scope

This document defines the v0.4.0 evidence archive and manifest convention for already generated MT5 evidence.

TASK-099 only defines the schema and external archive convention. It does not implement a parser, does not implement a validator, does not copy external evidence, does not run MT5, does not modify MQ5, does not modify backtest/sets, and does not modify backtest/reports.

## v0.4.0 Evidence Archive Goals

The v0.4.0 evidence archive process is intended to:

- Archive only already generated MT5 evidence.
- Support Strategy Tester HTML reports.
- Support Experts and Journal text logs.
- Support Inputs screenshots.
- Support Tester screenshots.
- Support evidence metadata normalization.
- Support no-trade reproducibility review.

The archive process is an evidence-quality workflow only. It is not a trading workflow.

## Manifest Schema

Each evidence set should be described by a manifest object with the following top-level fields:

- `schemaVersion`: manifest schema version, for example `1`.
- `taskId`: task that produced or reviewed the evidence, for example `TASK-089-RERUN`.
- `evidenceSetId`: stable evidence set identifier.
- `source`: source description, such as external MT5 Strategy Tester output.
- `externalEvidenceRoot`: external directory path where evidence files remain.
- `files[]`: list of evidence files associated with the evidence set.
- `mt5`: MT5 terminal and environment metadata.
- `strategyTester`: Strategy Tester run metadata.
- `expert`: EA metadata.
- `inputs`: relevant input parameter values.
- `noTradeAssertions`: normalized no-trade result assertions.
- `parserExpectations`: expected parser behavior for each evidence type.
- `safetyAssertions`: safety boundaries that must not be inferred or weakened.
- `repositoryState`: repository state when evidence was reviewed.
- `tags`: relevant stable tags and targets.
- `notes`: additional human-readable notes.

### files[]

Each `files[]` item should include at least:

- `fileName`: original evidence file name.
- `relativePath`: path relative to `externalEvidenceRoot`, or repository-relative path if a future task explicitly allows copying.
- `evidenceType`: one of `strategyTesterHtml`, `expertsLog`, `journalLog`, `inputsScreenshot`, `testerScreenshot`, `otherScreenshot`, or `other`.
- `required`: whether this file is required for the evidence set.
- `expectedParser`: expected parser entry, or `none` when the file is not parser-targeted.
- `expectedFields`: fields expected to be extracted from this file.
- `notes`: context, limitations, or reviewer observations.

### mt5

The `mt5` object should include environment metadata such as:

- `terminalPath`: MT5 terminal path, when known.
- `terminalBuild`: MT5 build, when available.
- `platform`: operating system or execution environment.
- `runMode`: manual Strategy Tester, command-line Strategy Tester, or read-only archive review.
- `mt5RunDuringTask`: whether MT5 was run during the current task.

### strategyTester

The `strategyTester` object should include at least:

- `expertName`: EA name, for example `TradingSystem`.
- `symbol`: tested symbol.
- `period`: Strategy Tester chart period.
- `dateFrom`: test start date.
- `dateTo`: test end date.
- `model`: Strategy Tester model.
- `deposit`: initial deposit, when available.
- `leverage`: leverage, when available.

### expert

The `expert` object should include:

- `name`: EA name.
- `version`: EA or project version when available.
- `internalSignalTimeframe`: internal signal timeframe when different from tester period.
- `expectedMode`: expected mode such as no-trade observation.

### inputs

The `inputs` object should include at least:

- `InpEnableTrading`: expected to be `false` for trading-off tests, or explicitly justified when `true`.
- `InpEnableRiskObservation`: expected observation-mode value.
- `InpPrintRuntimeSummary`: whether runtime summary output is expected.
- Log throttle related inputs when available, including:
  - `InpPrintRiskRejectLog`
  - `InpRiskRejectLogEveryN`
  - `InpPrintRiskLogStatsInSummary`
  - `InpEnableNewBarLog`
  - `InpPrintNewBarLog`
  - `InpNewBarLogEveryN`
  - `InpPrintCoreLogStatsInSummary`
  - `InpPrintSignalLog`
  - `InpPrintSignalLogOnlyOnDirectionChange`
  - `InpSignalLogEveryN`
  - `InpPrintSignalLogStatsInSummary`

### noTradeAssertions

The `noTradeAssertions` object should include at least:

- `totalTrades`: expected trade count.
- `totalDeals`: expected deal count.
- `buyTrades`: expected buy trade count.
- `sellTrades`: expected sell trade count.
- `ordersOpened`: expected order-open evidence count or boolean assertion.
- `positionsOpened`: expected position-open evidence count or boolean assertion.
- `orderSendEvidence`: whether `OrderSend` evidence appears.
- `buySellEvidence`: whether `Buy` or `Sell` evidence appears.
- `executionAttempts`: execution attempt count.
- `riskApproved`: risk approval count.

For no-trade smoke evidence, these assertions should normally confirm zero trades, zero deals, zero orders, zero positions, zero buy trades, zero sell trades, no `OrderSend` evidence, no `Buy` / `Sell` evidence, zero execution attempts, and zero risk approvals.

### parserExpectations

The `parserExpectations` object should define expected extraction behavior:

- Strategy Tester HTML parser should extract expert, symbol, period, date range, inputs, trades, deals, buy trades, sell trades, deposit, leverage, and model when present.
- Log parser should extract runtime summary, `riskApproved`, `executionAttempts`, risk rejection summary, and relevant log throttle summary fields.
- Parser should distinguish `TradingSystem` evidence from unrelated EA evidence.
- Parser should not infer live trading readiness.
- Parser should not infer profitability.
- Parser should report missing required fields instead of inventing values.

### safetyAssertions

The `safetyAssertions` object should record:

- `noRealTrading`: must remain true for no-trade evidence sets.
- `noProfitOptimization`: must remain true.
- `noLiveTradingReadinessClaim`: must remain true.
- `noTradingPermissionClaim`: must remain true.
- `noMq5Authorization`: evidence archive review does not authorize MQ5 changes.
- `noBacktestSetAuthorization`: evidence archive review does not authorize backtest/sets changes.
- `noMt5RerunAuthorization`: evidence archive review does not authorize MT5 reruns.

### repositoryState

The `repositoryState` object should include at least:

- `head`: repository HEAD when the evidence was reviewed or synced.
- `stableTag`: relevant stable tag.
- `mq5Changed`: whether MQ5 files changed during the task.
- `backtestSetsChanged`: whether backtest/sets changed during the task.
- `backtestReportsChanged`: whether backtest/reports changed during the task.
- `externalEvidenceCopiedIntoRepo`: whether external evidence was copied into the repository.
- `mt5RunDuringTask`: whether MT5 was run during the task.

### tags

The `tags` object should record:

- `currentStableTag`: current stable tag name.
- `currentStableTagTarget`: target commit for the current stable tag.
- `previousStableTags`: relevant historical stable tag names and targets.
- `tagMoved`: whether any existing tag moved during the task.

### notes

The `notes` field should be used for reviewer context, source limitations, parser limitations, and future task candidates. Notes must not claim validation that did not occur.

## External Evidence Archive Convention

External MT5 evidence may remain outside the repository.

Repository docs may reference external paths and file names as metadata only. The external path should be recorded so the evidence can be found later, but the presence of a path in docs does not mean the files were copied, validated, or archived inside the repository.

No external evidence should be copied into the repository unless a future ChatGPT task explicitly allows it.

External evidence path must be recorded as metadata only.

Evidence file checksums are an optional future enhancement and are not required in TASK-099.

Screenshots and HTML reports are evidence files, not source code.

## v0.5.0 Official Manifest Policy

TASK-114 defines policy only. It does not create `backtest/reports/manifests/`, does not create a manifest, does not create fixtures, does not copy external evidence, does not run MT5, and does not modify parser, generator, validator, MQ5, backtest/sets, or existing backtest reports.

### Official Manifest Storage Policy

The recommended official repository manifest storage directory is:

```text
backtest/reports/manifests/
```

This directory must not be created until a future ChatGPT task explicitly authorizes it. TASK-114 defines the path only.

Directory roles:

- `backtest/reports/generated/` remains reserved for tool-generated reports or temporary generated reports.
- `backtest/reports/samples/` remains reserved for example inputs or sample reports.
- `backtest/reports/manifests/` is reserved for future official repository manifests.

### Official Manifest Naming Convention

Official repository manifests should use this file name format:

```text
{taskId}_{evidenceSetId}_manifest.json
```

Example:

```text
TASK-109_TASK-109-read-only-external-evidence-validation_manifest.json
```

Naming constraints:

- `taskId` must match `TASK-\d+`.
- `evidenceSetId` must use ASCII-safe characters.
- `evidenceSetId` may contain `a-z`, `A-Z`, `0-9`, hyphen, underscore, and dot.
- Spaces are not allowed.
- Non-ASCII or localized path names must not be used as part of the manifest file name.
- Absolute paths must not be used as file names.
- Existing manifest files must not be overwritten.
- Multiple manifests must not point to the same `evidenceSetId` unless a future task explicitly marks a revision.

### Manifest Revision and Version Policy

- `schemaVersion` identifies the manifest schema version.
- `manifestRevision` may identify an archive revision for the same `evidenceSetId` if a future schema supports that field.
- The current schema does not require `manifestRevision`.
- Until `manifestRevision` is added by an explicit future task, official manifests should use `schemaVersion`, `taskId`, and `evidenceSetId` as the primary identity.
- `schemaVersion` upgrades must be authorized by an independent task.
- `schemaVersion` upgrades must update the validator, self-test, and generator together.
- Schema meaning must not be changed silently.

### Metadata-Only External Evidence Reference Policy

- External evidence must not be copied into the repository by default.
- Manifest `files[]` should record metadata fields such as `fileName`, `relativePath`, `evidenceType`, `expectedParser`, `expectedFields`, and `notes`.
- `externalEvidenceRoot` records an external root path string. It must not be treated as a repository file.
- `repositoryState.externalEvidenceCopiedIntoRepo` must be `false` unless a future ChatGPT task explicitly authorizes copying evidence.
- Copying evidence requires a separately defined sanitization, retention, and privacy policy.

### Evidence Sanitization Policy Placeholder

No evidence sanitization is performed by TASK-114.

No real evidence is copied by TASK-114.

Before any future task copies evidence into the repository, that task must define:

- Which evidence file types may be copied.
- Whether account number, broker name, terminal path, or local user name must be removed.
- Whether logs must be truncated.
- Whether hashes or checksums are required.
- Whether original file encoding must be preserved.
- How the sanitization method must be recorded.

Evidence must not be copied before sanitization policy is defined and explicitly authorized.

### Official Manifest Creation Boundary

TASK-114 does not create an official manifest.

Future official manifest creation must be explicitly authorized by ChatGPT. Such a task must confirm:

- `repositoryState.externalEvidenceCopiedIntoRepo=false`, unless evidence copying is explicitly authorized.
- `repositoryState.mt5RunDuringTask=false`, unless an MT5 run is explicitly authorized.
- `safetyAssertions.noRealTrading=true`.
- `safetyAssertions.noProfitOptimization=true`.
- `safetyAssertions.noLiveTradingReadinessClaim=true`.
- `safetyAssertions.noRealTradingAllowedClaim=true`.
- `safetyAssertions.noProfitabilityClaim=true`.

### First Official Manifest Dry-Run Boundary

TASK-123 defines the first official manifest dry-run boundary only.

The first official manifest dry-run is a temporary reproducibility and policy-check workflow. It does not create an official repository manifest, does not create `backtest/reports/manifests/`, does not create fixtures, does not copy external evidence, does not run MT5, and does not authorize real trading or profit optimization.

The dry-run boundary is:

- Dry-run may generate a manifest only in a temporary directory.
- Dry-run must not create an official repository manifest.
- Dry-run must not create `backtest/reports/manifests/`.
- Dry-run must not create a repository fixture.
- Dry-run must not copy external evidence.
- Dry-run must not run MT5.
- Dry-run must use existing external evidence metadata references only.
- Dry-run must use `generate_evidence_manifest.py`.
- Dry-run must use `validate_evidence_manifest_schema.py`.
- Dry-run must use `validate_official_manifest_path_policy.py` to validate the future official manifest path and naming policy.
- Dry-run must use `task_acceptance_report.ps1` for local task acceptance.
- Dry-run artifacts must be cleaned before the task ends.
- Dry-run output must not be treated as an official archive.

The dry-run does not mean:

- It does not mean an official archive has been created.
- It does not mean live trading readiness.
- It does not mean real trading availability.
- It does not mean profitability.
- It does not authorize real trading.
- It does not authorize copying evidence.
- It does not authorize repository manifest creation.
- It does not authorize creating `backtest/reports/manifests/`.
- It does not authorize creating fixtures.
- It does not authorize running MT5.

### First Official Manifest Creation Authorization Boundary

TASK-137 defines the first official manifest creation authorization boundary only.

This task is a policy boundary definition. It does not create an official manifest, does not create `backtest/reports/manifests/`, does not create fixtures, does not copy external evidence, does not run MT5, does not authorize real trading, and does not perform profit optimization.

First official manifest creation must be separately authorized by a future explicit ChatGPT task. Until that task exists, the repository must continue to have no official repository manifest and `backtest/reports/manifests/` must remain uncreated.

Before any future first official manifest creation task writes an official manifest, it must:

- Pass `validate_official_manifest_path_policy.py`.
- Use the official naming convention:

```text
{taskId}_{evidenceSetId}_manifest.json
```

- Use `backtest/reports/manifests/` as the official manifest directory.
- Use `generate_evidence_manifest.py` to assemble the manifest.
- Use `validate_evidence_manifest_schema.py` to validate the generated manifest.
- Use `validate_official_manifest_path_policy.py` to validate the future official manifest path and name.
- Use `task_acceptance_report.ps1` for local task acceptance.
- Record `repositoryState`.
- Record `tags`.
- Record `files[]` as metadata-only external evidence references.
- Keep `repositoryState.externalEvidenceCopiedIntoRepo=false`.
- Keep `repositoryState.mt5RunDuringTask=false`, unless a future task explicitly authorizes an MT5 run.
- Keep `safetyAssertions.noRealTrading=true`.
- Keep `safetyAssertions.noProfitOptimization=true`.
- Keep `safetyAssertions.noLiveTradingReadinessClaim=true`.
- Keep `safetyAssertions.noRealTradingAllowedClaim=true`.
- Keep `safetyAssertions.noProfitabilityClaim=true`.

A future first official manifest creation task must not:

- Copy external evidence into the repository.
- Claim live trading readiness.
- Claim real trading availability.
- Claim profitability.
- Authorize real trading.
- Authorize profit optimization.
- Weaken or bypass risk controls.
- Modify MQ5 unless a future task explicitly authorizes it.
- Modify `backtest/sets` unless a future task explicitly authorizes it.

The current v0.5.12 stable tag means only that the first official manifest promotion readiness audit is closed. It does not mean an official manifest has been created.

Current state remains:

- v0.5.12 only represents promotion readiness audit closure.
- v0.5.12 does not represent official repository manifest creation.
- No official repository manifest exists.
- `backtest/reports/manifests/` is still not created.
- First official manifest creation still requires a future explicit ChatGPT task.
- Evidence copying still requires future explicit authorization and a sanitization / retention / privacy policy.
- Official manifest creation does not authorize real trading.
- Official manifest creation does not prove profitability.

### Reproducibility Checklist Placeholder

A future official manifest should record:

- `HEAD`
- `stableTag`
- `taskId`
- `evidenceSetId`
- `externalEvidenceRoot`
- `files[]`
- Parser tools used.
- Parser outputs summary.
- `noTradeAssertions`
- `safetyAssertions`
- `repositoryState`
- `tags`
- `notes`

### Safety Statements

- v0.5.0 does not represent live trading readiness.
- v0.5.0 does not represent real trading availability.
- v0.5.0 does not represent profitable strategy completion.
- Official manifest does not prove profitability.
- Official manifest does not authorize real trading.
- Evidence archive policy does not authorize MT5 run.
- No `OrderSend` / `Buy` / `Sell` / `CTrade` / `PositionOpen` / `PositionClose` / `OrderModify` / `OrderClose`.

## Parser Quality Expectations

Future parser-quality work should follow these expectations:

- Strategy Tester HTML parser should extract expert, symbol, period, date range, inputs, trades/deals stats, deposit, leverage, and model when present.
- Log parser should extract runtime summary, `riskApproved`, `executionAttempts`, risk rejection summary, and log throttle summaries.
- Parser should distinguish `TradingSystem` evidence from unrelated EA evidence.
- Parser should not infer live trading readiness.
- Parser should not infer real trading permission.
- Parser should not infer profitability.
- Parser should preserve unknown or missing fields as missing, not fabricated.
- Parser output should make no-trade evidence reproducibility review easier.

## Forbidden Interpretations

The evidence manifest does not mean live trading readiness.

The evidence manifest does not mean real trading is allowed.

The evidence manifest does not mean profitable strategy completion.

The evidence archive does not authorize MT5 reruns.

The evidence archive does not authorize MQ5 changes.

The evidence archive does not authorize backtest/sets changes.

The evidence archive does not authorize parser implementation unless a future ChatGPT task explicitly allows it.

The evidence archive does not authorize validator implementation unless a future ChatGPT task explicitly allows it.

## Example Manifest Skeleton

The following skeleton is example only. It is not an actual archived evidence file, not a validation result, and not copied external evidence.

```json
{
  "schemaVersion": 1,
  "taskId": "TASK-EXAMPLE",
  "evidenceSetId": "example-no-trade-smoke",
  "source": "external MT5 Strategy Tester evidence",
  "externalEvidenceRoot": "E:\\\\GPT\\\\MT5-test\\\\Journal Experts Tester",
  "files": [
    {
      "fileName": "TesterBacktest.html",
      "relativePath": "TesterBacktest.html",
      "evidenceType": "strategyTesterHtml",
      "required": true,
      "expectedParser": "future_strategy_tester_html_parser",
      "expectedFields": [
        "expertName",
        "symbol",
        "period",
        "dateFrom",
        "dateTo",
        "totalTrades",
        "totalDeals"
      ],
      "notes": "Example only; not copied external evidence."
    },
    {
      "fileName": "log.txt",
      "relativePath": "log.txt",
      "evidenceType": "expertsLog",
      "required": true,
      "expectedParser": "future_log_parser",
      "expectedFields": [
        "runtimeSummary",
        "riskApproved",
        "executionAttempts",
        "riskRejected"
      ],
      "notes": "Example only; not a validation result."
    }
  ],
  "mt5": {
    "terminalPath": "D:\\\\MT5-test\\\\MetaTrader 5\\\\terminal64.exe",
    "terminalBuild": null,
    "platform": "Windows",
    "runMode": "manual Strategy Tester",
    "mt5RunDuringTask": false
  },
  "strategyTester": {
    "expertName": "TradingSystem",
    "symbol": "EURUSD",
    "period": "M5",
    "dateFrom": "2024-01-01",
    "dateTo": "2024-01-31",
    "model": "Every tick based on real ticks",
    "deposit": null,
    "leverage": null
  },
  "expert": {
    "name": "TradingSystem",
    "version": null,
    "internalSignalTimeframe": "PERIOD_M5",
    "expectedMode": "no-trade observation"
  },
  "inputs": {
    "InpEnableTrading": false,
    "InpEnableRiskObservation": true,
    "InpPrintRuntimeSummary": true,
    "InpPrintRiskRejectLog": null,
    "InpRiskRejectLogEveryN": null,
    "InpPrintRiskLogStatsInSummary": null,
    "InpEnableNewBarLog": null,
    "InpPrintNewBarLog": null,
    "InpNewBarLogEveryN": null,
    "InpPrintCoreLogStatsInSummary": null,
    "InpPrintSignalLog": null,
    "InpPrintSignalLogOnlyOnDirectionChange": null,
    "InpSignalLogEveryN": null,
    "InpPrintSignalLogStatsInSummary": null
  },
  "noTradeAssertions": {
    "totalTrades": 0,
    "totalDeals": 0,
    "buyTrades": 0,
    "sellTrades": 0,
    "ordersOpened": 0,
    "positionsOpened": 0,
    "orderSendEvidence": false,
    "buySellEvidence": false,
    "executionAttempts": 0,
    "riskApproved": 0
  },
  "parserExpectations": {
    "strategyTesterHtml": [
      "extract expert, symbol, period, date range, inputs, trades/deals stats",
      "do not infer live trading readiness",
      "do not infer profitability"
    ],
    "logs": [
      "extract runtime summary",
      "extract riskApproved and executionAttempts",
      "extract risk rejection summary"
    ]
  },
  "safetyAssertions": {
    "noRealTrading": true,
    "noProfitOptimization": true,
    "noLiveTradingReadinessClaim": true,
    "noTradingPermissionClaim": true,
    "noMq5Authorization": true,
    "noBacktestSetAuthorization": true,
    "noMt5RerunAuthorization": true
  },
  "repositoryState": {
    "head": "example-only",
    "stableTag": "example-only",
    "mq5Changed": false,
    "backtestSetsChanged": false,
    "backtestReportsChanged": false,
    "externalEvidenceCopiedIntoRepo": false,
    "mt5RunDuringTask": false
  },
  "tags": {
    "currentStableTag": "example-only",
    "currentStableTagTarget": "example-only",
    "previousStableTags": [],
    "tagMoved": false
  },
  "notes": [
    "Example only.",
    "Not an actual archived evidence file.",
    "Not a validation result.",
    "Not copied external evidence."
  ]
}
```
