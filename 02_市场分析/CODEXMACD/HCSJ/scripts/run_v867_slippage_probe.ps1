param()
$ErrorActionPreference='Stop'

$root = 'E:\CODEXMACD'
. "$root\HCSJ\scripts\robust_search_runner.ps1"

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path $root 'HCSJ\matrix\production_readiness'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$summaryCsv = Join-Path $outDir "slippage_probe_v867_$timestamp.csv"
$summaryMd = Join-Path $outDir "slippage_probe_v867_$timestamp.md"

$source = Join-Path $root 'SniperTrendEA_v8.67_grokbase_production_ready.mq5'
$expert = 'SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5'
$ex5 = Join-Path 'D:\MT5测试\MetaTrader 5\MQL5\Experts' $expert
$setPath = Join-Path $root 'HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set'

$windows = @(
    [pscustomobject]@{ label='S2012_2019'; from='2012.01.01'; to='2019.12.31'; window='2012-2019' },
    [pscustomobject]@{ label='S2020_2026'; from='2020.01.01'; to='2026.06.30'; window='2020-2026' }
)

$probes = @(
    @{ key='Slippage'; value='3'; notes='candidate slippage field' },
    @{ key='Deviation'; value='3'; notes='candidate deviation field' }
)

$rows=@()
$case=1
foreach($p in $probes){
    foreach($w in $windows){
        $runId = "v867_slippage_probe_$($timestamp.Replace('_',''))_$($p.key)_$($w.label)_case$('{0:d4}' -f $case)"
        $notes = "slippage probe key=$($p.key) value=$($p.value) window=$($w.window)"
        $r = Invoke-Mt5Backtest `
            -RunId $runId `
            -Version 'v8.67' `
            -Window $w.window `
            -Stage 'slippage_probe' `
            -Round 1 `
            -CaseId $case `
            -SourceFile $source `
            -ExpertFileName $expert `
            -Ex5File $ex5 `
            -BaseSet $setPath `
            -Overrides @{} `
            -FromDate $w.from `
            -ToDate $w.to `
            -CandidateClass 'slippage_probe_v867' `
            -Decision 'v8.67-slippage' `
            -Notes $notes `
            -ConfigOverrides @{$($p.key)=$($p.value)} `
            -TimeoutSeconds 1200

        $metric = if (Test-Path $r.Metrics) { Import-Csv -Path $r.Metrics | Select-Object -First 1 } else { $null }

        $rows += [pscustomobject]@{
            run_id = $r.RunId
            field = $p.key
            value = $p.value
            window = $w.window
            status = $r.Status
            net_profit = if($metric){ $metric.net_profit } else { '' }
            profit_factor = if($metric){ $metric.profit_factor } else { '' }
            total_trades = if($metric){ $metric.total_trades } else { '' }
            buy_trades = if($metric){ $metric.buy_trades } else { '' }
            sell_trades = if($metric){ $metric.sell_trades } else { '' }
            max_equity_dd_pct = if($metric){ $metric.max_equity_dd_pct } else { '' }
            max_consecutive_losses_count = if($metric){ $metric.max_consecutive_losing_count } else { '' }
            report = $r.Report
            config_path = $r.Config
            set_path = $r.Set
            notes = $notes
        }
        $case++
        Start-Sleep -Seconds 2
    }
}

$rows | Export-Csv -Path $summaryCsv -NoTypeInformation -Encoding UTF8

$decision = 'requires_temp_ea_or_external_model'
if($rows.Count -gt 0 -and ($rows | Where-Object status -eq 'completed').Count -lt $rows.Count){
    $decision = 'launch_error'
}

$md = @"
# Slippage Probe (v8.67 config-level test) - $timestamp

- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- EA: E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- Set: E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- Decision: $decision

| Field | Value | Window | Status | Net Profit | PF | Trades | Max Equity DD % | Max Consecutive Losses | Buy | Sell |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
"@
foreach($r in $rows){
    $md += "`n| $($r.field) | $($r.value) | $($r.window) | $($r.status) | $($r.net_profit) | $($r.profit_factor) | $($r.total_trades) | $($r.max_equity_dd_pct) | $($r.max_consecutive_losses_count) | $($r.buy_trades) | $($r.sell_trades) |"
}
Set-Content -Encoding UTF8 -Path $summaryMd -Value $md

Write-Output "CSV=$summaryCsv`nMD=$summaryMd`nDecision=$decision"
