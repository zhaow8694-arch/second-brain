param(
  [Parameter(Mandatory=$true)][string]$Expert,
  [Parameter(Mandatory=$true)][string]$EAName,
  [Parameter(Mandatory=$true)][ValidateSet('M1','M5','M15','M30','H1','H2','H3','H4','D1','Daily')][string]$Period,
  [string]$SetFile = '',
  [string]$Symbol = 'XAUUSD',
  [string]$FromDate = '2025.04.01',
  [string]$ToDate = '2026.03.31',
  [string]$RunId = 'manual_12m_H1_H4_20260616',
  [int]$Model = 4,
  [int]$Deposit = 20000,
  [string]$Currency = 'USD',
  [int]$Leverage = 200,
  [int]$ExecutionMode = 100,
  [int]$TimeoutMinutes = 25
)

$ErrorActionPreference = 'Stop'

$base = 'D:\MT5测试\MetaTrader 5'
$terminal = Join-Path $base 'terminal64.exe'
$outRoot = Join-Path $base "SingleEAReports\$RunId"
$csv = Join-Path $outRoot 'EA_Test_Log.csv'
$stamp = ($FromDate -replace '\.', '') + '_' + ($ToDate -replace '\.', '')

function Convert-ToSafeName([string]$name) {
  $safe = $name -replace '[^A-Za-z0-9_.-]', '_'
  if($safe.Length -le 70) { return $safe }
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($name)
  $sha = [System.Security.Cryptography.SHA1]::Create()
  $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').Substring(0, 8)
  return $safe.Substring(0, 60) + '_' + $hash
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

$running = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'terminal64.exe' -and $_.ExecutablePath -like "$base*"
}
if($running) {
  throw "MT5 terminal is already running for $base. Stop it before starting another single test."
}

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
if(!(Test-Path -LiteralPath $csv)) {
  $header = '测试时间,EA,参数文件,品种,周期,开始日期,结束日期,状态,净利润,毛利,毛损,盈利因子,预期收益,最大净值回撤,相对净值回撤,交易总计,盈利交易,亏损交易,最大盈利单,最大亏损单,平均盈利单,平均亏损单,报告路径,备注'
  [System.IO.File]::WriteAllText($csv, $header + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

$safeEA = Convert-ToSafeName $EAName
$outDir = Join-Path $outRoot "$safeEA\$Period"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$config = Join-Path $base "Tester\single_${RunId}_${safeEA}_${Symbol}_${Period}.ini"
$reportName = "${safeEA}_${Symbol}_${Period}_${stamp}"
$configLines = @(
  '[Tester]',
  "Expert=$Expert"
)
if($SetFile -ne '') {
  $configLines += "ExpertParameters=$SetFile"
}
$configLines += @(
  "Symbol=$Symbol",
  "Period=$Period",
  'Optimization=0',
  "Model=$Model",
  "FromDate=$FromDate",
  "ToDate=$ToDate",
  'ForwardMode=0',
  "Deposit=$Deposit",
  "Currency=$Currency",
  'ProfitInPips=0',
  "Leverage=$Leverage",
  "ExecutionMode=$ExecutionMode",
  'OptimizationCriterion=7',
  'Visual=0',
  "Report=$reportName",
  'ReplaceReport=1',
  'ShutdownTerminal=1'
)
$configText = ($configLines -join "`r`n") + "`r`n"
$containsNonAscii = $false
foreach($ch in $Expert.ToCharArray()) {
  if([int][char]$ch -gt 127) {
    $containsNonAscii = $true
    break
  }
}
$configEncoding = if($containsNonAscii) { [System.Text.Encoding]::Default } else { [System.Text.UTF8Encoding]::new($false) }
[System.IO.File]::WriteAllText($config, $configText, $configEncoding)

Get-ChildItem -LiteralPath $base -Filter "$reportName*" -File -ErrorAction SilentlyContinue | Remove-Item -Force

$process = Start-Process -FilePath $terminal -ArgumentList @('/portable',('/config:"' + $config + '"')) -WindowStyle Hidden -PassThru
$started = Get-Date
while(Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
  Start-Sleep -Seconds 10
  if(((Get-Date) - $started).TotalMinutes -gt $TimeoutMinutes) {
    Stop-Process -Id $process.Id -Force
    throw "Test timeout after $TimeoutMinutes minutes: $EAName $Period"
  }
}

$reportPath = Join-Path $base ($reportName + '.htm')
if(!(Test-Path -LiteralPath $reportPath)) {
  $status = '失败-无报告'
  $row = [pscustomobject]@{
    '测试时间'=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss'); 'EA'=$EAName; '参数文件'=if($SetFile){$SetFile}else{'默认'};
    '品种'=$Symbol; '周期'=$Period; '开始日期'=$FromDate; '结束日期'=$ToDate; '状态'=$status;
    '净利润'=''; '毛利'=''; '毛损'=''; '盈利因子'=''; '预期收益'=''; '最大净值回撤'='';
    '相对净值回撤'=''; '交易总计'=''; '盈利交易'=''; '亏损交易'=''; '最大盈利单'='';
    '最大亏损单'=''; '平均盈利单'=''; '平均亏损单'=''; '报告路径'=''; '备注'="No report generated. Config=$config"
  }
  $row | Export-Csv -LiteralPath $csv -Append -NoTypeInformation -Encoding UTF8
  $row | Format-List
  exit 2
}

$lines = Read-ReportLines $reportPath
$testerLog = Join-Path $base ('Tester\logs\' + (Get-Date -Format 'yyyyMMdd') + '.log')
$testerTail = ''
if(Test-Path -LiteralPath $testerLog) {
  $testerTail = Get-Content -LiteralPath $testerLog -Tail 240 | Out-String
}

$status = '完成'
$note = "$FromDate-$ToDate $Period；Model=$Model；Deposit=$Deposit；Leverage=$Leverage；ExecutionMode=$ExecutionMode；" + $(if($SetFile){$SetFile}else{'默认参数'})
if($testerTail -match 'not enough money') {
  $status = '完成-含保证金不足'
  $note += '；日志出现not enough money'
}

$finalReport = Join-Path $outDir ($reportName + '.htm')
Get-ChildItem -LiteralPath $base -Filter ($reportName + '*') -File |
  ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination (Join-Path $outDir $_.Name) -Force }

$row = [pscustomobject]@{
  '测试时间'=(Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  'EA'=$EAName
  '参数文件'=if($SetFile){$SetFile}else{'默认'}
  '品种'=$Symbol
  '周期'=$Period
  '开始日期'=$FromDate
  '结束日期'=$ToDate
  '状态'=$status
  '净利润'=Get-Metric $lines '总净盈利'
  '毛利'=Get-Metric $lines '毛利'
  '毛损'=Get-Metric $lines '毛损'
  '盈利因子'=Get-Metric $lines '盈利因子'
  '预期收益'=Get-Metric $lines '预期收益'
  '最大净值回撤'=Get-Metric $lines '最大净值亏损'
  '相对净值回撤'=Get-Metric $lines '相对净值亏损'
  '交易总计'=Get-Metric $lines '交易总计'
  '盈利交易'=Get-Metric $lines '盈利交易 (% 全部)'
  '亏损交易'=Get-Metric $lines '亏损交易 (% 全部)'
  '最大盈利单'=Get-Metric $lines '最大 获利交易'
  '最大亏损单'=Get-Metric $lines '最大 亏损交易'
  '平均盈利单'=Get-Metric $lines '平均 获利交易'
  '平均亏损单'=Get-Metric $lines '平均 亏损交易'
  '报告路径'=$finalReport
  '备注'=$note
}
$row | Export-Csv -LiteralPath $csv -Append -NoTypeInformation -Encoding UTF8
$row | Format-List
