$mt5 = Get-ChildItem "D:\" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like 'MT5*' } |
    ForEach-Object { Join-Path $_.FullName "MetaTrader 5" } |
    Where-Object { Test-Path (Join-Path $_ "terminal64.exe") } |
    Select-Object -First 1
if (-not $mt5) { throw "MT5 terminal not found" }

$reportRoot = Join-Path $mt5 "SingleEAReports\overfit_check_grokmacd_v861"
$outCsv = "E:\grokmacd\overfit_check\overfit_results.csv"

function Get-Mt5Metrics([string]$htmPath) {
    if (-not (Test-Path $htmPath)) { return $null }
    $t = [IO.File]::ReadAllText($htmPath, [Text.Encoding]::GetEncoding(936))
    $cells = [regex]::Matches($t, '<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>\s*<b>([^<]+)</b>')
    if ($cells.Count -lt 33) { return $null }

    $pf = $cells[21].Groups[2].Value.Trim()
    $trades = $cells[32].Groups[2].Value.Trim()
    $profit = $cells[12].Groups[2].Value.Trim()
    $dd = $cells[17].Groups[2].Value.Trim()
    $sharpe = $cells[25].Groups[2].Value.Trim()

    [PSCustomObject]@{
        PF = [double]($pf -replace '[^\d.\-]','')
        Trades = [int]($trades -replace '[^\d]','')
        NetProfit = $profit
        MaxDD = $dd
        Sharpe = [double]($sharpe -replace '[^\d.\-]','')
    }
}

$rows = @()
Get-ChildItem $reportRoot -Filter "overfit_*.htm" | ForEach-Object {
    if ($_.Name -notmatch '^overfit_(.+)_(\d{4}_\d{4})\.htm$') { return }
    $m = Get-Mt5Metrics $_.FullName
    if ($null -eq $m) { return }
    $rows += [PSCustomObject]@{
        Group = $Matches[1]
        Period = $Matches[2]
        PF = $m.PF
        Trades = $m.Trades
        NetProfit = $m.NetProfit
        MaxDD = $m.MaxDD
        Sharpe = $m.Sharpe
        Report = $_.FullName
    }
}

if ($rows.Count -eq 0) { throw "No overfit reports parsed from $reportRoot" }

$rows | Export-Csv $outCsv -NoTypeInformation -Encoding UTF8

Write-Host "`n=== Results Matrix (PF by Group x Period) ==="
$rows | Sort-Object Group, Period | Format-Table Group, Period, PF, Trades, MaxDD, Sharpe -AutoSize

$scored = $rows | Group-Object Group | ForEach-Object {
    $items = $_.Group
    $oos = $items | Where-Object { $_.Period -in @('2015_2019','2025_2026') }
    $ins = $items | Where-Object { $_.Period -eq '2020_2025' } | Select-Object -First 1
    $oosPf = ($oos | Measure-Object PF -Average).Average
    $insPf = $ins.PF
    $oosTrades = ($oos | Measure-Object Trades -Sum).Sum
    $maxDd = ($items | ForEach-Object { if ($_.MaxDD -match '\(([\d.]+)%\)') { [double]$Matches[1] } } | Measure-Object -Maximum).Maximum
    $pfRatio = if ($oosPf -and $insPf -gt 0) { [math]::Round($oosPf / $insPf, 2) } else { $null }
    $overfitFlag = if ($pfRatio -lt 0.6) { 'HIGH' } elseif ($pfRatio -lt 0.85) { 'MED' } else { 'LOW' }
    [PSCustomObject]@{
        Group = $_.Name
        PF_2015_2019 = ($items | Where-Object Period -eq '2015_2019').PF
        PF_2020_2025 = $insPf
        PF_2025_2026 = ($items | Where-Object Period -eq '2025_2026').PF
        InSamplePF = [math]::Round($insPf, 2)
        OutSamplePF = [math]::Round($oosPf, 2)
        OOS_InSample_Ratio = $pfRatio
        OutSampleTrades = $oosTrades
        MaxDDPct = if ($maxDd) { [math]::Round($maxDd, 2) } else { $null }
        RobustScore = [math]::Round(($oosPf * 0.7 + $insPf * 0.3) - ($(if ($maxDd) { $maxDd } else { 0 }) * 0.01), 2)
        OverfitFlag = $overfitFlag
    }
} | Sort-Object RobustScore -Descending

Write-Host "`n=== Robust Ranking (OOS-weighted) ==="
$scored | Format-Table -AutoSize
$scored | Export-Csv "E:\grokmacd\overfit_check\robust_ranking.csv" -NoTypeInformation -Encoding UTF8