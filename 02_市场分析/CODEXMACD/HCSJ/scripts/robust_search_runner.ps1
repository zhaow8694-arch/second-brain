$ErrorActionPreference = 'Stop'

$Root = 'E:\CODEXMACD'
$Hcsj = Join-Path $Root 'HCSJ'
$Mt5 = 'D:\MT5测试\MetaTrader 5'
$Terminal = Join-Path $Mt5 'terminal64.exe'
$TesterSetDir = Join-Path $Mt5 'MQL5\Profiles\Tester'
$SingleReportDir = Join-Path $Mt5 'SingleEAReports'
$MatrixPath = Join-Path $Hcsj 'matrix\robust_parameter_search_matrix.csv'
$WorkLog = Join-Path $Root 'WORK_LOG.md'
$Symbol = 'XAUUSD'
$Period = 'H4'
$Model = '1'
$Spread = 'current'
$Deposit = '20000'
$Leverage = '100'

function Ensure-Matrix {
    $header='run_id,version,window,stage,round,case_id,status,source_file,ex5_file,set_file,config_file,report_file,start_date,end_date,symbol,timeframe,model,spread,deposit,leverage,net_profit,profit_factor,max_balance_dd,max_balance_dd_pct,max_equity_dd,max_equity_dd_pct,relative_equity_dd,relative_equity_dd_pct,total_trades,win_rate,robustness_score,candidate_class,decision,notes'
    if(!(Test-Path -LiteralPath $MatrixPath)){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $MatrixPath) | Out-Null
        [System.IO.File]::WriteAllText($MatrixPath, $header + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
    }
}

function CsvEscape {
    param($Value)
    if($null -eq $Value){ return '' }
    $s = [string]$Value
    if($s -match '[,"`r`n]') { return '"' + $s.Replace('"','""') + '"' }
    return $s
}

function Append-MatrixRow {
    param([hashtable]$Row)
    Ensure-Matrix
    $cols = 'run_id','version','window','stage','round','case_id','status','source_file','ex5_file','set_file','config_file','report_file','start_date','end_date','symbol','timeframe','model','spread','deposit','leverage','net_profit','profit_factor','max_balance_dd','max_balance_dd_pct','max_equity_dd','max_equity_dd_pct','relative_equity_dd','relative_equity_dd_pct','total_trades','win_rate','robustness_score','candidate_class','decision','notes'
    $line = ($cols | ForEach-Object { CsvEscape $Row[$_] }) -join ','
    [System.IO.File]::AppendAllText($MatrixPath, $line + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function New-SetFile {
    param([string]$BaseSet,[string]$OutSet,[hashtable]$Overrides)
    $lines = [System.Collections.Generic.List[string]]::new()
    [System.IO.File]::ReadAllLines($BaseSet) | ForEach-Object { [void]$lines.Add($_) }
    foreach($key in $Overrides.Keys){
        $found = $false
        for($i=0; $i -lt $lines.Count; $i++){
            if($lines[$i] -match ('^' + [regex]::Escape($key) + '=')){
                $lines[$i] = "$key=$($Overrides[$key])"
                $found = $true
                break
            }
        }
        if(-not $found){ [void]$lines.Add("$key=$($Overrides[$key])") }
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutSet) | Out-Null
    [System.IO.File]::WriteAllLines($OutSet, $lines, [System.Text.UTF8Encoding]::new($false))
}

function Clean-CellText {
    param([string]$Html)
    $s = [regex]::Replace($Html, '<[^>]+>', '')
    $s = [System.Net.WebUtility]::HtmlDecode($s).Trim()
    return $s
}
function Parse-CellNumber {
    param([string]$Value, [int]$Decimals = 2)
    if($null -eq $Value){ return '' }
    $normalized = ($Value -replace '[\s\u00a0]', '').Replace(',', '')
    $m = [regex]::Match($normalized, '[-]?\d+\.?\d*')
    if(-not $m.Success){ return '' }
    return [math]::Round([double]$m.Value, $Decimals)
}
function Parse-CountFromCell {
    param([string]$Value)
    if($null -eq $Value){ return '' }
    $normalized = ($Value -replace '[\s\u00a0]', '').Replace(',', '')
    $m = [regex]::Match($normalized, '^(-?\d+)')
    if(-not $m.Success){ return '' }
    return [int]$m.Value
}
function Parse-CountPercentPair {
    param([string]$Value)
    $result = @{count=''; percent=''; amount=''}
    if([string]::IsNullOrWhiteSpace($Value)){ return $result }
    $normalized = ($Value -replace '[\s\u00a0]', '').Replace(',', '')
    $m = [regex]::Match($normalized, '(-?[\d.]+)\s*\(([-+]?[0-9.]+)%\)')
    if($m.Success){
        $result.amount = $m.Groups[1].Value
        $result.percent = $m.Groups[2].Value
        return $result
    }
    $m2 = [regex]::Match($normalized, '(-?[\d.]+)\s*\((\d+)\)')
    if($m2.Success){
        $result.amount = $m2.Groups[1].Value
        $result.percent = ''
        $result.count = $m2.Groups[2].Value
        return $result
    }
    return $result
}

function Split-ValueAndPct {
    param([string]$Value)
    if($Value -match '([0-9 .-]+)\s*\(([-0-9.]+)%\)'){
        return @(($Matches[1] -replace ' ', ''), $Matches[2])
    }
    return @(($Value -replace ' ', ''), '')
}

function Get-ReportMetrics {
    param([string]$ReportPath)
    $metrics = @{
        net_profit=''; profit_factor=''; max_balance_dd=''; max_balance_dd_pct=''; max_equity_dd=''; max_equity_dd_pct=''; relative_equity_dd=''; relative_equity_dd_pct=''; total_trades=''; win_rate=''; buy_trades=''; sell_trades=''; max_consecutive_wins=''; max_consecutive_losses=''; max_consecutive_wins_count=''; max_consecutive_losses_count=''
    }
    if([string]::IsNullOrWhiteSpace($ReportPath) -or !(Test-Path -LiteralPath $ReportPath)){ return $metrics }
    $html = [System.IO.File]::ReadAllText($ReportPath, [System.Text.Encoding]::Default)
    $matches = [regex]::Matches($html, '<td[^>]*>(.*?)</td>', 'Singleline')
    $cells = New-Object System.Collections.Generic.List[string]
    foreach($m in $matches){
        $cell = Clean-CellText $m.Groups[1].Value
        if($cell.Length -gt 0){ [void]$cells.Add($cell) }
    }
    for($i=0; $i -lt ($cells.Count - 1); $i++){
        $label = $cells[$i]
        $val = $cells[$i+1]
        if($label -match '总净盈利') { $metrics.net_profit = ($val -replace ' ', '') }
        elseif($label -match '盈利因子') { $metrics.profit_factor = $val }
        elseif($label -match '最大结余亏损') {
            $pair = Split-ValueAndPct $val
            $metrics.max_balance_dd = $pair[0]
            $metrics.max_balance_dd_pct = $pair[1]
        }
        elseif($label -match '最大净值亏损') {
            $pair = Split-ValueAndPct $val
            $metrics.max_equity_dd = $pair[0]
            $metrics.max_equity_dd_pct = $pair[1]
        }
        elseif($label -match '相对净值亏损') {
            if($val -match '([-0-9.]+)%\s*\(([-0-9 .]+)\)'){
                $metrics.relative_equity_dd_pct = $Matches[1]
                $metrics.relative_equity_dd = ($Matches[2] -replace ' ', '')
            } else { $metrics.relative_equity_dd = $val }
        }
        elseif($label -match '交易总计') { $metrics.total_trades = $val }
        elseif($label -match '卖出交易|Short trades|Short Deals') {
            $pair = Parse-CountPercentPair $val
            $metrics.sell_trades = Parse-CountFromCell $val
            if($pair.percent){ $metrics.sell_trades_pct = $pair.percent }
        }
        elseif($label -match '买入交易|Buy trades|Long trades|Buy Deals') {
            $pair = Parse-CountPercentPair $val
            $metrics.buy_trades = Parse-CountFromCell $val
            if($pair.percent){ $metrics.buy_trades_pct = $pair.percent }
        }
        elseif($label -match '极大值\s*连续获利|Maximal consecutive profits|Maximum consecutive profits|最大值 连续获利') {
            $pair = Parse-CountPercentPair $val
            $metrics.max_consecutive_wins = $pair.amount
            if($pair.count){ $metrics.max_consecutive_wins_count = $pair.count }
            else {
                $countMatch = [regex]::Match($val.Replace(' ',''), '\((\d+)\)')
                if($countMatch.Success){ $metrics.max_consecutive_wins_count = $countMatch.Groups[1].Value }
            }
        }
        elseif($label -match '极大值\s*连续亏损|Maximal consecutive losses|Maximum consecutive losses|最大值 连续亏损|极大值 连续亏损') {
            $pair = Parse-CountPercentPair $val
            $metrics.max_consecutive_losses = $pair.amount
            if($pair.count){ $metrics.max_consecutive_losses_count = $pair.count }
            else {
                $countMatch = [regex]::Match($val.Replace(' ',''), '\((\d+)\)')
                if($countMatch.Success){ $metrics.max_consecutive_losses_count = $countMatch.Groups[1].Value }
            }
        }
        elseif($label -match '盈利交易') {
            if($val -match '\(([-0-9.]+)%\)'){ $metrics.win_rate = $Matches[1] }
        }
    }
    return $metrics
}

function Write-TesterConfig {
    param(
        [string]$ConfigPath,
        [string]$ExpertFileName,
        [string]$TesterSetFileName,
        [string]$FromDate,
        [string]$ToDate,
        [string]$ReportName,
        [hashtable]$ExtraIni
    )
    if($null -eq $ExtraIni){ $ExtraIni = @{} }
    $extraLines = New-Object System.Text.StringBuilder
    foreach($k in $ExtraIni.Keys){
        $v = $ExtraIni[$k]
        if([string]::IsNullOrWhiteSpace($k)){ continue }
        [void]$extraLines.AppendLine(('{0}={1}' -f $k, $v))
    }
    $content = @"
[Tester]
Expert=$ExpertFileName
ExpertParameters=$TesterSetFileName
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
ExecutionMode=100
OptimizationCriterion=0
Visual=0
Report=SingleEAReports\$ReportName
ReplaceReport=1
ShutdownTerminal=1
$($extraLines.ToString())
"@
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ConfigPath) | Out-Null
    [System.IO.File]::WriteAllText($ConfigPath, $content, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-Mt5Backtest {
    param(
        [string]$RunId,[string]$Version,[string]$Window,[string]$Stage,[int]$Round,[int]$CaseId,
        [string]$SourceFile,[string]$ExpertFileName,[string]$Ex5File,[string]$BaseSet,[hashtable]$Overrides,
        [string]$FromDate,[string]$ToDate,[string]$CandidateClass,[string]$Decision,[string]$Notes,[hashtable]$ConfigOverrides=[hashtable]::new(),[int]$TimeoutSeconds = 900
    )
    $archiveDir = Join-Path $Hcsj "backtest_archive\$Version\$Window\$RunId"
    $setDir = Join-Path $Hcsj "set\$Version\$Window"
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
    New-Item -ItemType Directory -Force -Path $setDir | Out-Null
    New-Item -ItemType Directory -Force -Path $TesterSetDir | Out-Null
    New-Item -ItemType Directory -Force -Path $SingleReportDir | Out-Null

    $setFileName = "$RunId.set"
    $archiveSet = Join-Path $setDir $setFileName
    New-SetFile -BaseSet $BaseSet -OutSet $archiveSet -Overrides $Overrides
    $testerSet = Join-Path $TesterSetDir $setFileName
    Copy-Item -LiteralPath $archiveSet -Destination $testerSet -Force

    $configPath = Join-Path $archiveDir "$RunId.ini"
    $reportName = $RunId
    Write-TesterConfig -ConfigPath $configPath -ExpertFileName $ExpertFileName -TesterSetFileName $setFileName -FromDate $FromDate -ToDate $ToDate -ReportName $reportName -ExtraIni $ConfigOverrides

    $reportSrc = Join-Path $SingleReportDir "$reportName.htm"
    if(Test-Path -LiteralPath $reportSrc){ Remove-Item -LiteralPath $reportSrc -Force }
    $reportDst = Join-Path $archiveDir "$RunId.htm"
    $notesPath = Join-Path $archiveDir "$RunId`_notes.md"

    $status = 'started'
    $start = Get-Date
    try {
        $p = Start-Process -FilePath $Terminal -ArgumentList @('/portable', "/config:$configPath") -WorkingDirectory $Mt5 -WindowStyle Hidden -PassThru
        $finished = $p.WaitForExit($TimeoutSeconds * 1000)
        if(-not $finished){
            try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
            $status = 'timeout'
        } else { $status = 'terminal_exit_' + $p.ExitCode }
    } catch {
        $status = 'launch_failed'
        $Notes = $Notes + '; launch error: ' + $_.Exception.Message
    }
    Start-Sleep -Seconds 2
    if(Test-Path -LiteralPath $reportSrc){
        Copy-Item -LiteralPath $reportSrc -Destination $reportDst -Force
        $status = 'completed'
    } else {
        $reportDst = ''
        if($status -eq 'started'){ $status = 'no_report' }
        elseif($status -like 'terminal_exit_*'){ $status = $status + '_no_report' }
    }

    $metrics = if($reportDst){ Get-ReportMetrics -ReportPath $reportDst } else { Get-ReportMetrics -ReportPath '' }
    $metricCsv = Join-Path $archiveDir "$RunId`_metrics.csv"
    $metricHeader = 'run_id,net_profit,profit_factor,max_balance_dd,max_balance_dd_pct,max_equity_dd,max_equity_dd_pct,relative_equity_dd,relative_equity_dd_pct,total_trades,win_rate,buy_trades,sell_trades,max_consecutive_winning_trades,max_consecutive_losing_trades,max_consecutive_winning_count,max_consecutive_losing_count,status'
    $metricLine = (@(
        $RunId,
        $metrics.net_profit,
        $metrics.profit_factor,
        $metrics.max_balance_dd,
        $metrics.max_balance_dd_pct,
        $metrics.max_equity_dd,
        $metrics.max_equity_dd_pct,
        $metrics.relative_equity_dd,
        $metrics.relative_equity_dd_pct,
        $metrics.total_trades,
        $metrics.win_rate,
        $metrics.buy_trades,
        $metrics.sell_trades,
        $metrics.max_consecutive_wins,
        $metrics.max_consecutive_losses,
        $metrics.max_consecutive_wins_count,
        $metrics.max_consecutive_losses_count,
        $status
    ) | ForEach-Object { CsvEscape $_ }) -join ','
    [System.IO.File]::WriteAllText($metricCsv, $metricHeader + [Environment]::NewLine + $metricLine + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($notesPath, "# $RunId`n`nStatus: $status`n`nNotes: $Notes`n", [System.Text.UTF8Encoding]::new($false))

    Append-MatrixRow @{
        run_id=$RunId; version=$Version; window=$Window; stage=$Stage; round=$Round; case_id=$CaseId; status=$status; source_file=$SourceFile; ex5_file=$Ex5File; set_file=$archiveSet; config_file=$configPath; report_file=$reportDst; start_date=$FromDate; end_date=$ToDate; symbol=$Symbol; timeframe=$Period; model=$Model; spread=$Spread; deposit=$Deposit; leverage=$Leverage; net_profit=$metrics.net_profit; profit_factor=$metrics.profit_factor; max_balance_dd=$metrics.max_balance_dd; max_balance_dd_pct=$metrics.max_balance_dd_pct; max_equity_dd=$metrics.max_equity_dd; max_equity_dd_pct=$metrics.max_equity_dd_pct; relative_equity_dd=$metrics.relative_equity_dd; relative_equity_dd_pct=$metrics.relative_equity_dd_pct; total_trades=$metrics.total_trades; win_rate=$metrics.win_rate; robustness_score=''; candidate_class=$CandidateClass; decision=$Decision; notes=$Notes
    }
    return [pscustomobject]@{RunId=$RunId; Status=$status; NetProfit=$metrics.net_profit; PF=$metrics.profit_factor; Trades=$metrics.total_trades; Report=$reportDst; Metrics=$metricCsv; Config=$configPath; Set=$archiveSet; Seconds=[int]((Get-Date)-$start).TotalSeconds}
}
