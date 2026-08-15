param(
  [Parameter(Mandatory=$true)][string]$Quarter,
  [Parameter(Mandatory=$true)][string]$FromDate,
  [Parameter(Mandatory=$true)][string]$ToDate,
  [Parameter(Mandatory=$true)][double]$Deposit,
  [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $PSCommandPath
$configDir = Join-Path $scriptDir 'configs-d-mt5'
$mt5Base = Get-ChildItem -LiteralPath 'D:\' -Directory |
  Where-Object { $_.Name -like 'MT5*' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'MetaTrader 5\terminal64.exe')) } |
  Select-Object -First 1

if (-not $mt5Base) {
  throw 'Cannot locate MT5 base directory under D:\.'
}

$mt5Root = Join-Path $mt5Base.FullName 'MetaTrader 5'
$terminal = Join-Path $mt5Root 'terminal64.exe'
$reportStem = "EA31337_Lite_MODEL1_H1ONLY_CHAIN_${Quarter}_XAUUSD_H1"
$reportPath = Join-Path $mt5Root "BatchReports\$reportStem.htm"
$configPath = Join-Path $configDir "$reportStem.ini"

New-Item -ItemType Directory -Force -Path $configDir | Out-Null
if (Test-Path -LiteralPath $reportPath) {
  Remove-Item -LiteralPath $reportPath -Force
}

$depositText = $Deposit.ToString('0.00', [Globalization.CultureInfo]::InvariantCulture)
$config = @"
[Experts]
AllowLiveTrading=0
AllowDllImport=0
Enabled=1
Account=0
Profile=0

[Tester]
Expert=EA31337_release\EA31337-Lite-v2.013.1
Symbol=XAUUSD
Period=H1
Deposit=$depositText
Currency=USD
Leverage=1:100
Model=1
ExecutionMode=0
Optimization=0
FromDate=$FromDate
ToDate=$ToDate
Report=BatchReports\$reportStem
ReplaceReport=1
ShutdownTerminal=1
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0

[TesterInputs]
Strategy_M1=0
Strategy_M5=0
Strategy_M15=0
Strategy_M30=0
Strategy_H1=17
Strategy_H2=0
Strategy_H3=0
Strategy_H4=0
Strategy_H6=0
Strategy_H8=0
Strategy_H12=0
VerboseLevel=0
EA_DisplayDetailsOnChart=false
"@

Set-Content -LiteralPath $configPath -Value $config -Encoding ASCII

$start = Get-Date
$p = Start-Process -FilePath $terminal -ArgumentList @('/portable', "/config:$configPath") -PassThru -WindowStyle Hidden
$finished = $p.WaitForExit($TimeoutSeconds * 1000)
if (-not $finished) {
  Stop-Process -Id $p.Id -Force
}
$seconds = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)

function Get-ReportValue([string]$Html, [string]$Label) {
  $pattern = '<td[^>]*>\s*' + [regex]::Escape($Label) + ':\s*</td>\s*<td[^>]*>\s*<b>(.*?)</b>'
  $match = [regex]::Match($Html, $pattern, [Text.RegularExpressions.RegexOptions]::Singleline)
  if ($match.Success) {
    return ([Net.WebUtility]::HtmlDecode(($match.Groups[1].Value -replace '<[^>]+>', ' '))).Trim()
  }
  return ''
}

function Convert-ReportNumber([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return 0.0 }
  $first = ($Value -split '\s*\(')[0]
  $clean = $first -replace '\s+', ''
  $clean = $clean -replace ',', ''
  $out = 0.0
  if ([double]::TryParse($clean, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$out)) {
    return $out
  }
  return 0.0
}

$html = ''
if (Test-Path -LiteralPath $reportPath) {
  $html = Get-Content -LiteralPath $reportPath -Raw
}

$netProfitText = Get-ReportValue $html '总净盈利'
$netProfit = Convert-ReportNumber $netProfitText
$endingDeposit = $Deposit + $netProfit

$result = [ordered]@{
  quarter = $Quarter
  fromDate = $FromDate
  toDate = $ToDate
  startDeposit = [math]::Round($Deposit, 2)
  finished = [bool]$finished
  exitCode = if ($finished) { $p.ExitCode } else { 'TIMEOUT' }
  seconds = $seconds
  reportExists = (Test-Path -LiteralPath $reportPath)
  reportPath = $reportPath
  configPath = $configPath
  expert = Get-ReportValue $html '专家'
  period = Get-ReportValue $html '期间'
  netProfitText = $netProfitText
  netProfit = [math]::Round($netProfit, 2)
  endingDeposit = [math]::Round($endingDeposit, 2)
  profitFactor = Get-ReportValue $html '盈利因子'
  totalTrades = Get-ReportValue $html '交易总计'
  sellTrades = Get-ReportValue $html '卖出交易 (赢得 %)'
  buyTrades = Get-ReportValue $html '买入交易 (赢得 %)'
  profitTrades = Get-ReportValue $html '盈利交易 (% 全部)'
  lossTrades = Get-ReportValue $html '亏损交易 (% 全部)'
  maxEquityDrawdown = Get-ReportValue $html '最大净值亏损'
  bars = Get-ReportValue $html '柱'
  ticks = Get-ReportValue $html '报价'
}

$result | ConvertTo-Json -Depth 4
