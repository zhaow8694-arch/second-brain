param(
  [string]$Folder = 'D:\MT5测试\MetaTrader 5\MQL5\Experts\metatrader5-master',
  [string]$Symbol = 'XAUUSD',
  [string]$RunId = 'metatrader5_master_matrix_20260617',
  [int]$TimeoutMinutes = 20,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$base = 'D:\MT5测试\MetaTrader 5'
$expertsRoot = Join-Path $base 'MQL5\Experts'
$singleRunner = 'E:\ea代码库\tools\Run-Mt5SingleEaTest.ps1'
$outRoot = Join-Path $base "SingleEAReports\$RunId"
$masterCsv = Join-Path $outRoot 'EA_Test_Log.csv'
$queueCsv = Join-Path $outRoot 'EA_Test_Queue.csv'
$runLogCsv = Join-Path $outRoot 'EA_Run_Log.csv'
$stdoutDir = Join-Path $outRoot 'runner_stdout'

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 110) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 100) + '_' + $hash
}

function Get-ExistingKeys([string]$csvPath) {
  $keys = New-Object 'System.Collections.Generic.HashSet[string]'
  if(Test-Path -LiteralPath $csvPath) {
    Import-Csv -LiteralPath $csvPath | ForEach-Object {
      [void]$keys.Add("$($_.EA)|$($_.品种)|$($_.周期)|$($_.开始日期)|$($_.结束日期)")
    }
  }
  return ,$keys
}

if(!(Test-Path -LiteralPath $Folder)) {
  throw "Folder not found: $Folder"
}
if(!(Test-Path -LiteralPath $singleRunner)) {
  throw "Single runner not found: $singleRunner"
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
New-Item -ItemType Directory -Force -Path $stdoutDir | Out-Null

$dateCases = @(
  [pscustomobject]@{ Name='2025'; From='2025.01.01'; To='2025.12.31' },
  [pscustomobject]@{ Name='2020_2025'; From='2020.01.01'; To='2025.12.31' }
)
$periods = @('H1','H4')

$eas = Get-ChildItem -LiteralPath $Folder -Recurse -File -Filter '*.ex5' |
  Sort-Object FullName |
  ForEach-Object {
    $relative = $_.FullName.Substring($expertsRoot.Length + 1)
    $nameNoExt = $relative.Substring(0, $relative.Length - $_.Extension.Length)
    [pscustomobject]@{
      Name = Convert-ToSafeName $nameNoExt
      Expert = $relative
      FullName = $_.FullName
    }
  }

$queue = New-Object System.Collections.Generic.List[object]
foreach($dateCase in $dateCases) {
  foreach($period in $periods) {
    foreach($ea in $eas) {
      $queue.Add([pscustomobject]@{
        Case = $dateCase.Name
        FromDate = $dateCase.From
        ToDate = $dateCase.To
        Period = $period
        Symbol = $Symbol
        EA = $ea.Name
        Expert = $ea.Expert
        FullName = $ea.FullName
        Key = "$($ea.Name)|$Symbol|$period|$($dateCase.From)|$($dateCase.To)"
      })
    }
  }
}

$queue | Select-Object Case,FromDate,ToDate,Period,Symbol,EA,Expert,FullName |
  Export-Csv -LiteralPath $queueCsv -NoTypeInformation -Encoding UTF8

if(!(Test-Path -LiteralPath $runLogCsv)) {
  '时间,状态,退出码,Case,EA,Expert,Symbol,Period,FromDate,ToDate,StdOut,StdErr' |
    Set-Content -LiteralPath $runLogCsv -Encoding UTF8
}

$existing = Get-ExistingKeys $masterCsv
$total = $queue.Count
$done = 0
$skipped = 0
$ran = 0
$failed = 0

foreach($item in $queue) {
  $done++
  if($existing.Contains($item.Key)) {
    $skipped++
    Write-Host "[$done/$total] SKIP $($item.Case) $($item.Period) $($item.EA)"
    continue
  }

  if($DryRun) {
    Write-Host "[$done/$total] DRYRUN $($item.Case) $($item.Period) $($item.EA)"
    continue
  }

  $ran++
  Write-Host "[$done/$total] RUN $($item.Case) $($item.Period) $($item.EA)"
  $safeCaseName = Convert-ToSafeName "$($item.Case)_$($item.Period)_$($item.EA)"
  $stdout = Join-Path $stdoutDir ($safeCaseName + '.out.txt')
  $stderr = Join-Path $stdoutDir ($safeCaseName + '.err.txt')

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
    '-Model', '0',
    '-TimeoutMinutes', [string]$TimeoutMinutes
  )

  $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $exitCode = $p.ExitCode
  $status = if($exitCode -eq 0) { '完成' } else { '失败' }
  if($exitCode -ne 0) { $failed++ }

  $row = [pscustomobject]@{
    '时间'=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    '状态'=$status
    '退出码'=$exitCode
    'Case'=$item.Case
    'EA'=$item.EA
    'Expert'=$item.Expert
    'Symbol'=$item.Symbol
    'Period'=$item.Period
    'FromDate'=$item.FromDate
    'ToDate'=$item.ToDate
    'StdOut'=$stdout
    'StdErr'=$stderr
  }
  $row | Export-Csv -LiteralPath $runLogCsv -Append -NoTypeInformation -Encoding UTF8

  $existing = Get-ExistingKeys $masterCsv
}

[pscustomobject]@{
  Folder=$Folder
  RunId=$RunId
  EAFileCount=$eas.Count
  TotalCases=$total
  Ran=$ran
  Skipped=$skipped
  Failed=$failed
  QueueCsv=$queueCsv
  MasterCsv=$masterCsv
  RunLogCsv=$runLogCsv
  OutputRoot=$outRoot
}
