param(
    [int[]]$Levels = @(0,1,2,3,5),
    [string[]]$Objects = @('B','C'),
    [int]$TimeoutSeconds = 1200,
    [switch]$NoRun
)

$ErrorActionPreference = 'Stop'
$Root = 'E:\CODEXMACD'
. "$Root\HCSJ\scripts\robust_search_runner.ps1"

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$workLog = Join-Path $Root 'WORK_LOG.md'
$mt5 = 'D:\MT5测试\MetaTrader 5'
$ex5File = Join-Path $mt5 'MQL5\Experts\SniperTrendEA_v8.67_slippage_test.ex5'
$source = Join-Path $Root 'SniperTrendEA_v8.67_slippage_test.mq5'

$outDir = Join-Path (Join-Path $Root 'HCSJ\matrix\production_readiness') ('v867_slippage_harness_' + $timestamp)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$setRoot = Join-Path $Root ("HCSJ\set\v8.67\$timestamp")
New-Item -ItemType Directory -Force -Path $setRoot | Out-Null
$archiveRoot = Join-Path $Root ('HCSJ\backtest_archive\v867_slippage_harness_' + $timestamp)
New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null

$matrixRows = @()
$rows = @()
$case = 1

$setMap = @{
    B = Join-Path $Root 'HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set'
    C = Join-Path $Root 'HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set'
}
$windowMap = @(
    @{ key = '2012-2019'; from = '2012.01.01'; to = '2019.12.31' },
    @{ key = '2020-2026'; from = '2020.01.01'; to = '2026.06.30' }
)

foreach($obj in $Objects){
    if(-not $setMap.ContainsKey($obj)) { continue }
    $baseSet = $setMap[$obj]
    if(-not (Test-Path $baseSet)) { throw "Base set missing: $baseSet" }

    foreach($w in $windowMap){
        foreach($lvl in $Levels){
            $runId = "v867_slippage_harness_${timestamp}_obj${obj}_${w.key}_lvl${lvl}_case{0:d4}" -f $case
            $notes = "temp slippage harness level=${lvl} for object=${obj} window=${w.key}"
            if($NoRun){
                $runId = "$runId`_dryrun"
            }
            $r = Invoke-Mt5Backtest -RunId $runId -Version 'v8.67' -Window $w.key -Stage 'slippage_harness' -Round 1 -CaseId $case -SourceFile $source -ExpertFileName 'SniperTrendEA_v8.67_slippage_test.ex5' -Ex5File $ex5File -BaseSet $baseSet -Overrides @{InpSlippagePressurePips = [string]$lvl } -FromDate $w.from -ToDate $w.to -CandidateClass 'temp_slippage' -Decision 'v8.67-temp-slippage-harness' -Notes $notes -ConfigOverrides @{} -TimeoutSeconds $TimeoutSeconds

            $metric = $null
            if(Test-Path $r.Metrics){
                $metric = Import-Csv -Path $r.Metrics | Select-Object -First 1
            }

            $rows += [pscustomobject]@{
                run_id       = $r.RunId
                object       = $obj
                window       = $w.key
                slippage_pips = $lvl
                status       = $r.Status
                report       = $r.Report
                set          = $r.Set
                config       = $r.Config
                metrics_csv  = $r.Metrics
                notes        = $notes
                net_profit   = if($metric){ $metric.net_profit } else { '' }
                profit_factor= if($metric){ $metric.profit_factor } else { '' }
                total_trades = if($metric){ $metric.total_trades } else { '' }
                max_equity_dd_pct = if($metric){ $metric.max_equity_dd_pct } else { '' }
                max_consecutive_losing_count = if($metric){ $metric.max_consecutive_losing_count } else { '' }
                buy_trades = if($metric){ $metric.buy_trades } else { '' }
                sell_trades = if($metric){ $metric.sell_trades } else { '' }
            }

            $case++
            Start-Sleep -Milliseconds 500
        }
    }
}

$csvPath = Join-Path $outDir ("slippage_harness_v867_$timestamp.csv")
$rows | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

$success = @($rows | Where-Object { $_.status -eq 'completed' }).Count
$fail = @($rows | Where-Object { $_.status -ne 'completed' }).Count
$decision = if($success -eq 0){ 'blocked' } elseif($fail -gt 0){ 'partial' } else { 'completed' }

$md = @"
# v8.67 Temporary Slippage Harness (B/C) - $timestamp

- Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- Input source: E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- Temp EA: E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- Total cases: $($rows.Count)
- Completed: $success
- Other: $fail
- Decision: $decision

## Raw CSV

- $csvPath

## Matrix

| RunID | Object | Window | Level | Status | Net Profit | PF | Trades |
|---|---|---|---:|---|---:|---:|
"@
foreach($r in $rows){
    $md += "`n| $($r.run_id) | $($r.object) | $($r.window) | $($r.slippage_pips) | $($r.status) | $($r.net_profit) | $($r.profit_factor) | $($r.total_trades) |"
}
$md += "`n"
$mdPath = Join-Path $outDir ("slippage_harness_v867_$timestamp.md")
Set-Content -Encoding UTF8 -Path $mdPath -Value $md

$entry = @"
## $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - v8.67临时滑点EA闭环补测
- 类型：回测 / 参数生成 / 报告生成
- 任务目标：执行临时滑点EA压力测试（对象B/C，级别0/1/2/3/5）
- 输入文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
- 执行文件：E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.ex5
- 输出目录：
  - 矩阵/报告: $outDir
  - .set: $setRoot
  - 报告归档: $archiveRoot
  - 结果CSV: $csvPath
  - 结果MD: $mdPath
- 回测数量：$($rows.Count)
- 成功：$success
- 失败：$fail
- 决议：$decision
- 后续：基于利润与PF退化阈值更新执行风险结论
"@
Add-Content -Path $workLog -Value $entry

Write-Output ("CSV=$csvPath")
Write-Output ("MD=$mdPath")
Write-Output ("Decision=$decision")
Write-Output ("Success=$success")
Write-Output ("Fail=$fail")
