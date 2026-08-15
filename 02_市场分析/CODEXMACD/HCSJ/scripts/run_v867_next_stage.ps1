param(
    [ValidateSet('precheck','dateshift','wf20','wf12','spread','slippage','quarter','month_cluster','month_core','month_full')]
    [string]$Module = 'precheck',
    [string]$RunId = '',
    [ValidateSet('A','B','C','D')]
    [string[]]$Objects = @('B'),
    [string[]]$Windows = @('both'),
    [string[]]$Scenarios = @(),
    [int]$TimeoutSeconds = 300,
    [switch]$ForceCloseTerminal,
    [switch]$NoRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'E:\CODEXMACD'
$Hcsj = Join-Path $Root 'HCSJ'
$Mt5 = 'D:\MT5测试\MetaTrader 5'
$Terminal = Join-Path $Mt5 'terminal64.exe'
$TesterSetDir = Join-Path $Mt5 'MQL5\Profiles\Tester'
$SingleReportDir = Join-Path $Mt5 'SingleEAReports'
$WorkLog = Join-Path $Root 'WORK_LOG.md'

$Symbol = 'XAUUSD'
$Period = 'H4'
$Model = '1'
$Deposit = '20000'
$Leverage = '100'
$Round = 'r01'
$script:BatchManifest = ''

$candidateMap = @{
    A = @{
        Expert = 'SniperTrendEA_v8.6_groktrue_20260619.ex5'
        BaseSet = Join-Path $TesterSetDir 'v86_2020-2026_control_robust_case0502.set'
        Label = 'v8.6_control_robust_case0502'
    }
    B = @{
        Expert = 'SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
        BaseSet = Join-Path $TesterSetDir 'v866_2020-2026_control_robust_case0010.set'
        Label = 'v8.66_robust_main_case0010'
    }
    C = @{
        Expert = 'SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
        BaseSet = Join-Path $TesterSetDir 'v866_2020-2026_control_aggressive_case0005.set'
        Label = 'v8.66_aggressive_case0005'
    }
    D = @{
        Expert = 'SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
        BaseSet = Join-Path $TesterSetDir 'v866_2020-2026_control_conservative_case0401.set'
        Label = 'v8.66_conservative_case0401'
    }
}

function New-UniqueRunId {
    param([string]$Stage)
    $base = "{0}_{1}" -f (Get-Date -Format 'yyyyMMdd_HHmm'), $Stage
    $candidate = $base
    $i = 1
    while(
        (Test-Path -LiteralPath (Join-Path $Hcsj "v8.67_validation_runs\$candidate")) -or
        (Test-Path -LiteralPath (Join-Path $Hcsj "set\v8.67_validation_runs\$candidate")) -or
        (Test-Path -LiteralPath (Join-Path $Hcsj "backtest_archive\v8.67_validation_runs\$candidate")) -or
        (Test-Path -LiteralPath (Join-Path $Hcsj "matrix\v8.67_validation_runs\$candidate"))
    ) {
        $candidate = "{0}_{1:00}" -f $base, $i
        $i++
    }
    return $candidate
}

function Assert-NewPath {
    param([string]$Path)
    if(Test-Path -LiteralPath $Path) {
        throw "Refusing to overwrite existing path: $Path"
    }
}

function Get-DefaultScenarios {
    param([string]$Module)
    switch($Module) {
        'dateshift' { return @('shift00','shift01','shift02','shift03','shift04','shift05','shift06','shift07') }
        'precheck' { return @('shift00') }
        'wf20' { return @('validate') }
        'wf12' { return @('validate') }
        'slippage' { return @('delay000','delay100','delay500') }
        'quarter' { return @(1..32 | ForEach-Object { 'q{0:00}' -f $_ }) }
        'month_cluster' {
            return @(
                'm201407','m201408','m201409','m201410','m201411','m201412',
                'm201501','m201502','m201503','m201504','m201505','m201506',
                'm201701','m201702','m201703','m201704','m201705','m201706',
                'm201907','m201908','m201909','m201910','m201911','m201912'
            )
        }
    }
    throw "Module not implemented in runner yet: $Module"
}

function Convert-Mt5Date {
    param([string]$Date)
    return [datetime]::ParseExact($Date, 'yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
}

function Format-Mt5Date {
    param([datetime]$Date)
    return $Date.ToString('yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
}

function Get-ScenarioOffsetDays {
    param([string]$Scenario)
    if($Scenario -match '^shift0?([0-7])$') {
        return [int]$Matches[1]
    }
    throw "Unsupported dateshift scenario: $Scenario"
}

function Get-SlippageExecutionMode {
    param([string]$Scenario)
    if($Scenario -match '^delay([0-9]{3,4})$') {
        return [int]$Matches[1]
    }
    if($Scenario -eq 'random') {
        return -1
    }
    throw "Unsupported slippage scenario: $Scenario"
}

function Resolve-QuarterDateRange {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Window,

        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    if($Scenario -notmatch '^q([0-9]{2})$') {
        throw "Unsupported quarter scenario: $Scenario"
    }

    $quarterIndex = [int]$Matches[1]
    if($quarterIndex -lt 1) {
        throw "Unsupported quarter scenario: $Scenario"
    }

    $windowDates = Get-WindowDates -Window $Window
    $windowStart = Convert-Mt5Date $windowDates.From
    $windowEnd = Convert-Mt5Date $windowDates.To
    $from = $windowStart.AddMonths(3 * ($quarterIndex - 1))
    if($from -gt $windowEnd) {
        throw "Quarter scenario $Scenario is outside window $Window"
    }

    $to = $from.AddMonths(3).AddDays(-1)
    if($to -gt $windowEnd) { $to = $windowEnd }

    return @{
        Window = $Window
        FromDate = (Format-Mt5Date $from)
        ToDate = (Format-Mt5Date $to)
        Scenario = $Scenario
    }
}

function Get-MonthClusterScenarios {
    return @(
        'm201407','m201408','m201409','m201410','m201411','m201412',
        'm201501','m201502','m201503','m201504','m201505','m201506',
        'm201701','m201702','m201703','m201704','m201705','m201706',
        'm201907','m201908','m201909','m201910','m201911','m201912'
    )
}

function Resolve-MonthClusterDateRange {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Window,

        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    if($Window -ne '2012-2019') {
        throw "month_cluster only supports old window 2012-2019; received $Window"
    }

    if($Scenario -notmatch '^m([0-9]{4})([0-9]{2})$') {
        throw "Unsupported month_cluster scenario: $Scenario"
    }

    $allowed = @(Get-MonthClusterScenarios)
    if($Scenario -notin $allowed) {
        throw "month_cluster scenario outside allowed losing clusters: $Scenario"
    }

    $year = [int]$Matches[1]
    $month = [int]$Matches[2]
    $from = [datetime]::new($year, $month, 1)
    $to = $from.AddMonths(1).AddDays(-1)

    return @{
        Window = '2012-2019'
        FromDate = (Format-Mt5Date $from)
        ToDate = (Format-Mt5Date $to)
        Scenario = $Scenario
    }
}
function Get-FileSha256 {
    param([string]$Path)
    if(!(Test-Path -LiteralPath $Path)) { return '' }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function CsvEscape {
    param($Value)
    if($null -eq $Value) { return '' }
    $s = [string]$Value
    if($s -match '[,"`r`n]') { return '"' + $s.Replace('"','""') + '"' }
    return $s
}

function Append-BatchManifestRow {
    param([string]$Type, [string]$Path)
    if([string]::IsNullOrWhiteSpace($script:BatchManifest)) { return }
    if(!(Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path
    $row = @($Type, $item.FullName, $item.Length, $item.LastWriteTime.ToString('s'), (Get-FileSha256 $item.FullName))
    [System.IO.File]::AppendAllText($script:BatchManifest, (($row | ForEach-Object { CsvEscape $_ }) -join ',') + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Convert-Number {
    param($Value)
    if($null -eq $Value) { return 0.0 }
    $text = ([string]$Value).Trim() -replace ',', ''
    if([string]::IsNullOrWhiteSpace($text)) { return 0.0 }
    $number = 0.0
    if([double]::TryParse($text, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) {
        return $number
    }
    return 0.0
}

function Get-Median {
    param([double[]]$Values)
    $items = @($Values | Sort-Object)
    if($items.Count -eq 0) { return 0.0 }
    $middle = [int][math]::Floor($items.Count / 2)
    if(($items.Count % 2) -eq 1) { return $items[$middle] }
    return ($items[$middle - 1] + $items[$middle]) / 2.0
}

function Clean-CellText {
    param([string]$Html)
    $s = [regex]::Replace($Html, '<[^>]+>', '')
    return [System.Net.WebUtility]::HtmlDecode($s).Trim()
}

function Split-ValueAndPct {
    param([string]$Value)
    if($Value -match '([0-9 .-]+)\s*\(([-0-9.]+)%\)') {
        return @(($Matches[1] -replace ' ', ''), $Matches[2])
    }
    return @(($Value -replace ' ', ''), '')
}

function Get-ReportMetrics {
    param([string]$ReportPath)
    $metrics = @{
        profit = ''
        pf = ''
        max_dd = ''
        max_dd_pct = ''
        trade_count = ''
        avg_trade_profit = ''
    }
    if(!(Test-Path -LiteralPath $ReportPath)) { return $metrics }

    $html = [System.IO.File]::ReadAllText($ReportPath, [System.Text.Encoding]::Default)
    $matches = [regex]::Matches($html, '<td[^>]*>(.*?)</td>', 'Singleline')
    $cells = New-Object System.Collections.Generic.List[string]
    foreach($m in $matches) {
        $cell = Clean-CellText $m.Groups[1].Value
        if($cell.Length -gt 0) { [void]$cells.Add($cell) }
    }

    for($i = 0; $i -lt ($cells.Count - 1); $i++) {
        $label = $cells[$i]
        $val = $cells[$i + 1]
        if($label -match '总净盈利') {
            $metrics.profit = ($val -replace ' ', '')
        }
        elseif($label -match '盈利因子') {
            $metrics.pf = $val
        }
        elseif($label -match '最大结余亏损') {
            $pair = Split-ValueAndPct $val
            $metrics.max_dd = $pair[0]
            $metrics.max_dd_pct = $pair[1]
        }
        elseif($label -match '交易总计') {
            $metrics.trade_count = $val
        }
    }

    $profitNumber = 0.0
    $tradeNumber = 0.0
    if([double]::TryParse(($metrics.profit -replace ',', ''), [ref]$profitNumber) -and
       [double]::TryParse(($metrics.trade_count -replace ',', ''), [ref]$tradeNumber) -and
       $tradeNumber -ne 0) {
        $metrics.avg_trade_profit = [math]::Round($profitNumber / $tradeNumber, 2).ToString([Globalization.CultureInfo]::InvariantCulture)
    }
    return $metrics
}

function Write-TesterConfig {
    param(
        [string]$ConfigPath,
        [string]$Expert,
        [string]$SetFileName,
        [string]$FromDate,
        [string]$ToDate,
        [string]$ReportName,
        [string]$ExecutionModeValue = '100'
    )
    $content = @"
[Tester]
Expert=$Expert
ExpertParameters=$SetFileName
Symbol=$Symbol
Period=$Period
Optimization=0
Model=$Model
FromDate=$FromDate
ToDate=$ToDate
ForwardMode=0
Deposit=$Deposit
Currency=USD
ProfitInPips=0
Leverage=$Leverage
ExecutionMode=$ExecutionModeValue
OptimizationCriterion=0
Visual=0
Report=SingleEAReports\$ReportName
ReplaceReport=1
ShutdownTerminal=1
"@
    [System.IO.File]::WriteAllText($ConfigPath, $content, [System.Text.UTF8Encoding]::new($false))
}

function Get-WindowDates {
    param([string]$Window)
    if($Window -eq '2012-2019') {
        return @{ From = '2012.01.01'; To = '2019.12.31' }
    }
    if($Window -eq '2020-2026') {
        return @{ From = '2020.01.01'; To = '2026.06.30' }
    }
    throw "Unsupported window: $Window"
}

function Resolve-ValidationDateRange {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Module,

        [Parameter(Mandatory = $true)]
        [string]$Window,

        [Parameter(Mandatory = $true)]
        [string]$Scenario
    )

    if($Module -eq 'wf20') {
        return @{
            Window = '2012-2019'
            FromDate = '2012.01.01'
            ToDate = '2019.12.31'
            Scenario = 'validate'
        }
    }

    if($Module -eq 'wf12') {
        return @{
            Window = '2020-2026'
            FromDate = '2020.01.01'
            ToDate = '2026.06.30'
            Scenario = 'validate'
        }
    }

    return $null
}

function Write-FailureHtml {
    param([string]$Path, [string]$RunCaseId, [string]$Message)
    $html = "<html><head><meta charset=`"utf-8`"><title>$RunCaseId failed</title></head><body><h1>$RunCaseId failed</h1><pre>$([System.Net.WebUtility]::HtmlEncode($Message))</pre></body></html>"
    [System.IO.File]::WriteAllText($Path, $html, [System.Text.UTF8Encoding]::new($false))
}

function Update-MatrixRetentions {
    param([string]$MatrixPath)
    $rows = @(Import-Csv -LiteralPath $MatrixPath)
    foreach($windowGroup in ($rows | Group-Object window)) {
        $baseline = @($windowGroup.Group | Where-Object { $_.scenario -eq 'shift00' } | Select-Object -First 1)
        if($baseline.Count -eq 0) { continue }
        $baselineProfit = Convert-Number $baseline[0].profit
        $baselineTrades = Convert-Number $baseline[0].trade_count
        foreach($row in $windowGroup.Group) {
            $profit = Convert-Number $row.profit
            $trades = Convert-Number $row.trade_count
            if($baselineProfit -ne 0) {
                $row.profit_retention = [math]::Round($profit / $baselineProfit, 4).ToString([Globalization.CultureInfo]::InvariantCulture)
            }
            if($baselineTrades -ne 0) {
                $row.trade_retention = [math]::Round($trades / $baselineTrades, 4).ToString([Globalization.CultureInfo]::InvariantCulture)
            }
        }
    }
    $rows | Export-Csv -LiteralPath $MatrixPath -NoTypeInformation -Encoding UTF8
    return @(Import-Csv -LiteralPath $MatrixPath)
}

function Get-DateshiftRowGate {
    param($Row)
    if($Row.pass_fail -ne 'PASS') { return 'Red' }
    $profit = Convert-Number $Row.profit
    $pf = Convert-Number $Row.pf
    $retention = Convert-Number $Row.profit_retention
    $maxDdPct = Convert-Number $Row.max_dd_pct
    $trades = Convert-Number $Row.trade_count

    if($Row.window -eq '2020-2026') {
        if($profit -le 0 -or $retention -lt 0.60 -or $pf -lt 1.40 -or $trades -lt 150) { return 'Red' }
        if($retention -ge 0.70 -and $pf -ge 2.00 -and $trades -ge 180) { return 'Green' }
        return 'Yellow'
    }

    if($Row.window -eq '2012-2019') {
        if($profit -le 0 -or $pf -lt 1.00 -or $trades -lt 180 -or $maxDdPct -gt 75) { return 'Red' }
        if($pf -ge 1.15 -and $trades -ge 220 -and $maxDdPct -le 65) { return 'Green' }
        return 'Yellow'
    }

    return 'Yellow'
}

function Get-DateshiftGateReason {
    param($Row, [string]$Gate)
    if($Row.pass_fail -ne 'PASS') { return $Row.notes }
    $profit = Convert-Number $Row.profit
    $pf = Convert-Number $Row.pf
    $retention = Convert-Number $Row.profit_retention
    $maxDdPct = Convert-Number $Row.max_dd_pct
    $trades = Convert-Number $Row.trade_count
    if($Gate -eq 'Green') { return 'meets row gate' }
    if($Row.window -eq '2020-2026') {
        if($profit -le 0) { return 'non-positive profit' }
        if($retention -lt 0.60) { return 'profit_retention < 0.60' }
        if($pf -lt 1.40) { return 'PF < 1.40' }
        if($trades -lt 150) { return 'trades < 150' }
        return 'below green recent-window gate'
    }
    if($Row.window -eq '2012-2019') {
        if($profit -le 0) { return 'non-positive profit' }
        if($pf -lt 1.00) { return 'PF < 1.00' }
        if($trades -lt 180) { return 'trades < 180' }
        if($maxDdPct -gt 75) { return 'max_dd_pct > 75' }
        return 'below green old-window gate'
    }
    return 'review required'
}

function Format-Decimal {
    param([double]$Value, [int]$Digits = 2)
    return ([math]::Round($Value, $Digits)).ToString([Globalization.CultureInfo]::InvariantCulture)
}

function New-DateshiftStageReport {
    param([string]$RunId, [string]$MatrixPath, [string]$ReportPath)
    $rows = @(Update-MatrixRetentions -MatrixPath $MatrixPath)
    foreach($row in $rows) {
        $row | Add-Member -NotePropertyName gate -NotePropertyValue (Get-DateshiftRowGate -Row $row) -Force
        $row | Add-Member -NotePropertyName reason -NotePropertyValue (Get-DateshiftGateReason -Row $row -Gate $row.gate) -Force
    }

    $recent = @($rows | Where-Object { $_.window -eq '2020-2026' })
    $old = @($rows | Where-Object { $_.window -eq '2012-2019' })
    $redCount = @($rows | Where-Object { $_.gate -eq 'Red' }).Count

    $recentRetentions = @($recent | ForEach-Object { Convert-Number $_.profit_retention })
    $recentPfs = @($recent | ForEach-Object { Convert-Number $_.pf })
    $recentTrades = @($recent | ForEach-Object { Convert-Number $_.trade_count })
    $oldPfs = @($old | ForEach-Object { Convert-Number $_.pf })
    $oldTrades = @($old | ForEach-Object { Convert-Number $_.trade_count })
    $oldDd = @($old | ForEach-Object { Convert-Number $_.max_dd_pct })
    $oldProfits = @($old | ForEach-Object { Convert-Number $_.profit })

    $recentGreen = (Get-Median $recentRetentions) -ge 0.85 -and ($recentRetentions | Measure-Object -Minimum).Minimum -ge 0.70 -and (Get-Median $recentPfs) -ge 2.00 -and ($recentTrades | Measure-Object -Minimum).Minimum -ge 180
    $oldGreen = (@($oldProfits | Where-Object { $_ -le 0 }).Count -eq 0) -and (Get-Median $oldPfs) -ge 1.15 -and ($oldTrades | Measure-Object -Minimum).Minimum -ge 220 -and ($oldDd | Measure-Object -Maximum).Maximum -le 65

    $recentYellow = (Get-Median $recentRetentions) -ge 0.75 -and ($recentRetentions | Measure-Object -Minimum).Minimum -ge 0.60 -and (Get-Median $recentPfs) -ge 1.70 -and ($recentTrades | Measure-Object -Minimum).Minimum -ge 160
    $oldYellow = (@($oldProfits | Where-Object { $_ -le 0 }).Count -eq 0) -and (Get-Median $oldPfs) -ge 1.05 -and ($oldTrades | Measure-Object -Minimum).Minimum -ge 200 -and ($oldDd | Measure-Object -Maximum).Maximum -le 75

    if($redCount -gt 0) {
        $decision = 'Stop'
        $reason = "$redCount red case(s); stop expansion and review B robustness."
        $nextAction = 'Write dateshift_failure_review.md before any A/C/D expansion.'
    }
    elseif($recentGreen -and $oldGreen) {
        $decision = 'Continue'
        $reason = 'Both recent and old windows satisfy green aggregate gates.'
        $nextAction = 'Run A/C/D dateshift comparison batch.'
    }
    elseif($recentYellow -and $oldYellow) {
        $decision = 'Hold'
        $reason = 'No red cases, but at least one aggregate window is only yellow.'
        $nextAction = 'Run wf20 B validation before expanding A/C/D.'
    }
    else {
        $decision = 'Stop'
        $reason = 'Aggregate gates are below yellow without a single-row red trigger.'
        $nextAction = 'Review worst dateshift cases and revisit parameter selection.'
    }

    function New-WindowTable {
        param($WindowRows)
        $lines = @('| scenario | profit | retention | PF | max_dd_pct | trades | gate | reason |')
        $lines += '|---|---:|---:|---:|---:|---:|---|---|'
        foreach($row in ($WindowRows | Sort-Object scenario)) {
            $lines += "| $($row.scenario) | $($row.profit) | $($row.profit_retention) | $($row.pf) | $($row.max_dd_pct) | $($row.trade_count) | $($row.gate) | $($row.reason) |"
        }
        return ($lines -join [Environment]::NewLine)
    }

    $artifactLines = @('| case_id | html | metrics | notes |')
    $artifactLines += '|---|---|---|---|'
    foreach($row in ($rows | Sort-Object window,scenario)) {
        $artifactLines += "| $($row.case_id) | $($row.artifact_html) | $($row.artifact_metrics) | $($row.artifact_notes) |"
    }

    $report = @"
# v8.67 Dateshift Stage Report

run_id: $RunId
module: dateshift
objects: $($Objects -join '/')
windows: 2012-2019 / 2020-2026
scenarios: shift00-shift07

## Executive Decision

Decision: $decision
Reason: $reason

## Aggregate Snapshot

- 2020-2026 median_retention: $(Format-Decimal (Get-Median $recentRetentions) 4)
- 2020-2026 min_retention: $(Format-Decimal (($recentRetentions | Measure-Object -Minimum).Minimum) 4)
- 2020-2026 median_pf: $(Format-Decimal (Get-Median $recentPfs) 2)
- 2020-2026 min_trades: $(Format-Decimal (($recentTrades | Measure-Object -Minimum).Minimum) 0)
- 2012-2019 median_pf: $(Format-Decimal (Get-Median $oldPfs) 2)
- 2012-2019 min_trades: $(Format-Decimal (($oldTrades | Measure-Object -Minimum).Minimum) 0)
- 2012-2019 max_dd_pct: $(Format-Decimal (($oldDd | Measure-Object -Maximum).Maximum) 2)

## 2020-2026 Recent Window

$(New-WindowTable -WindowRows $recent)

## 2012-2019 Old Window

$(New-WindowTable -WindowRows $old)

## Artifact Index

$($artifactLines -join [Environment]::NewLine)

## Next Action

$nextAction
"@

    [System.IO.File]::WriteAllText($ReportPath, $report, [System.Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{ Decision=$decision; Reason=$reason; NextAction=$nextAction; Report=$ReportPath; RedCount=$redCount }
}

function Get-WfBaselineProfit {
    param([string]$ObjectCode, [string]$Window)
    if($ObjectCode -eq 'A' -and $Window -eq '2012-2019') { return 133752.99 }
    if($ObjectCode -eq 'A' -and $Window -eq '2020-2026') { return 489512.30 }
    if($ObjectCode -eq 'B' -and $Window -eq '2012-2019') { return 55826.12 }
    if($ObjectCode -eq 'B' -and $Window -eq '2020-2026') { return 556052.56 }
    if($ObjectCode -eq 'C' -and $Window -eq '2012-2019') { return 57221.99 }
    if($ObjectCode -eq 'C' -and $Window -eq '2020-2026') { return 716968.27 }
    if($ObjectCode -eq 'D' -and $Window -eq '2012-2019') { return 51100.55 }
    if($ObjectCode -eq 'D' -and $Window -eq '2020-2026') { return 371235.57 }
    return 0.0
}

function Test-WfArchiveComplete {
    param($Row)
    foreach($field in @('artifact_set','artifact_ini','artifact_html','artifact_metrics','artifact_notes')) {
        if([string]::IsNullOrWhiteSpace($Row.$field)) { return $false }
        if(!(Test-Path -LiteralPath $Row.$field)) { return $false }
    }
    return $true
}

function Get-WfThresholdStatus {
    param($Row)
    if(!(Test-WfArchiveComplete -Row $Row)) { return 'FAIL_ARCHIVE_INCOMPLETE' }
    if($Row.pass_fail -ne 'PASS') { return 'FAIL_ELIMINATED' }

    $profit = Convert-Number $Row.profit
    $pf = Convert-Number $Row.pf
    $trades = Convert-Number $Row.trade_count
    $maxDdPct = Convert-Number $Row.max_dd_pct
    $retention = Convert-Number $Row.profit_retention

    if($profit -le 0 -or $pf -lt 1.00 -or $trades -lt 180 -or $maxDdPct -gt 75) {
        return 'FAIL_ELIMINATED'
    }

    if($Row.module -eq 'wf20') {
        if($pf -ge 1.15 -and $trades -ge 240 -and $maxDdPct -le 65 -and $retention -ge 0.85) {
            return 'GREEN'
        }
        if($pf -ge 1.10 -and $trades -ge 220 -and $maxDdPct -le 70) {
            return 'PASS'
        }
        return 'FAIL_ELIMINATED'
    }

    if($Row.module -eq 'wf12') {
        if($retention -ge 0.90 -and $pf -ge 2.20 -and $trades -ge 200 -and $maxDdPct -le 30) {
            return 'GREEN'
        }
        if($retention -ge 0.80 -and $pf -ge 2.00 -and $trades -ge 190 -and $maxDdPct -le 35) {
            return 'PASS'
        }
        return 'FAIL_ELIMINATED'
    }

    if($Row.module -eq 'slippage') {
        if($Row.window -eq '2020-2026') {
            if($retention -ge 0.90 -and $pf -ge 2.00 -and $trades -ge 190 -and $maxDdPct -le 35) {
                return 'GREEN'
            }
            if($retention -ge 0.80 -and $pf -ge 1.70 -and $trades -ge 180 -and $maxDdPct -le 45) {
                return 'PASS'
            }
            return 'FAIL_ELIMINATED'
        }

        if($Row.window -eq '2012-2019') {
            if($retention -ge 0.85 -and $pf -ge 1.10 -and $trades -ge 220 -and $maxDdPct -le 70) {
                return 'GREEN'
            }
            if($retention -ge 0.75 -and $pf -ge 1.05 -and $trades -ge 200 -and $maxDdPct -le 75) {
                return 'PASS'
            }
            return 'FAIL_ELIMINATED'
        }
    }

    return 'FAIL_ELIMINATED'
}

function Get-WfDecisionText {
    param($Row)
    if($Row.threshold_status -eq 'FAIL_ARCHIVE_INCOMPLETE') {
        return 'Stop: object failed a required WF threshold.'
    }
    if($Row.threshold_status -eq 'FAIL_ELIMINATED') {
        return 'Stop: object failed a required WF threshold.'
    }
    if([string]::IsNullOrWhiteSpace($Row.profit_retention)) {
        return 'Review manually: metrics are parsed but comparison baseline is missing.'
    }
    if($Row.object -eq 'C') {
        return 'Continue as challenger only: object passed but is not eligible to replace B yet.'
    }
    return 'Continue: object passed this WF module.'
}

function New-WfStageReport {
    param([string]$RunId, [string]$MatrixPath, [string]$ReportPath)

    $rows = @(Import-Csv -LiteralPath $MatrixPath)
    foreach($row in $rows) {
        $baseline = Get-WfBaselineProfit -ObjectCode $row.object -Window $row.window
        $profit = Convert-Number $row.profit
        if($baseline -ne 0 -and $profit -ne 0) {
            $row.profit_retention = [math]::Round($profit / $baseline, 4).ToString([Globalization.CultureInfo]::InvariantCulture)
        }
        $status = Get-WfThresholdStatus -Row $row
        $row | Add-Member -NotePropertyName threshold_status -NotePropertyValue $status -Force
        $row | Add-Member -NotePropertyName decision -NotePropertyValue (Get-WfDecisionText -Row $row) -Force
    }
    $rows | Export-Csv -LiteralPath $MatrixPath -NoTypeInformation -Encoding UTF8

    $caseLines = @('| object | module | window | scenario | profit | retention | PF | max_dd_pct | trades | status | decision |')
    $caseLines += '|---|---|---|---|---:|---:|---:|---:|---:|---|---|'
    foreach($row in $rows) {
        $caseLines += "| $($row.object) | $($row.module) | $($row.window) | $($row.scenario) | $($row.profit) | $($row.profit_retention) | $($row.pf) | $($row.max_dd_pct) | $($row.trade_count) | $($row.threshold_status) | $($row.decision) |"
    }

    $archiveLines = @('| case_id | set | ini | html | metrics | notes |')
    $archiveLines += '|---|---|---|---|---|---|'
    foreach($row in $rows) {
        $archiveLines += "| $($row.case_id) | $(Test-Path -LiteralPath $row.artifact_set) | $(Test-Path -LiteralPath $row.artifact_ini) | $(Test-Path -LiteralPath $row.artifact_html) | $(Test-Path -LiteralPath $row.artifact_metrics) | $(Test-Path -LiteralPath $row.artifact_notes) |"
    }

    $failed = @($rows | Where-Object { $_.threshold_status -like 'FAIL*' })
    $green = @($rows | Where-Object { $_.threshold_status -eq 'GREEN' })
    if($failed.Count -gt 0) {
        $decision = 'Stop'
        $reason = "$($failed.Count) WF case(s) failed threshold or archive checks."
        $nextAction = 'Stop this branch and review wf_stage_report.md before running the next object.'
    }
    elseif($green.Count -eq $rows.Count) {
        $decision = 'Continue'
        $reason = 'All WF cases reached GREEN threshold.'
        $nextAction = 'Wait for operator confirmation before running the next WF batch.'
    }
    else {
        $decision = 'Continue'
        $reason = 'All WF cases passed required thresholds.'
        $nextAction = 'Wait for operator confirmation before running the next WF batch.'
    }

    $report = @"
# WF Stage Report

## Run

- run_id: $RunId
- module: $Module
- objects: $($Objects -join '/')
- generated: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))

## Cases

$($caseLines -join [Environment]::NewLine)

## Threshold Result

- decision: $decision
- reason: $reason

## Decision

$($rows | ForEach-Object { "- $($_.object) $($_.module) $($_.window): $($_.decision)" } | Out-String)

## Archive Checklist

$($archiveLines -join [Environment]::NewLine)
"@

    [System.IO.File]::WriteAllText($ReportPath, $report, [System.Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{ Decision=$decision; Reason=$reason; NextAction=$nextAction; Report=$ReportPath; RedCount=$failed.Count }
}

function New-QuarterStageReport {
    param([string]$RunId, [string]$MatrixPath, [string]$ReportPath)

    $rows = @(Import-Csv -LiteralPath $MatrixPath)
    foreach($row in $rows) {
        $profit = Convert-Number $row.profit
        $trades = Convert-Number $row.trade_count
        if($row.pass_fail -ne 'PASS') {
            $status = 'FAIL_ARCHIVE_OR_REPORT'
            $decisionText = 'Stop: report chain failed.'
        }
        elseif($trades -le 0) {
            $status = 'FAIL_ZERO_TRADES'
            $decisionText = 'Stop: zero-trade quarter.'
        }
        elseif($profit -gt 0) {
            $status = 'GREEN'
            $decisionText = 'Continue: profitable quarter.'
        }
        else {
            $status = 'RED'
            $decisionText = 'Review: losing quarter.'
        }
        $row | Add-Member -NotePropertyName threshold_status -NotePropertyValue $status -Force
        $row | Add-Member -NotePropertyName decision -NotePropertyValue $decisionText -Force
    }
    $rows | Export-Csv -LiteralPath $MatrixPath -NoTypeInformation -Encoding UTF8

    $failCount = @($rows | Where-Object { $_.threshold_status -like 'FAIL*' }).Count
    $redCount = @($rows | Where-Object { $_.threshold_status -eq 'RED' }).Count
    $greenCount = @($rows | Where-Object { $_.threshold_status -eq 'GREEN' }).Count
    $completedCount = @($rows | Where-Object { $_.pass_fail -eq 'PASS' }).Count
    $positiveRate = if($rows.Count -gt 0) { [math]::Round($greenCount / $rows.Count, 4) } else { 0.0 }
    $profits = @($rows | ForEach-Object { Convert-Number $_.profit })
    $pfs = @($rows | ForEach-Object { Convert-Number $_.pf })
    $trades = @($rows | ForEach-Object { Convert-Number $_.trade_count })

    if($failCount -gt 0) {
        $decision = 'Stop'
        $reason = "$failCount quarter case(s) failed report/archive or zero-trade checks."
        $nextAction = 'Stop before month expansion and review failed quarter artifacts.'
    }
    elseif($positiveRate -ge 0.60) {
        $decision = 'Continue'
        $reason = "Quarter positive rate $positiveRate with no failed report chain."
        $nextAction = 'Compare B/C quarter concentration before month_core.'
    }
    elseif($positiveRate -ge 0.50) {
        $decision = 'Hold'
        $reason = "Quarter positive rate $positiveRate is borderline."
        $nextAction = 'Review losing quarters before month_core.'
    }
    else {
        $decision = 'Stop'
        $reason = "Quarter positive rate $positiveRate is below 0.50."
        $nextAction = 'Stop expansion and review concentration risk.'
    }

    $caseLines = @('| scenario | profit | PF | max_dd_pct | trades | status | decision |')
    $caseLines += '|---|---:|---:|---:|---:|---|---|'
    foreach($row in ($rows | Sort-Object scenario)) {
        $caseLines += "| $($row.scenario) | $($row.profit) | $($row.pf) | $($row.max_dd_pct) | $($row.trade_count) | $($row.threshold_status) | $($row.decision) |"
    }

    $report = @"
# Quarter Stage Report

## Run

- run_id: $RunId
- module: quarter
- objects: $($Objects -join '/')
- windows: $($expandedWindows -join ' / ')
- generated: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))

## Aggregate

- completed_cases: $completedCount / $($rows.Count)
- green_quarters: $greenCount
- losing_quarters: $redCount
- failed_quarters: $failCount
- positive_rate: $positiveRate
- total_profit: $(Format-Decimal (($profits | Measure-Object -Sum).Sum) 2)
- median_pf: $(Format-Decimal (Get-Median $pfs) 2)
- min_trades: $(Format-Decimal (($trades | Measure-Object -Minimum).Minimum) 0)

## Decision

- decision: $decision
- reason: $reason
- next_action: $nextAction

## Cases

$($caseLines -join [Environment]::NewLine)
"@

    [System.IO.File]::WriteAllText($ReportPath, $report, [System.Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{ Decision=$decision; Reason=$reason; NextAction=$nextAction; Report=$ReportPath; RedCount=$redCount; FailCount=$failCount; PositiveRate=$positiveRate }
}

function New-MonthClusterStageReport {
    param([string]$RunId, [string]$MatrixPath, [string]$ReportPath)

    $rows = @(Import-Csv -LiteralPath $MatrixPath)
    foreach($row in $rows) {
        $profit = Convert-Number $row.profit
        $trades = Convert-Number $row.trade_count
        if($row.pass_fail -ne 'PASS') {
            $status = 'FAIL_ARCHIVE_OR_REPORT'
            $decisionText = 'Stop: report chain failed.'
        }
        elseif($trades -le 0) {
            $status = 'NO_TRADE'
            $decisionText = 'No-trade month; neutral for cluster hit-rate.'
        }
        elseif($profit -gt 0) {
            $status = 'GREEN'
            $decisionText = 'Profitable month.'
        }
        else {
            $status = 'RED'
            $decisionText = 'Losing month.'
        }
        $row | Add-Member -NotePropertyName threshold_status -NotePropertyValue $status -Force
        $row | Add-Member -NotePropertyName decision -NotePropertyValue $decisionText -Force
    }
    $rows | Export-Csv -LiteralPath $MatrixPath -NoTypeInformation -Encoding UTF8

    $failCount = @($rows | Where-Object { $_.threshold_status -like 'FAIL*' }).Count
    $redCount = @($rows | Where-Object { $_.threshold_status -eq 'RED' }).Count
    $greenCount = @($rows | Where-Object { $_.threshold_status -eq 'GREEN' }).Count
    $activeRows = @($rows | Where-Object { $_.threshold_status -ne 'NO_TRADE' })
    $noTradeCount = @($rows | Where-Object { $_.threshold_status -eq 'NO_TRADE' }).Count
    $positiveRate = if($activeRows.Count -gt 0) { [math]::Round($greenCount / $activeRows.Count, 4) } else { 0.0 }
    $profits = @($rows | ForEach-Object { Convert-Number $_.profit })
    $trades = @($rows | ForEach-Object { Convert-Number $_.trade_count })

    if($failCount -gt 0) {
        $decision = 'Stop'
        $reason = "$failCount month_cluster case(s) failed report/archive checks."
        $nextAction = 'Stop and review failed month artifacts.'
    }
    elseif($activeRows.Count -eq 0) {
        $decision = 'Hold'
        $reason = "Month-cluster has only no-trade cases."
        $nextAction = 'Review scenario selection before expanding month_cluster.'
    }
    elseif($positiveRate -ge 0.60) {
        $decision = 'Continue'
        $reason = "Month-cluster active positive rate $positiveRate; no_trade=$noTradeCount."
        $nextAction = 'Compare B/C monthly cluster profile before full month_core.'
    }
    else {
        $decision = 'Hold'
        $reason = "Month-cluster active positive rate $positiveRate is weak; no_trade=$noTradeCount."
        $nextAction = 'Do not run full month_core before cluster review.'
    }

    $caseLines = @('| scenario | profit | PF | max_dd_pct | trades | status | decision |')
    $caseLines += '|---|---:|---:|---:|---:|---|---|'
    foreach($row in ($rows | Sort-Object scenario)) {
        $caseLines += "| $($row.scenario) | $($row.profit) | $($row.pf) | $($row.max_dd_pct) | $($row.trade_count) | $($row.threshold_status) | $($row.decision) |"
    }

    $report = @"
# Month Cluster Stage Report

## Run

- run_id: $RunId
- module: month_cluster
- objects: $($Objects -join '/')
- windows: $($expandedWindows -join ' / ')
- generated: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))

## Aggregate

- completed_cases: $(@($rows | Where-Object { $_.pass_fail -eq 'PASS' }).Count) / $($rows.Count)
- green_months: $greenCount
- losing_months: $redCount
- no_trade_months: $noTradeCount
- failed_months: $failCount
- positive_rate: $positiveRate
- total_profit: $(Format-Decimal (($profits | Measure-Object -Sum).Sum) 2)
- min_trades: $(Format-Decimal (($trades | Measure-Object -Minimum).Minimum) 0)

## Decision

- decision: $decision
- reason: $reason
- next_action: $nextAction

## Cases

$($caseLines -join [Environment]::NewLine)
"@

    [System.IO.File]::WriteAllText($ReportPath, $report, [System.Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{ Decision=$decision; Reason=$reason; NextAction=$nextAction; Report=$ReportPath; RedCount=$redCount; FailCount=$failCount; PositiveRate=$positiveRate }
}
function Invoke-OneBacktest {
    param(
        [string]$ObjectCode,
        [string]$Window,
        [string]$Scenario,
        [int]$CaseNumber,
        [string]$RunRoot,
        [string]$SetRoot,
        [string]$ArchiveRoot,
        [string]$MatrixPath
    )

    $candidate = $candidateMap[$ObjectCode]
    $moduleForName = if($Module -eq 'precheck') { 'dateshift' } else { $Module }
    $executionModeValue = '100'
    $wfRange = Resolve-ValidationDateRange -Module $Module -Window $Window -Scenario $Scenario
    if($null -ne $wfRange) {
        $Window = $wfRange.Window
        $Scenario = $wfRange.Scenario
        $fromDate = $wfRange.FromDate
        $toDate = $wfRange.ToDate
    }
    elseif($Module -eq 'slippage') {
        $dates = Get-WindowDates -Window $Window
        $fromDate = $dates.From
        $toDate = $dates.To
        $executionModeValue = [string](Get-SlippageExecutionMode -Scenario $Scenario)
    }
    elseif($Module -eq 'quarter') {
        $quarterRange = Resolve-QuarterDateRange -Window $Window -Scenario $Scenario
        $Window = $quarterRange.Window
        $Scenario = $quarterRange.Scenario
        $fromDate = $quarterRange.FromDate
        $toDate = $quarterRange.ToDate
    }
    elseif($Module -eq 'month_cluster') {
        $monthRange = Resolve-MonthClusterDateRange -Window $Window -Scenario $Scenario
        $Window = $monthRange.Window
        $Scenario = $monthRange.Scenario
        $fromDate = $monthRange.FromDate
        $toDate = $monthRange.ToDate
    }
    else {
        $dates = Get-WindowDates -Window $Window
        $offsetDays = Get-ScenarioOffsetDays -Scenario $Scenario
        $fromDate = Format-Mt5Date ((Convert-Mt5Date $dates.From).AddDays($offsetDays))
        $toDate = Format-Mt5Date ((Convert-Mt5Date $dates.To).AddDays(-1 * $offsetDays))
    }
    $caseText = 'case{0:0000}' -f $CaseNumber
    if($Module -in @('wf20','wf12')) {
        $id = "v866_${ObjectCode}_${Module}_${Window}_${Scenario}_${Round}_${caseText}"
    }
    else {
        $id = "v866_${ObjectCode}_${moduleForName}_${Window}_${Scenario}_${Round}_${caseText}"
    }

    $configDir = Join-Path $RunRoot "config\$Window"
    $setDir = Join-Path $SetRoot $Window
    $caseArchiveDir = Join-Path $ArchiveRoot "$Window\$id"
    New-Item -ItemType Directory -Force -Path $configDir, $setDir, $caseArchiveDir | Out-Null

    $setFile = Join-Path $setDir "$id.set"
    $configFile = Join-Path $configDir "$id.ini"
    $archiveSet = Join-Path $caseArchiveDir "$id.set"
    $archiveIni = Join-Path $caseArchiveDir "$id.ini"
    $archiveHtml = Join-Path $caseArchiveDir "$id.htm"
    $metricsCsv = Join-Path $caseArchiveDir "$id`_metrics.csv"
    $notesMd = Join-Path $caseArchiveDir "$id`_notes.md"

    foreach($p in @($setFile, $configFile, $archiveSet, $archiveIni, $archiveHtml, $metricsCsv, $notesMd)) {
        Assert-NewPath -Path $p
    }

    if(!(Test-Path -LiteralPath $candidate['BaseSet'])) {
        throw "Base set not found for ${ObjectCode}: $($candidate['BaseSet'])"
    }
    $expertPath = Join-Path (Join-Path $Mt5 'MQL5\Experts') $candidate['Expert']
    if(!(Test-Path -LiteralPath $expertPath)) {
        throw "Expert not found for ${ObjectCode}: $expertPath"
    }

    Copy-Item -LiteralPath $candidate['BaseSet'] -Destination $setFile
    Copy-Item -LiteralPath $setFile -Destination (Join-Path $TesterSetDir "$id.set") -Force
    Append-BatchManifestRow -Type 'generated_set' -Path $setFile

    $reportName = "${script:RunId}_$id"
    $reportSource = Join-Path $SingleReportDir "$reportName.htm"
    Assert-NewPath -Path $reportSource
    Write-TesterConfig -ConfigPath $configFile -Expert $candidate['Expert'] -SetFileName "$id.set" -FromDate $fromDate -ToDate $toDate -ReportName $reportName -ExecutionModeValue $executionModeValue
    Append-BatchManifestRow -Type 'generated_ini' -Path $configFile

    $status = 'started'
    $failureMessage = ''
    $startedAt = Get-Date
    if($NoRun) {
        $status = 'dry_run'
    }
    else {
        try {
            $p = Start-Process -FilePath $Terminal -ArgumentList @('/portable', "/config:$configFile") -WorkingDirectory $Mt5 -WindowStyle Hidden -PassThru
            $finished = $p.WaitForExit($TimeoutSeconds * 1000)
            if($finished) {
                $status = "terminal_exit_$($p.ExitCode)"
            }
            else {
                $status = 'timeout'
                $failureMessage = "MT5 did not exit within $TimeoutSeconds seconds."
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            $status = 'launch_failed'
            $failureMessage = $_.Exception.Message
        }
    }

    if(-not $NoRun) {
        $deadline = (Get-Date).AddSeconds(20)
        while((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $reportSource)) {
            Start-Sleep -Milliseconds 500
        }
    }

    if((Test-Path -LiteralPath $reportSource) -and -not $NoRun) {
        Copy-Item -LiteralPath $reportSource -Destination $archiveHtml
        Append-BatchManifestRow -Type 'report_html' -Path $archiveHtml
        Get-ChildItem -Path $SingleReportDir -File -Filter "$reportName*.png" | ForEach-Object {
            $assetDest = Join-Path $caseArchiveDir $_.Name
            Assert-NewPath -Path $assetDest
            Copy-Item -LiteralPath $_.FullName -Destination $assetDest
            Append-BatchManifestRow -Type 'report_png' -Path $assetDest
        }
        $status = 'completed'
    }
    elseif(-not $NoRun) {
        if([string]::IsNullOrWhiteSpace($failureMessage)) {
            $failureMessage = "No report generated at $reportSource. Check Tester set path and terminal logs."
        }
        Write-FailureHtml -Path $archiveHtml -RunCaseId $id -Message $failureMessage
        if($status -like 'terminal_exit_*') { $status = "${status}_no_report" }
    }

    Copy-Item -LiteralPath $setFile -Destination $archiveSet
    Copy-Item -LiteralPath $configFile -Destination $archiveIni
    Append-BatchManifestRow -Type 'archive_set' -Path $archiveSet
    Append-BatchManifestRow -Type 'archive_ini' -Path $archiveIni

    $metrics = Get-ReportMetrics -ReportPath $archiveHtml
    $profitRetention = ''
    $baselineProfit = Get-WfBaselineProfit -ObjectCode $ObjectCode -Window $Window
    if($Module -in @('wf20','wf12','slippage','quarter') -and $baselineProfit -ne 0 -and $metrics.profit) {
        $profitNumber = 0.0
        if([double]::TryParse(($metrics.profit -replace ',', ''), [ref]$profitNumber)) {
            $profitRetention = [math]::Round($profitNumber / $baselineProfit, 4).ToString([Globalization.CultureInfo]::InvariantCulture)
        }
    }
    elseif($ObjectCode -eq 'B' -and $Window -eq '2020-2026' -and $metrics.profit) {
        $profitNumber = 0.0
        if([double]::TryParse(($metrics.profit -replace ',', ''), [ref]$profitNumber)) {
            $profitRetention = [math]::Round($profitNumber / 556052.56, 4).ToString([Globalization.CultureInfo]::InvariantCulture)
        }
    }
    $passFail = if($status -eq 'completed') { 'PASS' } elseif($status -eq 'dry_run') { 'DRY_RUN' } else { 'FAIL' }

    $metricHeader = 'run_id,module,object,case_id,window,scenario,profit,pf,max_dd,max_dd_pct,trade_count,profit_retention,trade_retention,pass_fail,notes,artifact_set,artifact_ini,artifact_html,artifact_metrics,artifact_notes'
    $metricRow = @($script:RunId,$Module,$ObjectCode,$id,$Window,$Scenario,$metrics.profit,$metrics.pf,$metrics.max_dd,$metrics.max_dd_pct,$metrics.trade_count,$profitRetention,'',$passFail,$status,$archiveSet,$archiveIni,$archiveHtml,$metricsCsv,$notesMd)
    [System.IO.File]::WriteAllText($metricsCsv, $metricHeader + [Environment]::NewLine + (($metricRow | ForEach-Object { CsvEscape $_ }) -join ',') + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
    Append-BatchManifestRow -Type 'metrics_csv' -Path $metricsCsv

    [System.IO.File]::WriteAllText($notesMd, @"
# $id

Status: $status
Object: $ObjectCode ($($candidate['Label']))
Window: $Window
Scenario: $Scenario
FromDate: $fromDate
ToDate: $toDate
Expert: $($candidate['Expert'])
Tester set: $(Join-Path $TesterSetDir "$id.set")
Report source: $reportSource
Failure: $failureMessage
Started: $($startedAt.ToString('yyyy-MM-dd HH:mm:ss zzz'))
Finished: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))
"@, [System.Text.UTF8Encoding]::new($false))
    Append-BatchManifestRow -Type 'notes_md' -Path $notesMd

    [System.IO.File]::AppendAllText($MatrixPath, (($metricRow | ForEach-Object { CsvEscape $_ }) -join ',') + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

    return [pscustomobject]@{
        Id = $id
        Status = $status
        Object = $ObjectCode
        Window = $Window
        Scenario = $Scenario
        Profit = $metrics.profit
        PF = $metrics.pf
        MaxDdPct = $metrics.max_dd_pct
        Trades = $metrics.trade_count
        Html = $archiveHtml
        Metrics = $metricsCsv
        Notes = $notesMd
        Seconds = [int]((Get-Date) - $startedAt).TotalSeconds
    }
}

if(!(Test-Path -LiteralPath $Terminal)) { throw "MT5 terminal not found: $Terminal" }
New-Item -ItemType Directory -Force -Path $TesterSetDir, $SingleReportDir | Out-Null

$implementedModules = @('precheck','dateshift','wf20','wf12','slippage','quarter','month_cluster')
if($Module -notin $implementedModules) {
    throw "Module not implemented in runner yet: $Module"
}

if([string]::IsNullOrWhiteSpace($RunId)) {
    $script:RunId = New-UniqueRunId -Stage $Module
}
else {
    $script:RunId = $RunId.Trim()
}

$expandedWindows = @()
if($Windows -contains 'both') {
    $expandedWindows = @('2012-2019','2020-2026')
}
else {
    $expandedWindows = $Windows
}
foreach($w in $expandedWindows) {
    if($w -notin @('2012-2019','2020-2026')) { throw "Unsupported window: $w" }
}

$expandedScenarios = @()
if($Scenarios.Count -eq 0) {
    $expandedScenarios = @(Get-DefaultScenarios -Module $Module)
}
else {
    $expandedScenarios = @($Scenarios | ForEach-Object { $_ -split ',' } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() })
}
foreach($scenario in $expandedScenarios) {
    if($Module -in @('precheck','dateshift')) {
        [void](Get-ScenarioOffsetDays -Scenario $scenario)
    }
    elseif($Module -eq 'slippage') {
        [void](Get-SlippageExecutionMode -Scenario $scenario)
    }
    elseif($Module -eq 'quarter') {
        foreach($window in $expandedWindows) {
            [void](Resolve-QuarterDateRange -Window $window -Scenario $scenario)
        }
    }
    elseif($Module -eq 'month_cluster') {
        foreach($window in $expandedWindows) {
            [void](Resolve-MonthClusterDateRange -Window $window -Scenario $scenario)
        }
    }
    elseif($scenario -ne 'validate') {
        throw "Unsupported ${Module} scenario: $scenario"
    }
}

$runRoot = Join-Path $Hcsj "v8.67_validation_runs\$script:RunId"
$setRoot = Join-Path $Hcsj "set\v8.67_validation_runs\$script:RunId"
$archiveRoot = Join-Path $Hcsj "backtest_archive\v8.67_validation_runs\$script:RunId"
$matrixRoot = Join-Path $Hcsj "matrix\v8.67_validation_runs\$script:RunId"
foreach($p in @($runRoot, $setRoot, $archiveRoot, $matrixRoot)) { Assert-NewPath -Path $p }
New-Item -ItemType Directory -Force -Path $runRoot, $setRoot, $archiveRoot, $matrixRoot | Out-Null

$sourceSnapshotDir = Join-Path $archiveRoot '_source_snapshot'
$logsDir = Join-Path $archiveRoot '_logs'
New-Item -ItemType Directory -Force -Path $sourceSnapshotDir, $logsDir | Out-Null
$runnerSnapshot = Join-Path $sourceSnapshotDir 'run_v867_next_stage.ps1'
Copy-Item -LiteralPath (Join-Path $Hcsj 'scripts\run_v867_next_stage.ps1') -Destination $runnerSnapshot
$script:BatchManifest = Join-Path $archiveRoot '_batch_manifest.csv'
[System.IO.File]::WriteAllText($script:BatchManifest, "type,path,size,last_write_time,sha256" + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Append-BatchManifestRow -Type 'runner_snapshot' -Path $runnerSnapshot
foreach($objectCode in $Objects) {
    Append-BatchManifestRow -Type 'base_set' -Path $candidateMap[$objectCode]['BaseSet']
}

$matrixPath = Join-Path $matrixRoot 'matrix.csv'
$matrixHeader = 'run_id,module,object,case_id,window,scenario,profit,pf,max_dd,max_dd_pct,trade_count,profit_retention,trade_retention,pass_fail,notes,artifact_set,artifact_ini,artifact_html,artifact_metrics,artifact_notes'
[System.IO.File]::WriteAllText($matrixPath, $matrixHeader + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

$existingTerminals = @(Get-Process -Name terminal64 -ErrorAction SilentlyContinue)
if((-not $NoRun) -and $existingTerminals.Count -gt 0) {
    if($ForceCloseTerminal) {
        $existingTerminals | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    else {
        throw "terminal64.exe is already running. Re-run with -ForceCloseTerminal for unattended backtests."
    }
}

$results = New-Object System.Collections.Generic.List[object]
$caseNumber = 1
foreach($objectCode in $Objects) {
    foreach($scenario in $expandedScenarios) {
        foreach($window in $expandedWindows) {
            $result = Invoke-OneBacktest -ObjectCode $objectCode -Window $window -Scenario $scenario -CaseNumber $caseNumber -RunRoot $runRoot -SetRoot $setRoot -ArchiveRoot $archiveRoot -MatrixPath $matrixPath
            [void]$results.Add($result)
            $caseNumber++
        }
    }
}

$todayLogName = (Get-Date).ToString('yyyyMMdd') + '.log'
$terminalLog = Join-Path (Join-Path $Mt5 'logs') $todayLogName
$testerLog = Join-Path (Join-Path $Mt5 'Tester\logs') $todayLogName
if((Test-Path -LiteralPath $terminalLog) -and -not $NoRun) {
    $destLog = Join-Path $logsDir "terminal_$todayLogName"
    Copy-Item -LiteralPath $terminalLog -Destination $destLog -Force
    Append-BatchManifestRow -Type 'terminal_log' -Path $destLog
}
if((Test-Path -LiteralPath $testerLog) -and -not $NoRun) {
    $destLog = Join-Path $logsDir "tester_$todayLogName"
    Copy-Item -LiteralPath $testerLog -Destination $destLog -Force
    Append-BatchManifestRow -Type 'tester_log' -Path $destLog
}

$stageReportResult = $null
if($Module -eq 'dateshift' -and -not $NoRun) {
    $stageReportPath = Join-Path $matrixRoot 'dateshift_stage_report.md'
    Assert-NewPath -Path $stageReportPath
    $stageReportResult = New-DateshiftStageReport -RunId $script:RunId -MatrixPath $matrixPath -ReportPath $stageReportPath
    Append-BatchManifestRow -Type 'stage_report' -Path $stageReportPath
}
elseif($Module -in @('wf20','wf12') -and -not $NoRun) {
    $stageReportPath = Join-Path $matrixRoot 'wf_stage_report.md'
    Assert-NewPath -Path $stageReportPath
    $stageReportResult = New-WfStageReport -RunId $script:RunId -MatrixPath $matrixPath -ReportPath $stageReportPath
    Append-BatchManifestRow -Type 'stage_report' -Path $stageReportPath
}
elseif($Module -eq 'slippage' -and -not $NoRun) {
    $stageReportPath = Join-Path $matrixRoot 'slippage_stage_report.md'
    Assert-NewPath -Path $stageReportPath
    $stageReportResult = New-WfStageReport -RunId $script:RunId -MatrixPath $matrixPath -ReportPath $stageReportPath
    Append-BatchManifestRow -Type 'stage_report' -Path $stageReportPath
}
elseif($Module -eq 'quarter' -and -not $NoRun) {
    $stageReportPath = Join-Path $matrixRoot 'quarter_stage_report.md'
    Assert-NewPath -Path $stageReportPath
    $stageReportResult = New-QuarterStageReport -RunId $script:RunId -MatrixPath $matrixPath -ReportPath $stageReportPath
    Append-BatchManifestRow -Type 'stage_report' -Path $stageReportPath
}
elseif($Module -eq 'month_cluster' -and -not $NoRun) {
    $stageReportPath = Join-Path $matrixRoot 'month_cluster_stage_report.md'
    Assert-NewPath -Path $stageReportPath
    $stageReportResult = New-MonthClusterStageReport -RunId $script:RunId -MatrixPath $matrixPath -ReportPath $stageReportPath
    Append-BatchManifestRow -Type 'stage_report' -Path $stageReportPath
}

$successCount = @($results | Where-Object { $_.Status -eq 'completed' }).Count
$dryRunCount = @($results | Where-Object { $_.Status -eq 'dry_run' }).Count
$failCount = $results.Count - $successCount - $dryRunCount
$decision = if($NoRun) { 'DRY_RUN' } elseif($failCount -eq 0) { '通过' } else { '中止并复盘' }
$nextStep = if($NoRun) { 'dry-run 完成后执行真实批次' } elseif($null -ne $stageReportResult) { $stageReportResult.NextAction } elseif($failCount -eq 0) { '继续进入下一阶段' } else { '中止并复盘 MT5 启动/报告链路' }
$scenarioText = $expandedScenarios -join ','
$resultLines = ($results | ForEach-Object { "- $($_.Id): scenario=$($_.Scenario), status=$($_.Status), profit=$($_.Profit), PF=$($_.PF), trades=$($_.Trades)" }) -join [Environment]::NewLine
$outputLines = @(
    "- set: $setRoot",
    "- ini: $runRoot",
    "- htm: $archiveRoot",
    "- metrics: $matrixPath",
    "- notes: $archiveRoot",
    "- matrix: $matrixPath",
    "- logs: $logsDir",
    "- manifest: $script:BatchManifest"
) -join [Environment]::NewLine
if($null -ne $stageReportResult) {
    $outputLines += [Environment]::NewLine + "- stage_report: $($stageReportResult.Report)"
}

$workLogEntry = @"

## $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz')) - v8.67 $Module batch $script:RunId
类型：回测 / 参数生成 / 报告生成
run_id: $script:RunId
模块：$Module
任务目标：按 v8.67 下一阶段计划执行 $Module 小批次验证
MT5路径：$Mt5
输入对象：$($Objects -join '/')
输入窗口：$($expandedWindows -join ' / ')
输入参数：$(($Objects | ForEach-Object { "$_=$($candidateMap[$_]['Label'])" }) -join '; ')
场景配置：$scenarioText
回测数量：$($results.Count)
成功：$successCount
失败：$failCount
DryRun：$dryRunCount
关键指标：
$resultLines
初筛结论：$decision
原因代码：$(if($failCount -eq 0){'OK'}else{'D01回测失败'})
下一步：$nextStep
输出路径：
$outputLines
"@
[System.IO.File]::AppendAllText($WorkLog, $workLogEntry, [System.Text.UTF8Encoding]::new($false))

$results | Format-Table Id,Status,Object,Window,Scenario,Profit,PF,Trades,Seconds -AutoSize
Write-Output "RunId=$script:RunId"
Write-Output "Matrix=$matrixPath"
if($null -ne $stageReportResult) {
    Write-Output "StageReport=$($stageReportResult.Report)"
    Write-Output "StageDecision=$($stageReportResult.Decision)"
    Write-Output "StageReason=$($stageReportResult.Reason)"
}
