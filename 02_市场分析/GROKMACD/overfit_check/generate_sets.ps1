$mt5 = Get-ChildItem "D:\" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like 'MT5*' } |
    ForEach-Object { Join-Path $_.FullName "MetaTrader 5" } |
    Where-Object { Test-Path (Join-Path $_ "terminal64.exe") } |
    Select-Object -First 1
if (-not $mt5) { throw "MT5 terminal not found" }

$profileDir = Join-Path $mt5 "MQL5\Profiles\Tester"
$outDir = "E:\grokmacd\overfit_check\sets"
$templatePath = "E:\grokmacd\SniperTrendEA_v8.61_BEST_PF.set"
New-Item -ItemType Directory -Force -Path $outDir, $profileDir | Out-Null
if (-not (Test-Path $templatePath)) { throw "Template set not found: $templatePath" }

function New-CustomSetFile {
    param(
        [string]$Name,
        [string]$Comment,
        [hashtable]$Replacements
    )
    $lines = @(
        "; $Comment",
        "; Overfit check set generated $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
        ";"
    )
    Get-Content $templatePath | Where-Object { $_ -match '^Inp' } | ForEach-Object {
        if ($_ -match '^(Inp\w+)=(.+)$') {
            $key = $Matches[1]
            if ($Replacements.ContainsKey($key)) {
                if ($key -eq 'InpComment') {
                    $lines += "$key=$($Replacements[$key])"
                } else {
                    $parts = $Matches[2] -split '\|\|'
                    $parts[0] = $Replacements[$key]
                    $parts[1] = $Replacements[$key]
                    $lines += "$key=$($parts -join '||')"
                }
            } else {
                $lines += $_
            }
        }
    }
    $text = ($lines -join "`r`n") + "`r`n"
    foreach ($p in @((Join-Path $outDir "$Name.set"), (Join-Path $profileDir "$Name.set"))) {
        Set-Content -Path $p -Value $text -Encoding ASCII
    }
}

New-CustomSetFile "SniperTrendEA_v8.61_PASS1577" "Pass1577 PF=4.05 (BEST_PF base)" @{ InpComment = "SniperEA_PASS1577" }
New-CustomSetFile "SniperTrendEA_v8.61_PASS1632" "Pass1632 PF=3.90" @{ InpTrailingStart = "4.0"; InpComment = "SniperEA_PASS1632" }
New-CustomSetFile "SniperTrendEA_v8.61_PASS1729" "Pass1729 PF=3.87" @{ InpTrailingStep = "3.5"; InpComment = "SniperEA_PASS1729" }
New-CustomSetFile "SniperTrendEA_v8.61_PASS1581" "Pass1581 PF=3.87" @{ InpMA200BufferATR = "0.2"; InpBodyRatio = "0.55"; InpComment = "SniperEA_PASS1581" }
New-CustomSetFile "SniperTrendEA_v8.61_PASS1639" "Pass1639 PF=3.72" @{ InpMA200BufferATR = "0.4"; InpMaxCandleATR = "2.5"; InpComment = "SniperEA_PASS1639" }

$balanced = @"
; BALANCED preset overfit check
InpFilterPreset=1||1||0||3||N
InpFastEMA=12||12||1||120||N
InpSlowEMA=26||26||1||260||N
InpSignalSMA=9||9||1||90||N
InpMA200Period=200||200||1||2000||N
InpUseMA200Filter=true||false||0||true||N
InpMA200BufferATR=0.2||0.2||0.050000||5.000000||N
InpBodyRatio=0.55||0.55||0.060000||6.000000||N
InpMaxCandleATR=3.0||3.0||0.200000||20.000000||N
InpMaxOppositeShadow=0.30||0.30||0.015000||1.500000||N
InpRequireFollowThrough=false||false||0||true||N
InpFollowThroughBars=3||3||1||30||N
InpConfirmBars=3||3||1||30||N
InpRequireMACDDir=false||false||0||true||N
InpUseWickConflictFilter=true||false||0||true||N
InpMaxWickToBodyRatio=1.5||1.5||0.150000||15.000000||N
InpRequireMomentumDominance=true||false||0||true||N
InpMomentumLookback=5||5||1||50||N
InpMomentumMinRatio=0.85||0.85||0.085000||8.500000||N
InpUseADX=false||false||0||true||N
InpADXPeriod=14||14||1||140||N
InpADXThreshold=25.0||25.0||2.500000||250.000000||N
InpUseTimeFilter=false||false||0||true||N
InpStartHour=8||8||1||80||N
InpEndHour=20||20||1||200||N
InpUseATRFilter=false||false||0||true||N
InpATRFilterPeriod=20||20||1||200||N
InpATRFilterRatio=1.0||1.0||0.100000||10.000000||N
InpUseDailyFilter=false||false||0||true||N
InpRiskPercent=0.5||0.5||0.050000||5.000000||N
InpATRMultiplier=1.5||1.5||0.100000||10.000000||N
InpATRPeriod=14||14||1||140||N
InpTrailingStart=5.0||5.0||0.450000||45.000000||N
InpTrailingStep=2.5||2.5||0.300000||30.000000||N
InpMaxPositions=1||1||1||10||N
InpUseIgnitionExit=true||false||0||true||N
InpIgnitionMaxBars=3||3||1||30||N
InpIgnitionEngulfRatio=0.85||0.85||0.085000||8.500000||N
InpIgnitionMaxLossATR=1.0||1.0||0.100000||10.000000||N
InpMagicNumber=20260618||20260618||1||202606180||N
InpComment=SniperEA_BALANCED
InpEnableBuy=true||false||0||true||N
InpEnableSell=true||false||0||true||N
InpDebugMode=false||false||0||true||N
"@

$conservative = $balanced -replace 'InpFilterPreset=1','InpFilterPreset=0' `
    -replace 'InpMA200BufferATR=0.2','InpMA200BufferATR=0.0' `
    -replace 'InpBodyRatio=0.55','InpBodyRatio=0.60' `
    -replace 'InpMaxCandleATR=3.0','InpMaxCandleATR=2.5' `
    -replace 'InpMaxOppositeShadow=0.30','InpMaxOppositeShadow=0.20' `
    -replace 'InpConfirmBars=3','InpConfirmBars=4' `
    -replace 'InpMaxWickToBodyRatio=1.5','InpMaxWickToBodyRatio=1.0' `
    -replace 'InpMomentumMinRatio=0.85','InpMomentumMinRatio=1.0' `
    -replace 'SniperEA_BALANCED','SniperEA_CONSERVATIVE'

foreach ($pair in @(
    @{Name='SniperTrendEA_v8.61_BALANCED'; Text=$balanced},
    @{Name='SniperTrendEA_v8.61_CONSERVATIVE'; Text=$conservative}
)) {
    Set-Content (Join-Path $outDir "$($pair.Name).set") -Value $pair.Text -Encoding ASCII
    Set-Content (Join-Path $profileDir "$($pair.Name).set") -Value $pair.Text -Encoding ASCII
}

Write-Host "Generated 7 set files in $outDir and $profileDir"