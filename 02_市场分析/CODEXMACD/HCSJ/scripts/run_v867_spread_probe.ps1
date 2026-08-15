param()
$ErrorActionPreference='Stop'

$root = 'E:\CODEXMACD'
. "$root\HCSJ\scripts\robust_search_runner.ps1"

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path $root 'HCSJ\matrix\production_readiness'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$summaryCsv = Join-Path $outDir "spread_probe_v867_$timestamp.csv"
$summaryMd = Join-Path $outDir "spread_probe_v867_$timestamp.md"

$source = Join-Path $root 'SniperTrendEA_v8.67_grokbase_production_ready.mq5'
$expert = 'SniperTrendEA_v8.67_grokbase_production_ready_20260620_033547.ex5'
$ex5 = Join-Path 'D:\\MT5测试\\MetaTrader 5\\MQL5\\Experts' $expert
$setPath = Join-Path $root 'HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set'

$windows = @(
    [pscustomobject]@{ label='S2012_2019'; from='2012.01.01'; to='2019.12.31'; window='2012-2019' },
    [pscustomobject]@{ label='S2020_2026'; from='2020.01.01'; to='2026.06.30'; window='2020-2026' }
)

$spreadLevels = @(
    @{ label='S1_0'; value='1.0'; notes='fixed spread absolute 1.0' },
    @{ label='S1_5'; value='1.5'; notes='fixed spread absolute 1.5' },
    @{ label='S2_0'; value='2.0'; notes='fixed spread absolute 2.0' }
)

$rows = @()
$case = 1
foreach($sp in $spreadLevels){
    foreach($w in $windows){
        $runId = "v867_spread_probe_$($timestamp.Replace('_',''))_$($sp.label)_$($w.label)_case$('{0:d4}' -f $case)"
        $notes = "fixed-spread probe key=Spread value=$($sp.value) window=$($w.window)"
        $r = Invoke-Mt5Backtest `
            -RunId $runId `
            -Version 'v8.67' `
            -Window $w.window `
            -Stage 'fixed_spread_probe' `
            -Round 1 `
            -CaseId $case `
            -SourceFile $source `
            -ExpertFileName $expert `
            -Ex5File $ex5 `
            -BaseSet $setPath `
            -Overrides @{} `
            -FromDate $w.from `
            -ToDate $w.to `
            -CandidateClass 'spread_probe_v867' `
            -Decision 'v8.67-fixed-spread' `
            -Notes $notes `
            -ConfigOverrides @{Spread=$sp.value} `
            -TimeoutSeconds 1200
        $metric = if (Test-Path $r.Metrics) { Import-Csv -Path $r.Metrics | Select-Object -First 1 } else { $null }

        $rows += [pscustomobject]@{
            run_id = $r.RunId
            spread_key = 'Spread'
            spread_value = $sp.value
            window = $w.window
            status = $r.Status
            net_profit = if($metric){ $metric.net_profit } else { '' }
            profit_factor = if($metric){ $metric.profit_factor } else { '' }
            total_trades = if($metric){ $metric.total_trades } else { '' }
            max_equity_dd_pct = if($metric){ $metric.max_equity_dd_pct } else { '' }
            relative_equity_dd_pct = if($metric){ $metric.relative_equity_dd_pct } else { '' }
            buy_trades = if($metric){ $metric.buy_trades } else { '' }
            sell_trades = if($metric){ $metric.sell_trades } else { '' }
            max_consecutive_losses_count = if($metric){ $metric.max_consecutive_losing_count } else { '' }
            report = $r.Report
            set_path = $r.Set
            config_path = $r.Config
            notes = $notes
        }
        $case++
        Start-Sleep -Seconds 2
    }
}

$rows | Export-Csv -Path $summaryCsv -NoTypeInformation -Encoding UTF8

$statusCounts = $rows | Group-Object status | Select-Object Name, Count
$decision = 'inconclusive'
if($statusCounts.Count -eq 1 -and $statusCounts[0].Name -eq 'completed'){
    $decision = 'attempted'
}

$md = @"
# Fixed Spread Probe (v8.67) - $timestamp

- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- EA: E:\CODEXMACD\SniperTrendEA_v8.67_grokbase_production_ready.mq5
- Set: E:\CODEXMACD\HCSJ\set\v8.67\v8.67_grokbase_production_ready_default_case0010.set
- Probe key: Spread
- Decision: $decision

## Raw outputs

- Metrics CSV: $summaryCsv

## Matrix

| Spread | Window | Status | Net Profit | PF | Trades | Max Equity DD % | Max Consecutive Losses | Buy | Sell |
|---|---|---|---:|---:|---:|---:|---:|---:|
"@
foreach($r in $rows){
    $md += "`n| $($r.spread_value) | $($r.window) | $($r.status) | $($r.net_profit) | $($r.profit_factor) | $($r.total_trades) | $($r.max_equity_dd_pct) | $($r.max_consecutive_losses_count) | $($r.buy_trades) | $($r.sell_trades) |"
}
Set-Content -Encoding UTF8 -Path $summaryMd -Value $md

Write-Output "CSV=$summaryCsv`nMD=$summaryMd`nDecision=$decision"



