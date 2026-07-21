# SniperTrendEA v8.61 overfit verification batch runner
# 7 configs x 3 periods = 21 backtests

$ErrorActionPreference = "Stop"
$lockFile = "E:\grokmacd\overfit_check\.overfit.lock"

if (Test-Path $lockFile) {
    $lockPid = Get-Content $lockFile -ErrorAction SilentlyContinue
    if ($lockPid -and (Get-Process -Id $lockPid -ErrorAction SilentlyContinue)) {
        throw "Another overfit check is already running (PID $lockPid). Wait or delete $lockFile if stale."
    }
    Remove-Item $lockFile -Force
}
Set-Content $lockFile $PID

try {
    $mt5Candidates = @(
        "D:\MT5测试\MetaTrader 5",
        (Get-ChildItem "D:\" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'MT5*' } | ForEach-Object { Join-Path $_.FullName "MetaTrader 5" } | Where-Object { Test-Path (Join-Path $_ "terminal64.exe") } | Select-Object -First 1)
    )
    $mt5 = $mt5Candidates | Where-Object { $_ -and (Test-Path (Join-Path $_ "terminal64.exe")) } | Select-Object -First 1
    if (-not $mt5) { throw "MT5 terminal not found" }

    $eaEx5 = Join-Path $mt5 "MQL5\Experts\SniperTrendEA_v8.6.ex5"
    if (-not (Test-Path $eaEx5)) { throw "EA not compiled: $eaEx5" }

    subst X: /D 2>$null | Out-Null
    $substResult = cmd /c "subst X: `"$mt5`""
    if (-not (Test-Path "X:\terminal64.exe")) { throw "subst X: failed — terminal64.exe not found at X:\" }

    $terminal = "X:\terminal64.exe"
    $testerDir = "X:\Tester"
    $reportRoot = "SingleEAReports\overfit_check_grokmacd_v861"
    $localReportRoot = "E:\grokmacd\overfit_check\reports"
    $mt5ReportDir = Join-Path $mt5 $reportRoot

    New-Item -ItemType Directory -Force -Path $testerDir, $localReportRoot, $mt5ReportDir | Out-Null

    # Remove corrupted single-file artifacts from previous buggy run
    Get-ChildItem $testerDir -Filter "overfit__*" -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem $mt5ReportDir -Filter "overfit__*" -ErrorAction SilentlyContinue | Remove-Item -Force

    Write-Host "MT5: $mt5 (mapped to X:)"
    Write-Host "EA: SniperTrendEA_v8.6.ex5 ($((Get-Item $eaEx5).LastWriteTime))"

    $groups = @(
        @{ Id = "PASS1577"; Set = "SniperTrendEA_v8.61_PASS1577.set" },
        @{ Id = "PASS1632"; Set = "SniperTrendEA_v8.61_PASS1632.set" },
        @{ Id = "PASS1729"; Set = "SniperTrendEA_v8.61_PASS1729.set" },
        @{ Id = "PASS1581"; Set = "SniperTrendEA_v8.61_PASS1581.set" },
        @{ Id = "PASS1639"; Set = "SniperTrendEA_v8.61_PASS1639.set" },
        @{ Id = "BALANCED"; Set = "SniperTrendEA_v8.61_BALANCED.set" },
        @{ Id = "CONSERVATIVE"; Set = "SniperTrendEA_v8.61_CONSERVATIVE.set" }
    )

    $periods = @(
        @{ Id = "2015_2019"; From = "2015.01.01"; To = "2019.12.31" },
        @{ Id = "2020_2025"; From = "2020.01.01"; To = "2025.12.31" },
        @{ Id = "2025_2026"; From = "2025.01.01"; To = "2026.06.30" }
    )

    $jobs = @()
    foreach ($g in $groups) {
        foreach ($p in $periods) {
            $name = "overfit_$($g.Id)_$($p.Id)"
            $report = Join-Path $reportRoot $name
            $ini = @"
[Tester]
Expert=SniperTrendEA_v8.6.ex5
ExpertParameters=$($g.Set)
Symbol=XAUUSD
Period=H4
Optimization=0
Model=1
FromDate=$($p.From)
ToDate=$($p.To)
ForwardMode=0
Deposit=20000
Currency=USD
ProfitInPips=0
Leverage=100
ExecutionMode=100
OptimizationCriterion=0
Visual=0
Report=$report
ReplaceReport=1
ShutdownTerminal=1
"@
            $iniPath = Join-Path $testerDir "$name.ini"
            Set-Content -Path $iniPath -Value $ini -Encoding ASCII
            $jobs += [PSCustomObject]@{
                Name = $name
                Group = $g.Id
                Period = $p.Id
                Ini = $iniPath
                ReportHtm = Join-Path $mt5 "$report.htm"
                IniConfig = "X:\Tester\$name.ini"
            }
        }
    }

    Write-Host "=== Overfit Check: $($jobs.Count) backtests ==="

    $results = @()
    $i = 0
    foreach ($job in $jobs) {
        $i++
        Write-Host "[$i/$($jobs.Count)] $($job.Group) / $($job.Period) ..."
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $exitCode = -1
        $procError = $null
        try {
            $proc = Start-Process -FilePath $terminal -ArgumentList "/portable", "/config:$($job.IniConfig)" -Wait -PassThru -ErrorAction Stop
            $exitCode = $proc.ExitCode
        } catch {
            $procError = $_.Exception.Message
        }
        $sw.Stop()
        $reportExists = Test-Path $job.ReportHtm
        $status = if ($exitCode -eq 0 -and $reportExists) { "OK" } else { "FAIL" }
        if ($procError) { Write-Warning "  Error: $procError" }
        if (-not $reportExists) { Write-Warning "  Report missing: $($job.ReportHtm)" }

        $results += [PSCustomObject]@{
            Group = $job.Group
            Period = $job.Period
            Status = $status
            ExitCode = $exitCode
            Seconds = [math]::Round($sw.Elapsed.TotalSeconds, 1)
            Report = $job.ReportHtm
        }
    }

    $summaryPath = Join-Path $localReportRoot "run_summary.csv"
    $results | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8
    Write-Host "Run summary: $summaryPath"
    $results | Format-Table -AutoSize

    $failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
    if ($failCount -gt 0) {
        Write-Warning "$failCount / $($results.Count) backtests failed."
        exit 1
    }
}
finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    subst X: /D 2>$null | Out-Null
}