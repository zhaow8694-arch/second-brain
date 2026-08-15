param(
  [Parameter(Mandatory=$true)][ValidateSet('SniperProbe','Sniper','OmniAggressive','VegasV41')][string]$Preset,
  [string]$Symbol = 'XAUUSD',
  [string]$Period = 'H4',
  [string]$FromDate = '2025.04.01',
  [string]$ToDate = '2026.03.31',
  [string]$RunId = 'optimize_profit_factor_20260617',
  [int]$OptimizationMode = 2,
  [int]$Model = 0,
  [int]$TimeoutMinutes = 180
)

$ErrorActionPreference = 'Stop'

$base = 'D:\MT5测试\MetaTrader 5'
$terminal = Join-Path $base 'terminal64.exe'
$profiles = Join-Path $base 'MQL5\Profiles\Tester'
$outRoot = Join-Path $base "SingleEAReports\$RunId"

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 70) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 60) + '_' + $hash
}

function Get-PresetConfig([string]$preset) {
  switch($preset) {
    'SniperProbe' {
      return @{
        EAName='SniperTrendEA_v8.7_RiskFix_probe'
        Expert='SniperTrendEA_v8.7_RiskFix.ex5'
        BaseSet='SniperTrendEA_v8.7_RiskFix.set'
        Params=@{
          InpConfirmBars='4||3||1||5||Y'
        }
      }
    }
    'Sniper' {
      return @{
        EAName='SniperTrendEA_v8.7_RiskFix'
        Expert='SniperTrendEA_v8.7_RiskFix.ex5'
        BaseSet='SniperTrendEA_v8.7_RiskFix.set'
        Params=@{
          InpMA200BufferATR='0.1||0.0||0.1||0.3||Y'
          InpMaxCandleATR='2.5||2.0||0.5||3.5||Y'
          InpMaxOppositeShadow='0.2||0.1||0.05||0.3||Y'
          InpConfirmBars='4||2||1||5||Y'
          InpATRMultiplier='1.5||1.0||0.25||2.0||Y'
          InpTrailingStart='5.0||3.0||1.0||6.0||Y'
          InpTrailingStep='2.5||1.5||0.5||3.5||Y'
        }
      }
    }
    'OmniAggressive' {
      return @{
        EAName='OmniAggressiveHedgeEngine'
        Expert='OmniFuturesSuite\OmniAggressiveHedgeEngine.ex5'
        BaseSet='OmniAggressiveHedgeEngine.set'
        Params=@{
          InpMaxDailyLossPct='8.0||4.0||2.0||10.0||Y'
          InpMaxGlobalRiskPct='14.0||8.0||4.0||20.0||Y'
          InpMaxPositionsPerSymbol='4||2||1||5||Y'
          InpRiskMultiplier='1.0||0.5||0.25||1.5||Y'
          InpMaxAddOnLayers='2||1||1||3||Y'
          InpRangeForceCloseHour='22||20||1||23||Y'
        }
      }
    }
    'VegasV41' {
      return @{
        EAName='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED'
        Expert='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED.ex5'
        BaseSet='Vegas_Trend_Master_H4_Multi_V4.1_Optimized_FIXED.set'
        Params=@{
          InpBreakEvenBufferPoints='0||0||10||50||Y'
          InpSLBufferPoints='50||20||20||100||Y'
          InpMaxSimultaneousPositions='4||1||1||4||Y'
          InpEma12='12||8||2||20||Y'
          InpEma144='144||120||12||180||Y'
          InpEma288='288||240||24||360||Y'
        }
      }
    }
  }
}

function Update-SetLines([string[]]$lines, [hashtable]$params) {
  $updated = New-Object System.Collections.Generic.List[string]
  foreach($line in $lines) {
    $handled = $false
    foreach($key in $params.Keys) {
      if($line -match ('^' + [regex]::Escape($key) + '=')) {
        $updated.Add("$key=$($params[$key])")
        $handled = $true
        break
      }
    }
    if(!$handled) { $updated.Add($line) }
  }
  return $updated.ToArray()
}

$presetConfig = Get-PresetConfig $Preset
$eaName = $presetConfig.EAName
$safeEA = Convert-ToSafeName $eaName
$stamp = ($FromDate -replace '\.', '') + '_' + ($ToDate -replace '\.', '')
$outDir = Join-Path $outRoot "$safeEA\$Period"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$baseSetPath = Join-Path $profiles $presetConfig.BaseSet
if(!(Test-Path -LiteralPath $baseSetPath)) {
  throw "Base set not found: $baseSetPath"
}
$optSetName = "${safeEA}_${Symbol}_${Period}_${stamp}_PF_OPT.set"
$optSetPath = Join-Path $profiles $optSetName
$setLines = Get-Content -LiteralPath $baseSetPath
$optLines = Update-SetLines $setLines $presetConfig.Params
[System.IO.File]::WriteAllText($optSetPath, ($optLines -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath $optSetPath -Destination (Join-Path $outDir $optSetName) -Force

$reportName = "${safeEA}_${Symbol}_${Period}_${stamp}_PF_OPT"
$config = Join-Path $base "Tester\$reportName.ini"
$configLines = @(
  '[Tester]',
  "Expert=$($presetConfig.Expert)",
  "ExpertParameters=$optSetName",
  "Symbol=$Symbol",
  "Period=$Period",
  "Optimization=$OptimizationMode",
  "Model=$Model",
  "FromDate=$FromDate",
  "ToDate=$ToDate",
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

$running = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'terminal64.exe' -and $_.ExecutablePath -like "$base*"
}
if($running) {
  throw "MT5 terminal is already running for $base. Stop it before optimization."
}

$before = Get-Date
$process = Start-Process -FilePath $terminal -ArgumentList @('/portable',('/config:"' + $config + '"')) -WindowStyle Hidden -PassThru
while(Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
  Start-Sleep -Seconds 15
  if(((Get-Date) - $before).TotalMinutes -gt $TimeoutMinutes) {
    Stop-Process -Id $process.Id -Force
    throw "Optimization timeout after $TimeoutMinutes minutes: $eaName $Period"
  }
}

$candidates = @()
$searchRoots = @($base, $profiles, (Join-Path $base 'MQL5\Files'))
foreach($root in $searchRoots) {
  if(Test-Path -LiteralPath $root) {
    $candidates += Get-ChildItem -LiteralPath $root -File -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like "$reportName*" -and $_.Extension -ne '.set' -and $_.LastWriteTime -ge $before.AddMinutes(-1) }
  }
}

$moved = @()
foreach($file in $candidates | Sort-Object FullName -Unique) {
  $dest = Join-Path $outDir $file.Name
  Move-Item -LiteralPath $file.FullName -Destination $dest -Force
  $moved += $dest
}

Copy-Item -LiteralPath $config -Destination (Join-Path $outDir (Split-Path $config -Leaf)) -Force

$logPath = Join-Path $base 'Tester\logs\20260617.log'
if(Test-Path -LiteralPath $logPath) {
  Get-Content -LiteralPath $logPath -Tail 400 | Set-Content -LiteralPath (Join-Path $outDir 'tester_tail.log')
}

[pscustomobject]@{
  EA=$eaName
  Preset=$Preset
  Period=$Period
  OptimizationMode=$OptimizationMode
  Model=$Model
  SetFile=$optSetName
  Config=$config
  OutputDir=$outDir
  ReportFiles=($moved -join '; ')
}
