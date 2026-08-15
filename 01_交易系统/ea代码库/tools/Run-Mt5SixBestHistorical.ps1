param(
  [string]$Symbol = 'XAUUSD',
  [string]$FromDate = '2015.01.01',
  [string]$ToDate = '2019.12.31',
  [string]$RunId = 'six_best_2015_2019_20260617',
  [int]$Model = 0,
  [int]$TimeoutMinutes = 60
)

$ErrorActionPreference = 'Stop'

$base = ('D:\MT5' + [char]0x6D4B + [char]0x8BD5 + '\MetaTrader 5')
$singleRunner = Join-Path $PSScriptRoot 'Run-Mt5SingleEaTest.ps1'
$outRoot = Join-Path $base "SingleEAReports\$RunId"
$runLogCsv = Join-Path $outRoot 'Six_Best_Run_Log.csv'
$summaryCsv = Join-Path $outRoot 'Six_Best_Test_Queue.csv'
$stdoutDir = Join-Path $outRoot 'runner_stdout'

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 100) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 90) + '_' + $hash
}

function U([int[]]$CodePoints) {
  return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Get-Prop($Object, [string]$Name) {
  if($null -eq $Object) { return '' }
  $prop = $Object.PSObject.Properties[$Name]
  if($prop) { return $prop.Value }
  return ''
}

$C = @{
  ParamFile=(U @(0x53C2,0x6570,0x6587,0x4EF6))
  Period=(U @(0x5468,0x671F))
  FromDate=(U @(0x5F00,0x59CB,0x65E5,0x671F))
  ToDate=(U @(0x7ED3,0x675F,0x65E5,0x671F))
}

function Get-ExistingKeySet([string]$CsvPath) {
  $keys = New-Object 'System.Collections.Generic.HashSet[string]'
  if(Test-Path -LiteralPath $CsvPath) {
    Import-Csv -LiteralPath $CsvPath | ForEach-Object {
      [void]$keys.Add("$($_.EA)|$(Get-Prop $_ $C.ParamFile)|$(Get-Prop $_ $C.Period)|$(Get-Prop $_ $C.FromDate)|$(Get-Prop $_ $C.ToDate)")
    }
  }
  return ,$keys
}

function Assert-NoMt5() {
  $running = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq 'terminal64.exe' -and $_.ExecutablePath -like "$base*") -or $_.Name -eq 'metatester64.exe'
  }
  if($running) { throw "MT5/metatester process is already running. Stop it before continuing." }
}

if(!(Test-Path -LiteralPath $singleRunner)) {
  throw "Single runner not found: $singleRunner"
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
New-Item -ItemType Directory -Force -Path $stdoutDir | Out-Null
if(!(Test-Path -LiteralPath $runLogCsv)) {
  'Time,Status,ExitCode,EA,Expert,SetFile,Symbol,Period,FromDate,ToDate,StdOut,StdErr' | Set-Content -LiteralPath $runLogCsv -Encoding UTF8
}

$periods = @('H1','H4')
$eas = @(
  [pscustomobject]@{
    EA='SniperTrendEA_v8.7_RiskFix'
    Expert='SniperTrendEA_v8.7_RiskFix.ex5'
    SetFile='SniperTrendEA_v8.7_RiskFix_ROBUST_20260617.set'
  },
  [pscustomobject]@{
    EA='OmniAggressiveHedgeEngine'
    Expert='OmniFuturesSuite\OmniAggressiveHedgeEngine.ex5'
    SetFile='OmniAggressiveHedgeEngine_ROBUST_20260617.set'
  },
  [pscustomobject]@{
    EA='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED'
    Expert='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED.ex5'
    SetFile='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED_LOW_SAMPLE_ROBUST_20260617.set'
  },
  [pscustomobject]@{
    EA='BBRSI-v1.6'
    Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'
    SetFile='BBRSI-v1.6_XAUUSD_H1_seq01.set'
  },
  [pscustomobject]@{
    EA='3MAF-v1.5'
    Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'
    SetFile='3MAF-v1.5_XAUUSD_H4_seq02.set'
  },
  [pscustomobject]@{
    EA='DHLAOS-v1.5'
    Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'
    SetFile='DHLAOS-v1.5_XAUUSD_H4_seq01.set'
  }
)

$queue = New-Object System.Collections.Generic.List[object]
foreach($ea in $eas) {
  foreach($period in $periods) {
    $queue.Add([pscustomobject]@{
      EA=$ea.EA
      Expert=$ea.Expert
      SetFile=$ea.SetFile
      Symbol=$Symbol
      Period=$period
      FromDate=$FromDate
      ToDate=$ToDate
    })
  }
}
$queue | Export-Csv -LiteralPath $summaryCsv -NoTypeInformation -Encoding UTF8

$resultCsv = Join-Path $outRoot 'EA_Test_Log.csv'
$existing = Get-ExistingKeySet $resultCsv
$total = $queue.Count
$index = 0
$ran = 0
$skipped = 0
$failed = 0

foreach($item in $queue) {
  $index++
  $key = "$($item.EA)|$($item.SetFile)|$($item.Period)|$($item.FromDate)|$($item.ToDate)"
  if($existing.Contains($key)) {
    $skipped++
    Write-Host "[$index/$total] SKIP $($item.EA) $($item.Period)"
    continue
  }

  Assert-NoMt5
  $ran++
  Write-Host "[$index/$total] RUN $($item.EA) $($item.Period)"
  $safe = Convert-ToSafeName "$($item.EA)_$($item.Period)_$($item.FromDate)_$($item.ToDate)"
  $stdout = Join-Path $stdoutDir ($safe + '.out.txt')
  $stderr = Join-Path $stdoutDir ($safe + '.err.txt')
  $args = @(
    '-NoProfile',
    '-ExecutionPolicy','Bypass',
    '-File', $singleRunner,
    '-Expert', $item.Expert,
    '-EAName', $item.EA,
    '-Symbol', $item.Symbol,
    '-Period', $item.Period,
    '-FromDate', $item.FromDate,
    '-ToDate', $item.ToDate,
    '-RunId', $RunId,
    '-Model', [string]$Model,
    '-TimeoutMinutes', [string]$TimeoutMinutes,
    '-SetFile', $item.SetFile
  )
  $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $exitCode = $p.ExitCode
  $status = if($exitCode -eq 0) { 'Done' } else { 'Failed' }
  if($exitCode -ne 0) { $failed++ }
  [pscustomobject]@{
    Time=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Status=$status
    ExitCode=$exitCode
    EA=$item.EA
    Expert=$item.Expert
    SetFile=$item.SetFile
    Symbol=$item.Symbol
    Period=$item.Period
    FromDate=$item.FromDate
    ToDate=$item.ToDate
    StdOut=$stdout
    StdErr=$stderr
  } | Export-Csv -LiteralPath $runLogCsv -Append -NoTypeInformation -Encoding UTF8
  $existing = Get-ExistingKeySet $resultCsv
}

[pscustomobject]@{
  RunId=$RunId
  Symbol=$Symbol
  FromDate=$FromDate
  ToDate=$ToDate
  Total=$total
  Ran=$ran
  Skipped=$skipped
  Failed=$failed
  OutputRoot=$outRoot
  ResultCsv=$resultCsv
  RunLogCsv=$runLogCsv
}
