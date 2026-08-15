param(
  [string]$Symbol = 'XAUUSD',
  [string[]]$Periods = @('H1','H4'),
  [string]$SweepFromDate = '2025.01.01',
  [string]$SweepToDate = '2025.12.31',
  [string]$ValidationFromDate = '2020.01.01',
  [string]$ValidationToDate = '2025.12.31',
  [string]$RunId = 'top3_pf_settings_seq_20260617',
  [int]$Model = 0,
  [int]$TestTimeoutMinutes = 35,
  [int]$TopPerCase = 3
)

$ErrorActionPreference = 'Stop'

$base = ('D:\MT5' + [char]0x6D4B + [char]0x8BD5 + '\MetaTrader 5')
$profiles = Join-Path $base 'MQL5\Profiles\Tester'
$singleRunner = Join-Path $PSScriptRoot 'Run-Mt5SingleEaTest.ps1'
$outRoot = Join-Path $base "SingleEAReports\$RunId"
$setArchive = Join-Path $outRoot 'CandidateSets'
$stdoutDir = Join-Path $outRoot 'runner_stdout'
$progressLog = Join-Path $outRoot 'Top3_SequentialSweep_Progress.csv'
$sweepSummaryCsv = Join-Path $outRoot 'Top3_SequentialSweep_2025.csv'
$selectedCsv = Join-Path $outRoot 'Top3_SequentialSweep_SelectedForValidation.csv'
$finalCsv = Join-Path $outRoot 'Top3_SequentialSweep_ValidatedSettings.csv'

function U([int[]]$CodePoints) { return -join ($CodePoints | ForEach-Object { [char]$_ }) }
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
  NetProfit=(U @(0x51C0,0x5229,0x6DA6))
  ProfitFactor=(U @(0x76C8,0x5229,0x56E0,0x5B50))
  Trades=(U @(0x4EA4,0x6613,0x603B,0x8BA1))
  RelativeEquityDD=(U @(0x76F8,0x5BF9,0x51C0,0x503C,0x56DE,0x64A4))
  Status=(U @(0x72B6,0x6001))
  ReportPath=(U @(0x62A5,0x544A,0x8DEF,0x5F84))
  MarginShortage=(U @(0x4FDD,0x8BC1,0x91D1,0x4E0D,0x8DB3))
}

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 100) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 90) + '_' + $hash
}

function Convert-ToNumber($value) {
  if($null -eq $value) { return $null }
  $s = ([string]$value).Trim()
  if($s -eq '') { return $null }
  $s = $s -replace ' ', ''
  $s = $s -replace ',', ''
  $s = $s -replace '%', ''
  $d = 0.0
  if([double]::TryParse($s, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$d)) { return $d }
  if([double]::TryParse($s, [ref]$d)) { return $d }
  return $null
}

function Get-DDPct([string]$text) {
  if($text -match '\(([0-9.,]+)%\)') { return Convert-ToNumber $Matches[1] }
  if($text -match '([0-9.,]+)%') { return Convert-ToNumber $Matches[1] }
  return $null
}

function Write-ProgressRow([string]$Stage, [string]$Status, [string]$EA, [string]$Period, [string]$Detail) {
  $row = [pscustomobject]@{
    Time=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Stage=$Stage
    Status=$Status
    EA=$EA
    Period=$Period
    Detail=$Detail
  }
  $row | Export-Csv -LiteralPath $progressLog -Append -NoTypeInformation -Encoding UTF8
  Write-Host "[$($row.Time)] [$Stage/$Status] $EA $Period $Detail"
}

function Assert-NoMt5() {
  $running = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq 'terminal64.exe' -and $_.ExecutablePath -like "$base*") -or $_.Name -eq 'metatester64.exe'
  }
  if($running) { throw "MT5/metatester process is already running. Stop it before continuing." }
}

function Set-ParamValue([string[]]$Lines, [hashtable]$Values) {
  $updated = New-Object System.Collections.Generic.List[string]
  foreach($line in $Lines) {
    $handled = $false
    foreach($key in $Values.Keys) {
      if($line -match ('^' + [regex]::Escape($key) + '=')) {
        $right = $line.Substring($line.IndexOf('=') + 1)
        if($right -like '*||*') {
          $parts = $right -split '\|\|'
          if($parts.Count -ge 5) {
            $parts[0] = [string]$Values[$key]
            $parts[4] = 'N'
            $updated.Add("$key=$($parts -join '||')")
          } else {
            $updated.Add("$key=$($Values[$key])")
          }
        } else {
          $updated.Add("$key=$($Values[$key])")
        }
        $handled = $true
        break
      }
    }
    if(!$handled) { $updated.Add($line) }
  }
  return $updated.ToArray()
}

function New-CandidateSet($Candidate, [string]$Period) {
  $safeEA = Convert-ToSafeName $Candidate.EA
  $setName = "${safeEA}_${Symbol}_${Period}_seq$($Candidate.CandidateId).set"
  $profilePath = Join-Path $profiles $setName
  $archivePath = Join-Path $setArchive $setName
  $baseSetPath = Join-Path $profiles $Candidate.BaseSet
  if(!(Test-Path -LiteralPath $baseSetPath)) { throw "Base set not found: $baseSetPath" }
  $newLines = Set-ParamValue (Get-Content -LiteralPath $baseSetPath) $Candidate.Params
  [System.IO.File]::WriteAllText($profilePath, ($newLines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
  Copy-Item -LiteralPath $profilePath -Destination $archivePath -Force
  return [pscustomobject]@{ SetFile=$setName; ProfilePath=$profilePath; ArchivePath=$archivePath }
}

function Get-ResultRow([string]$RunIdForCsv, [string]$EAName, [string]$Period, [string]$FromDate, [string]$ToDate, [string]$SetFile) {
  $csv = Join-Path $base "SingleEAReports\$RunIdForCsv\EA_Test_Log.csv"
  if(!(Test-Path -LiteralPath $csv)) { return $null }
  return Import-Csv -LiteralPath $csv | Where-Object {
    $_.EA -eq $EAName -and
      (Get-Prop $_ $C.Period) -eq $Period -and
      (Get-Prop $_ $C.FromDate) -eq $FromDate -and
      (Get-Prop $_ $C.ToDate) -eq $ToDate -and
      (Get-Prop $_ $C.ParamFile) -eq $SetFile
  } | Select-Object -Last 1
}

function Invoke-SingleTest($Candidate, [string]$Period, [string]$FromDate, [string]$ToDate, [string]$SetFile, [string]$Stage) {
  $eaName = "$($Candidate.EA)_seq$($Candidate.CandidateId)"
  $existing = Get-ResultRow $RunId $eaName $Period $FromDate $ToDate $SetFile
  if($existing) {
    Write-ProgressRow $Stage 'SkipExisting' $Candidate.EA $Period "$SetFile $FromDate-$ToDate"
    return $existing
  }

  $safeCase = Convert-ToSafeName "$Stage`_$($Candidate.EA)_$Period`_seq$($Candidate.CandidateId)_$FromDate`_$ToDate"
  $stdout = Join-Path $stdoutDir ($safeCase + '.out.txt')
  $stderr = Join-Path $stdoutDir ($safeCase + '.err.txt')
  Write-ProgressRow $Stage 'Start' $Candidate.EA $Period "$SetFile $FromDate-$ToDate"
  $args = @(
    '-NoProfile',
    '-ExecutionPolicy','Bypass',
    '-File', $singleRunner,
    '-Expert', $Candidate.Expert,
    '-EAName', $eaName,
    '-Symbol', $Symbol,
    '-Period', $Period,
    '-FromDate', $FromDate,
    '-ToDate', $ToDate,
    '-RunId', $RunId,
    '-Model', [string]$Model,
    '-TimeoutMinutes', [string]$TestTimeoutMinutes,
    '-SetFile', $SetFile
  )
  $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $status = if($p.ExitCode -eq 0) { 'Done' } else { "Exit$p.ExitCode" }
  Write-ProgressRow $Stage $status $Candidate.EA $Period "$stdout"
  $row = Get-ResultRow $RunId $eaName $Period $FromDate $ToDate $SetFile
  if(!$row) { throw "Result row not found for $eaName $Period $FromDate-$ToDate $SetFile" }
  return $row
}

function Convert-Result($Candidate, [string]$Period, [string]$SetFile, [string]$SetPath, $Row, [string]$Stage) {
  $net = Convert-ToNumber (Get-Prop $Row $C.NetProfit)
  $pf = Convert-ToNumber (Get-Prop $Row $C.ProfitFactor)
  $trades = Convert-ToNumber (((Get-Prop $Row $C.Trades) -split ' ')[0])
  $ddPct = Get-DDPct (Get-Prop $Row $C.RelativeEquityDD)
  $status = Get-Prop $Row $C.Status
  $marginWarning = $status -like ('*' + $C.MarginShortage + '*')
  $score = -999999.0
  if($null -ne $net -and $null -ne $pf -and $null -ne $ddPct -and $null -ne $trades -and !$marginWarning) {
    $score = ($pf * [math]::Log([math]::Max($trades, 2))) + ($net / 10000.0) - ($ddPct / 25.0)
  }
  return [pscustomobject]@{
    Stage=$Stage
    EA=$Candidate.EA
    Period=$Period
    CandidateId=$Candidate.CandidateId
    SetFile=$SetFile
    SetArchivePath=$SetPath
    NetProfit=$net
    ProfitFactor=$pf
    EquityDDPct=$ddPct
    Trades=$trades
    Status=$status
    MarginWarning=$marginWarning
    RobustScore=[math]::Round($score, 6)
    Parameters=($Candidate.Params.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join '; '
    ReportPath=(Get-Prop $Row $C.ReportPath)
  }
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
New-Item -ItemType Directory -Force -Path $setArchive | Out-Null
New-Item -ItemType Directory -Force -Path $stdoutDir | Out-Null
if(!(Test-Path -LiteralPath $progressLog)) {
  'Time,Stage,Status,EA,Period,Detail' | Set-Content -LiteralPath $progressLog -Encoding UTF8
}
if(!(Test-Path -LiteralPath $singleRunner)) { throw "Single runner not found: $singleRunner" }
Assert-NoMt5

$candidates = @(
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='01'; Params=@{} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='02'; Params=@{BBLen='300';RSILen='5';TPCoef='0.8';GridVolMult='1.0';GridMaxLvl='12'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='03'; Params=@{BBLen='300';RSILen='7';TPCoef='1.2';GridVolMult='1.0';GridMaxLvl='16'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='04'; Params=@{BBLen='500';RSILen='7';TPCoef='1.2';GridVolMult='1.1';GridMaxLvl='20'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='05'; Params=@{BBLen='700';RSILen='7';TPCoef='1.2';GridVolMult='1.0';GridMaxLvl='16'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='06'; Params=@{BBLen='700';RSILen='9';TPCoef='1.6';GridVolMult='1.1';GridMaxLvl='20'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='07'; Params=@{BBLen='900';RSILen='9';TPCoef='1.6';GridVolMult='1.0';GridMaxLvl='12'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='08'; Params=@{BBLen='500';RSILen='5';TPCoef='1.6';GridVolMult='1.2';GridMaxLvl='16'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='09'; Params=@{BBLen='300';RSILen='9';TPCoef='2.0';GridVolMult='1.0';GridMaxLvl='8'} },
  [pscustomobject]@{ EA='BBRSI-v1.6'; Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'; BaseSet='BBRSI-v1.6.set'; CandidateId='10'; Params=@{BBLen='900';RSILen='13';TPCoef='1.2';GridVolMult='1.1';GridMaxLvl='24'} },

  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='01'; Params=@{} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='02'; Params=@{MA1Len='30';MA2Len='220';MA3Len='420';TPCoef='0.8';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='03'; Params=@{MA1Len='60';MA2Len='220';MA3Len='420';TPCoef='1.2';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='04'; Params=@{MA1Len='60';MA2Len='280';MA3Len='520';TPCoef='1.2';GridVolMult='1.2'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='05'; Params=@{MA1Len='90';MA2Len='280';MA3Len='620';TPCoef='1.5';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='06'; Params=@{MA1Len='90';MA2Len='340';MA3Len='720';TPCoef='1.5';GridVolMult='1.2'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='07'; Params=@{MA1Len='120';MA2Len='400';MA3Len='820';TPCoef='2.0';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='08'; Params=@{MA1Len='30';MA2Len='280';MA3Len='620';TPCoef='2.0';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='09'; Params=@{MA1Len='60';MA2Len='340';MA3Len='620';TPCoef='0.8';GridVolMult='1.4'} },
  [pscustomobject]@{ EA='3MAF-v1.5'; Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'; BaseSet='3MAF-v1.5.set'; CandidateId='10'; Params=@{MA1Len='120';MA2Len='340';MA3Len='520';TPCoef='1.5';GridVolMult='1.4'} },

  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='01'; Params=@{} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='02'; Params=@{AosPeriod='30';AosSignalPeriod='5';TPCoef='0.8';DhlNCheck='20';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='03'; Params=@{AosPeriod='30';AosSignalPeriod='9';TPCoef='1.3';DhlNCheck='40';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='04'; Params=@{AosPeriod='50';AosSignalPeriod='9';TPCoef='1.3';DhlNCheck='50';GridVolMult='1.1'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='05'; Params=@{AosPeriod='70';AosSignalPeriod='9';TPCoef='1.8';DhlNCheck='60';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='06'; Params=@{AosPeriod='70';AosSignalPeriod='13';TPCoef='1.8';DhlNCheck='80';GridVolMult='1.1'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='07'; Params=@{AosPeriod='90';AosSignalPeriod='13';TPCoef='2.3';DhlNCheck='100';GridVolMult='1.0'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='08'; Params=@{AosPeriod='50';AosSignalPeriod='5';TPCoef='0.8';DhlNCheck='40';GridVolMult='1.2'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='09'; Params=@{AosPeriod='30';AosSignalPeriod='13';TPCoef='2.3';DhlNCheck='60';GridVolMult='1.1'} },
  [pscustomobject]@{ EA='DHLAOS-v1.5'; Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'; BaseSet='DHLAOS-v1.5.set'; CandidateId='10'; Params=@{AosPeriod='90';AosSignalPeriod='5';TPCoef='1.3';DhlNCheck='20';GridVolMult='1.0'} }
)

Write-ProgressRow 'Batch' 'Start' '' '' "RunId=$RunId Symbol=$Symbol Model=$Model Candidates=$($candidates.Count)"

$sweepRows = New-Object System.Collections.Generic.List[object]
$setInfoByKey = @{}
foreach($period in $Periods) {
  foreach($candidate in $candidates) {
    $setInfo = New-CandidateSet $candidate $period
    $setInfoByKey["$($candidate.EA)|$($candidate.CandidateId)|$period"] = $setInfo
    $row = Invoke-SingleTest $candidate $period $SweepFromDate $SweepToDate $setInfo.SetFile 'Sweep2025'
    $sweepRows.Add((Convert-Result $candidate $period $setInfo.SetFile $setInfo.ArchivePath $row 'Sweep2025'))
  }
}
$sweepRows | Export-Csv -LiteralPath $sweepSummaryCsv -NoTypeInformation -Encoding UTF8

$selected = New-Object System.Collections.Generic.List[object]
foreach($ea in ($candidates.EA | Sort-Object -Unique)) {
  foreach($period in $Periods) {
    $minTrades = if($period -eq 'H4') { 4 } else { 10 }
    $bucket = $sweepRows | Where-Object {
      $_.EA -eq $ea -and $_.Period -eq $period -and $_.NetProfit -gt 0 -and $_.ProfitFactor -ge 1.05 -and $_.Trades -ge $minTrades -and !$_.MarginWarning
    }
    $top = @($bucket | Sort-Object @{Expression='ProfitFactor';Descending=$true}, @{Expression='RobustScore';Descending=$true} | Select-Object -First $TopPerCase)
    foreach($item in $top) { $selected.Add($item) }
  }
}
$selected | Export-Csv -LiteralPath $selectedCsv -NoTypeInformation -Encoding UTF8
Write-ProgressRow 'Select' 'Done' '' '' "Selected=$($selected.Count)"

$finalRows = New-Object System.Collections.Generic.List[object]
foreach($item in $selected) {
  $candidate = $candidates | Where-Object { $_.EA -eq $item.EA -and $_.CandidateId -eq $item.CandidateId } | Select-Object -First 1
  $setInfo = $setInfoByKey["$($candidate.EA)|$($candidate.CandidateId)|$($item.Period)"]
  $row = Invoke-SingleTest $candidate $item.Period $ValidationFromDate $ValidationToDate $setInfo.SetFile 'Validate2020_2025'
  $converted = Convert-Result $candidate $item.Period $setInfo.SetFile $setInfo.ArchivePath $row 'Validate2020_2025'
  $converted | Add-Member -NotePropertyName SweepNetProfit -NotePropertyValue $item.NetProfit -Force
  $converted | Add-Member -NotePropertyName SweepProfitFactor -NotePropertyValue $item.ProfitFactor -Force
  $converted | Add-Member -NotePropertyName SweepEquityDDPct -NotePropertyValue $item.EquityDDPct -Force
  $converted | Add-Member -NotePropertyName SweepTrades -NotePropertyValue $item.Trades -Force
  $riskTag = 'Reject'
  if($converted.NetProfit -gt 0 -and $converted.ProfitFactor -ge 1.3 -and $converted.EquityDDPct -le 30 -and $converted.Trades -ge 20 -and !$converted.MarginWarning) { $riskTag = 'Preferred' }
  elseif($converted.NetProfit -gt 0 -and $converted.ProfitFactor -ge 1.15 -and $converted.EquityDDPct -le 50 -and $converted.Trades -ge 20 -and !$converted.MarginWarning) { $riskTag = 'Watch' }
  elseif($converted.NetProfit -gt 0 -and $converted.ProfitFactor -ge 1.05 -and $converted.EquityDDPct -le 70 -and $converted.Trades -ge 15 -and !$converted.MarginWarning) { $riskTag = 'HighRisk' }
  $converted | Add-Member -NotePropertyName RiskTag -NotePropertyValue $riskTag -Force
  $finalRows.Add($converted)
}
$finalRows | Export-Csv -LiteralPath $finalCsv -NoTypeInformation -Encoding UTF8
Write-ProgressRow 'Batch' 'Done' '' '' "FinalRows=$($finalRows.Count) FinalCsv=$finalCsv"

[pscustomobject]@{
  RunId=$RunId
  Symbol=$Symbol
  Model=$Model
  SweepRows=$sweepRows.Count
  SelectedRows=$selected.Count
  FinalRows=$finalRows.Count
  OutputRoot=$outRoot
  SweepSummaryCsv=$sweepSummaryCsv
  SelectedCsv=$selectedCsv
  FinalCsv=$finalCsv
}
