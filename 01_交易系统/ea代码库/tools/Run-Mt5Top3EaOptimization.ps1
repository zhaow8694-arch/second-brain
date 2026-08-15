param(
  [string]$Symbol = 'XAUUSD',
  [string[]]$Periods = @('H1','H4'),
  [string]$OptFromDate = '2025.01.01',
  [string]$OptToDate = '2025.12.31',
  [string]$ValidationFromDate = '2020.01.01',
  [string]$ValidationToDate = '2025.12.31',
  [string]$RunId = 'top3_pf_settings_20260617',
  [int]$OptimizationMode = 2,
  [int]$OptimizationModel = 4,
  [int]$ValidationModel = 0,
  [int]$OptimizationTimeoutMinutes = 120,
  [int]$ValidationTimeoutMinutes = 45,
  [int]$MaxCandidatesPerCase = 5,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

$base = ('D:\MT5' + [char]0x6D4B + [char]0x8BD5 + '\MetaTrader 5')
$terminal = Join-Path $base 'terminal64.exe'
$profiles = Join-Path $base 'MQL5\Profiles\Tester'
$singleRunner = Join-Path $PSScriptRoot 'Run-Mt5SingleEaTest.ps1'
$outRoot = Join-Path $base "SingleEAReports\$RunId"
$validationRunId = "${RunId}_validation"
$validationRoot = Join-Path $base "SingleEAReports\$validationRunId"
$progressLog = Join-Path $outRoot 'Top3_Optimization_Progress.csv'
$optimizerRowsCsv = Join-Path $outRoot 'Top3_Optimizer_AllRows.csv'
$candidateCsv = Join-Path $outRoot 'Top3_Candidates_For_Validation.csv'
$finalCsv = Join-Path $outRoot 'Top3_Validated_Settings.csv'
$setArchive = Join-Path $outRoot 'CandidateSets'
$stdoutDir = Join-Path $outRoot 'runner_stdout'

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 100) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 90) + '_' + $hash
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
    $_.Name -eq 'terminal64.exe' -and $_.ExecutablePath -like "$base*"
  }
  if($running) {
    throw "MT5 terminal is already running for $base. Stop it before continuing."
  }
}

function Update-SetLines([string[]]$Lines, [hashtable]$Params) {
  $updated = New-Object System.Collections.Generic.List[string]
  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach($line in $Lines) {
    $handled = $false
    foreach($key in $Params.Keys) {
      if($line -match ('^' + [regex]::Escape($key) + '=')) {
        $updated.Add("$key=$($Params[$key])")
        [void]$seen.Add($key)
        $handled = $true
        break
      }
    }
    if(!$handled) { $updated.Add($line) }
  }
  foreach($key in $Params.Keys) {
    if(!$seen.Contains($key)) { $updated.Add("$key=$($Params[$key])") }
  }
  return $updated.ToArray()
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

function Convert-ToNumber($value) {
  if($null -eq $value) { return $null }
  $s = ([string]$value).Trim()
  if($s -eq '') { return $null }
  $s = $s -replace ' ', ''
  $s = $s -replace ',', ''
  $s = $s -replace '%', ''
  $d = 0.0
  if([double]::TryParse($s, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$d)) {
    return $d
  }
  if([double]::TryParse($s, [ref]$d)) { return $d }
  return $null
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
  NetProfit=(U @(0x51C0,0x5229,0x6DA6))
  ProfitFactor=(U @(0x76C8,0x5229,0x56E0,0x5B50))
  Trades=(U @(0x4EA4,0x6613,0x603B,0x8BA1))
  RelativeEquityDD=(U @(0x76F8,0x5BF9,0x51C0,0x503C,0x56DE,0x64A4))
  Status=(U @(0x72B6,0x6001))
  MarginShortage=(U @(0x4FDD,0x8BC1,0x91D1,0x4E0D,0x8DB3))
  ReportPath=(U @(0x62A5,0x544A,0x8DEF,0x5F84))
}

function Get-XmlRowValues([System.Xml.XmlNode]$row) {
  $values = New-Object System.Collections.Generic.List[string]
  $col = 1
  foreach($cell in $row.SelectNodes("*[local-name()='Cell']")) {
    $idx = $cell.GetAttribute('Index', 'urn:schemas-microsoft-com:office:spreadsheet')
    if($idx) {
      while($col -lt [int]$idx) {
        $values.Add('')
        $col++
      }
    }
    $data = $cell.SelectSingleNode("*[local-name()='Data']")
    if($data) { $values.Add($data.InnerText) } else { $values.Add('') }
    $col++
  }
  return $values.ToArray()
}

function Read-OptimizerXml([string]$Path, [string]$EA, [string]$Period) {
  [xml]$xml = Get-Content -LiteralPath $Path -Raw
  $rows = $xml.SelectNodes("//*[local-name()='Worksheet']/*[local-name()='Table']/*[local-name()='Row']")
  if($rows.Count -lt 2) { return @() }
  $headers = Get-XmlRowValues $rows[0]
  $objects = New-Object System.Collections.Generic.List[object]
  for($i = 1; $i -lt $rows.Count; $i++) {
    $vals = Get-XmlRowValues $rows[$i]
    if($vals.Count -eq 0) { continue }
    $map = [ordered]@{
      EA=$EA
      Period=$Period
      SourceXml=$Path
    }
    for($j = 0; $j -lt $headers.Count; $j++) {
      $h = $headers[$j]
      if([string]::IsNullOrWhiteSpace($h)) { $h = "Column$j" }
      $v = if($j -lt $vals.Count) { $vals[$j] } else { '' }
      $map[$h] = $v
    }
    $objects.Add([pscustomobject]$map)
  }
  return $objects.ToArray()
}

function Get-Metric([string[]]$lines, [string]$label) {
  for($i = 0; $i -lt $lines.Count; $i++) {
    if($lines[$i] -eq ($label + ':') -or $lines[$i] -eq $label) {
      if($i + 1 -lt $lines.Count) { return $lines[$i + 1] }
    }
  }
  return ''
}

function Read-ReportLines([string]$path) {
  $raw = Get-Content -LiteralPath $path -Raw -Encoding Unicode
  if($raw.Length -lt 100) {
    $raw = Get-Content -LiteralPath $path -Raw
  }
  $text = [System.Net.WebUtility]::HtmlDecode(($raw -replace '<[^>]+>', "`n"))
  return @($text -split "`n" | ForEach-Object { ($_ -replace '\s+', ' ').Trim() } | Where-Object { $_ })
}

function Run-OptimizationCase($Target, [string]$Period) {
  Assert-NoMt5
  $safeEA = Convert-ToSafeName $Target.EA
  $stamp = ($OptFromDate -replace '\.', '') + '_' + ($OptToDate -replace '\.', '')
  $outDir = Join-Path $outRoot "$safeEA\$Period\optimizer"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null

  $baseSetPath = Join-Path $profiles $Target.BaseSet
  if(!(Test-Path -LiteralPath $baseSetPath)) { throw "Base set not found: $baseSetPath" }

  $optSetName = "${safeEA}_${Symbol}_${Period}_${stamp}_PF_OPT.set"
  $optSetPath = Join-Path $profiles $optSetName
  $optLines = Update-SetLines (Get-Content -LiteralPath $baseSetPath) $Target.Params
  [System.IO.File]::WriteAllText($optSetPath, ($optLines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
  Copy-Item -LiteralPath $optSetPath -Destination (Join-Path $outDir $optSetName) -Force

  $reportName = "${safeEA}_${Symbol}_${Period}_${stamp}_PF_OPT"
  $config = Join-Path $base "Tester\$reportName.ini"
  $configLines = @(
    '[Tester]',
    "Expert=$($Target.Expert)",
    "ExpertParameters=$optSetName",
    "Symbol=$Symbol",
    "Period=$Period",
    "Optimization=$OptimizationMode",
    "Model=$OptimizationModel",
    "FromDate=$OptFromDate",
    "ToDate=$OptToDate",
    'ForwardMode=0',
    'Deposit=20000',
    'Currency=USD',
    'ProfitInPips=0',
    'Leverage=200',
    'ExecutionMode=100',
    'OptimizationCriterion=1',
    'Visual=0',
    "Report=$reportName",
    'ReplaceReport=1',
    'ShutdownTerminal=1'
  )
  [System.IO.File]::WriteAllText($config, ($configLines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
  Copy-Item -LiteralPath $config -Destination (Join-Path $outDir (Split-Path $config -Leaf)) -Force

  $existingXml = Join-Path $outDir "$reportName.xml"
  if((Test-Path -LiteralPath $existingXml) -and !$Force) {
    Write-ProgressRow 'Optimize' 'SkipExisting' $Target.EA $Period $existingXml
    return $existingXml
  }

  Get-ChildItem -LiteralPath $base -Filter "$reportName*" -File -ErrorAction SilentlyContinue | Remove-Item -Force
  Write-ProgressRow 'Optimize' 'Start' $Target.EA $Period "$OptFromDate-$OptToDate"
  $before = Get-Date
  $process = Start-Process -FilePath $terminal -ArgumentList @('/portable',('/config:"' + $config + '"')) -WindowStyle Hidden -PassThru
  while(Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Start-Sleep -Seconds 15
    if(((Get-Date) - $before).TotalMinutes -gt $OptimizationTimeoutMinutes) {
      Stop-Process -Id $process.Id -Force
      throw "Optimization timeout after $OptimizationTimeoutMinutes minutes: $($Target.EA) $Period"
    }
  }

  $candidates = @()
  foreach($root in @($base, $profiles, (Join-Path $base 'MQL5\Files'))) {
    if(Test-Path -LiteralPath $root) {
      $candidates += Get-ChildItem -LiteralPath $root -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "$reportName*" -and $_.Extension -ne '.set' -and $_.LastWriteTime -ge $before.AddMinutes(-1) }
    }
  }
  foreach($file in $candidates | Sort-Object FullName -Unique) {
    Move-Item -LiteralPath $file.FullName -Destination (Join-Path $outDir $file.Name) -Force
  }

  $xmlPath = Join-Path $outDir "$reportName.xml"
  if(!(Test-Path -LiteralPath $xmlPath)) {
    $found = Get-ChildItem -LiteralPath $outDir -File -Filter "$reportName*.xml" -ErrorAction SilentlyContinue | Select-Object -First 1
    if($found) { $xmlPath = $found.FullName }
  }
  if(!(Test-Path -LiteralPath $xmlPath)) {
    throw "Optimization did not produce XML report: $($Target.EA) $Period"
  }
  Write-ProgressRow 'Optimize' 'Done' $Target.EA $Period $xmlPath
  return $xmlPath
}

function Select-Candidates($Target, [string]$Period, [object[]]$Rows) {
  $minTrades = if($Period -eq 'H4') { 8 } else { 18 }
  $usable = $Rows | ForEach-Object {
    $pf = Convert-ToNumber $_.'Profit Factor'
    $profit = Convert-ToNumber $_.Profit
    $dd = Convert-ToNumber $_.'Equity DD %'
    $trades = Convert-ToNumber $_.Trades
    $recovery = Convert-ToNumber $_.'Recovery Factor'
    if($null -ne $pf -and $null -ne $profit -and $null -ne $dd -and $null -ne $trades) {
      $_ | Add-Member -NotePropertyName '_PF' -NotePropertyValue $pf -Force
      $_ | Add-Member -NotePropertyName '_Profit' -NotePropertyValue $profit -Force
      $_ | Add-Member -NotePropertyName '_DD' -NotePropertyValue $dd -Force
      $_ | Add-Member -NotePropertyName '_Trades' -NotePropertyValue $trades -Force
      $_ | Add-Member -NotePropertyName '_Recovery' -NotePropertyValue $(if($null -ne $recovery){$recovery}else{0}) -Force
      $_
    }
  } | Where-Object { $_._Profit -gt 0 -and $_._PF -ge 1.15 -and $_._DD -le 80 -and $_._Trades -ge $minTrades }

  $selected = New-Object System.Collections.Generic.List[object]
  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach($bucket in @(
    @($usable | Sort-Object @{Expression='_PF';Descending=$true}, @{Expression='_Trades';Descending=$true} | Select-Object -First $MaxCandidatesPerCase),
    @($usable | Sort-Object @{Expression='_Recovery';Descending=$true}, @{Expression='_DD';Descending=$false} | Select-Object -First $MaxCandidatesPerCase),
    @($usable | Sort-Object @{Expression='_Profit';Descending=$true}, @{Expression='_DD';Descending=$false} | Select-Object -First $MaxCandidatesPerCase)
  )) {
    foreach($item in $bucket) {
      $key = "$($item.Pass)"
      if(!$seen.Contains($key)) {
        [void]$seen.Add($key)
        $selected.Add($item)
        if($selected.Count -ge $MaxCandidatesPerCase) { break }
      }
    }
    if($selected.Count -ge $MaxCandidatesPerCase) { break }
  }

  $ranked = New-Object System.Collections.Generic.List[object]
  $rank = 0
  foreach($item in $selected) {
    $rank++
    $params = [ordered]@{}
    foreach($paramName in $Target.OptimizedParamNames) {
      if($item.PSObject.Properties.Name -contains $paramName) {
        $params[$paramName] = $item.$paramName
      }
    }
    $ranked.Add([pscustomobject]@{
      EA=$Target.EA
      Expert=$Target.Expert
      BaseSet=$Target.BaseSet
      Period=$Period
      CandidateRank=$rank
      OptimizerPass=$item.Pass
      OptimizerProfit=$item._Profit
      OptimizerPF=$item._PF
      OptimizerRecovery=$item._Recovery
      OptimizerEquityDDPct=$item._DD
      OptimizerTrades=$item._Trades
      Parameters=($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join '; '
      ParameterMap=$params
      SourceXml=$item.SourceXml
    })
  }
  return $ranked.ToArray()
}

function New-CandidateSet($Candidate) {
  $safeEA = Convert-ToSafeName $Candidate.EA
  $setName = "${safeEA}_${Symbol}_$($Candidate.Period)_cand$($Candidate.CandidateRank)_PF.set"
  $profilePath = Join-Path $profiles $setName
  $archivePath = Join-Path $setArchive $setName
  $baseSetPath = Join-Path $profiles $Candidate.BaseSet
  $optLines = Get-Content -LiteralPath $baseSetPath
  $values = @{}
  foreach($entry in $Candidate.ParameterMap.GetEnumerator()) {
    $values[$entry.Key] = $entry.Value
  }
  $newLines = Set-ParamValue $optLines $values
  [System.IO.File]::WriteAllText($profilePath, ($newLines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
  Copy-Item -LiteralPath $profilePath -Destination $archivePath -Force
  return [pscustomobject]@{ SetFile=$setName; ProfilePath=$profilePath; ArchivePath=$archivePath }
}

function Run-Validation($Candidate, [string]$SetFile) {
  $safeCase = Convert-ToSafeName "$($Candidate.EA)_$($Candidate.Period)_cand$($Candidate.CandidateRank)"
  $stdout = Join-Path $stdoutDir ($safeCase + '.out.txt')
  $stderr = Join-Path $stdoutDir ($safeCase + '.err.txt')
  $eaName = "$($Candidate.EA)_cand$($Candidate.CandidateRank)"
  Write-ProgressRow 'Validate' 'Start' $Candidate.EA $Candidate.Period "$SetFile $ValidationFromDate-$ValidationToDate"
  $args = @(
    '-NoProfile',
    '-ExecutionPolicy','Bypass',
    '-File', $singleRunner,
    '-Expert', $Candidate.Expert,
    '-EAName', $eaName,
    '-Symbol', $Symbol,
    '-Period', $Candidate.Period,
    '-FromDate', $ValidationFromDate,
    '-ToDate', $ValidationToDate,
    '-RunId', $validationRunId,
    '-Model', [string]$ValidationModel,
    '-TimeoutMinutes', [string]$ValidationTimeoutMinutes,
    '-SetFile', $SetFile
  )
  $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $status = if($p.ExitCode -eq 0) { 'Done' } else { "Exit$p.ExitCode" }
  Write-ProgressRow 'Validate' $status $Candidate.EA $Candidate.Period "$stdout"

  $csv = Join-Path $validationRoot 'EA_Test_Log.csv'
  if(!(Test-Path -LiteralPath $csv)) {
    throw "Validation CSV not found: $csv"
  }
  $row = Import-Csv -LiteralPath $csv | Where-Object {
    $_.EA -eq $eaName -and
      (Get-Prop $_ $C.Period) -eq $Candidate.Period -and
      (Get-Prop $_ $C.FromDate) -eq $ValidationFromDate -and
      (Get-Prop $_ $C.ToDate) -eq $ValidationToDate -and
      (Get-Prop $_ $C.ParamFile) -eq $SetFile
  } | Select-Object -Last 1
  if(!$row) {
    throw "Validation row not found for $eaName $($Candidate.Period) $SetFile"
  }
  return $row
}

function Get-ReportMarginWarning([string]$ReportPath) {
  if(!$ReportPath -or !(Test-Path -LiteralPath $ReportPath)) { return $false }
  $dir = Split-Path -Parent $ReportPath
  $tail = Join-Path $dir 'tester_tail.log'
  if(Test-Path -LiteralPath $tail) {
    $txt = Get-Content -LiteralPath $tail -Raw
    return ($txt -match 'not enough money')
  }
  return $false
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
New-Item -ItemType Directory -Force -Path $setArchive | Out-Null
New-Item -ItemType Directory -Force -Path $stdoutDir | Out-Null
if(!(Test-Path -LiteralPath $progressLog)) {
  'Time,Stage,Status,EA,Period,Detail' | Set-Content -LiteralPath $progressLog -Encoding UTF8
}
if(!(Test-Path -LiteralPath $singleRunner)) { throw "Single runner not found: $singleRunner" }
if(!(Test-Path -LiteralPath $terminal)) { throw "MT5 terminal not found: $terminal" }

$targets = @(
  [pscustomobject]@{
    EA='BBRSI-v1.6'
    Expert='metatrader5-master\Build\BBRSI\BBRSI-v1.6.ex5'
    BaseSet='BBRSI-v1.6.set'
    Params=@{
      BBLen='500||300||200||900||Y'
      RSILen='7||5||2||13||Y'
      TPCoef='1.0||0.8||0.4||2.0||Y'
      GridVolMult='1.1||1.0||0.1||1.2||Y'
      GridMaxLvl='20||8||8||24||Y'
    }
    OptimizedParamNames=@('BBLen','RSILen','TPCoef','GridVolMult','GridMaxLvl')
  },
  [pscustomobject]@{
    EA='3MAF-v1.5'
    Expert='metatrader5-master\Build\3MAF\3MAF-v1.5.ex5'
    BaseSet='3MAF-v1.5.set'
    Params=@{
      MA1Len='60||30||30||120||Y'
      MA2Len='350||220||60||400||Y'
      MA3Len='600||420||100||820||Y'
      TPCoef='1.5||0.8||0.4||2.0||Y'
      GridVolMult='1.5||1.0||0.2||1.6||Y'
    }
    OptimizedParamNames=@('MA1Len','MA2Len','MA3Len','TPCoef','GridVolMult')
  },
  [pscustomobject]@{
    EA='DHLAOS-v1.5'
    Expert='metatrader5-master\Build\DHLAOS\DHLAOS-v1.5.ex5'
    BaseSet='DHLAOS-v1.5.set'
    Params=@{
      AosPeriod='50||30||20||90||Y'
      AosSignalPeriod='9||5||4||13||Y'
      TPCoef='1.5||0.8||0.5||2.3||Y'
      DhlNCheck='50||20||20||100||Y'
      GridVolMult='1.1||1.0||0.1||1.2||Y'
    }
    OptimizedParamNames=@('AosPeriod','AosSignalPeriod','TPCoef','DhlNCheck','GridVolMult')
  }
)

Write-ProgressRow 'Batch' 'Start' '' '' "RunId=$RunId Symbol=$Symbol Periods=$($Periods -join '/') OptModel=$OptimizationModel ValidationModel=$ValidationModel"

$allOptimizerRows = New-Object System.Collections.Generic.List[object]
$allCandidates = New-Object System.Collections.Generic.List[object]
foreach($target in $targets) {
  foreach($period in $Periods) {
    $xmlPath = Run-OptimizationCase $target $period
    $rows = @(Read-OptimizerXml $xmlPath $target.EA $period)
    foreach($row in $rows) { $allOptimizerRows.Add($row) }
    Write-ProgressRow 'Parse' 'Rows' $target.EA $period "$($rows.Count) optimizer rows"
    $candidates = @(Select-Candidates $target $period $rows)
    foreach($candidate in $candidates) { $allCandidates.Add($candidate) }
    Write-ProgressRow 'Select' 'Candidates' $target.EA $period "$($candidates.Count) candidates"
  }
}

$allOptimizerRows | Export-Csv -LiteralPath $optimizerRowsCsv -NoTypeInformation -Encoding UTF8
$allCandidates |
  Select-Object EA,Expert,BaseSet,Period,CandidateRank,OptimizerPass,OptimizerProfit,OptimizerPF,OptimizerRecovery,OptimizerEquityDDPct,OptimizerTrades,Parameters,SourceXml |
  Export-Csv -LiteralPath $candidateCsv -NoTypeInformation -Encoding UTF8

$finalRows = New-Object System.Collections.Generic.List[object]
foreach($candidate in $allCandidates) {
  $setInfo = New-CandidateSet $candidate
  $validation = Run-Validation $candidate $setInfo.SetFile
  $net = Convert-ToNumber (Get-Prop $validation $C.NetProfit)
  $pf = Convert-ToNumber (Get-Prop $validation $C.ProfitFactor)
  $tradesText = Get-Prop $validation $C.Trades
  $trades = Convert-ToNumber (($tradesText -split ' ')[0])
  $ddText = Get-Prop $validation $C.RelativeEquityDD
  $ddPct = $null
  if($ddText -match '\(([0-9.,]+)%\)') { $ddPct = Convert-ToNumber $Matches[1] }
  elseif($ddText -match '([0-9.,]+)%') { $ddPct = Convert-ToNumber $Matches[1] }
  $marginWarning = ((Get-Prop $validation $C.Status) -like ('*' + $C.MarginShortage + '*')) -or (Get-ReportMarginWarning (Get-Prop $validation $C.ReportPath))
  $riskTag = 'Reject'
  if($null -ne $net -and $null -ne $pf -and $null -ne $ddPct -and $null -ne $trades) {
    if($net -gt 0 -and $pf -ge 1.3 -and $ddPct -le 30 -and $trades -ge 20 -and !$marginWarning) { $riskTag = 'Preferred' }
    elseif($net -gt 0 -and $pf -ge 1.15 -and $ddPct -le 50 -and $trades -ge 20 -and !$marginWarning) { $riskTag = 'Watch' }
    elseif($net -gt 0 -and $pf -ge 1.05 -and $ddPct -le 70 -and $trades -ge 15 -and !$marginWarning) { $riskTag = 'HighRisk' }
  }
  $score = -999999.0
  if($null -ne $net -and $null -ne $pf -and $null -ne $ddPct -and $null -ne $trades -and !$marginWarning) {
    $score = ($pf * [math]::Log([math]::Max($trades, 2))) + ($net / 10000.0) - ($ddPct / 25.0)
  }
  $finalRows.Add([pscustomobject]@{
    EA=$candidate.EA
    Period=$candidate.Period
    CandidateRank=$candidate.CandidateRank
    SetFile=$setInfo.SetFile
    SetArchivePath=$setInfo.ArchivePath
    OptimizerPass=$candidate.OptimizerPass
    OptimizerProfit=$candidate.OptimizerProfit
    OptimizerPF=$candidate.OptimizerPF
    OptimizerRecovery=$candidate.OptimizerRecovery
    OptimizerEquityDDPct=$candidate.OptimizerEquityDDPct
    OptimizerTrades=$candidate.OptimizerTrades
    ValidationNetProfit=$net
    ValidationPF=$pf
    ValidationEquityDDPct=$ddPct
    ValidationTrades=$trades
    ValidationStatus=(Get-Prop $validation $C.Status)
    MarginWarning=$marginWarning
    RiskTag=$riskTag
    RobustScore=[math]::Round($score, 6)
    Parameters=$candidate.Parameters
    ValidationReport=(Get-Prop $validation $C.ReportPath)
    SourceOptimizerXml=$candidate.SourceXml
  })
}

$finalRows | Export-Csv -LiteralPath $finalCsv -NoTypeInformation -Encoding UTF8
Write-ProgressRow 'Batch' 'Done' '' '' "FinalCsv=$finalCsv"

[pscustomobject]@{
  RunId=$RunId
  Symbol=$Symbol
  OptimizerRows=$allOptimizerRows.Count
  Candidates=$allCandidates.Count
  FinalRows=$finalRows.Count
  OutputRoot=$outRoot
  ValidationRoot=$validationRoot
  OptimizerRowsCsv=$optimizerRowsCsv
  CandidateCsv=$candidateCsv
  FinalCsv=$finalCsv
}
