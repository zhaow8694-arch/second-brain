$ErrorActionPreference='Stop'
. 'E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1'
$Batch=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='E:\CODEXMACD'; $HCSJ=Join-Path $Root 'HCSJ'
$MDir=Join-Path $HCSJ 'matrix\production_readiness'
$BRoot=Join-Path $HCSJ 'backtest_archive\production_readiness'
$SRoot=Join-Path $HCSJ 'set\production_readiness'
$Log=Join-Path $Root 'WORK_LOG.md'
New-Item -ItemType Directory -Force -Path $MDir,$BRoot,$SRoot,(Join-Path $HCSJ 'logs\production_readiness') | Out-Null
$QMatrix=Join-Path $MDir 'quarterly_breakdown_matrix.csv'; $QSummary=Join-Path $MDir 'quarterly_breakdown_summary.csv'
$MMatrix=Join-Path $MDir 'monthly_breakdown_core_matrix.csv'; $MSummary=Join-Path $MDir 'monthly_breakdown_core_summary.csv'
$SpreadCsv=Join-Path $MDir 'spread_feasibility_recheck.csv'; $SpreadNotes=Join-Path $MDir 'spread_feasibility_notes.md'
$SlipPlan='E:\CODEXMACD\docs\superpowers\plans\2026-06-20-slippage-test-ea-design.md'; $SlipMd=Join-Path $MDir 'slippage_test_feasibility.md'
$Src86='E:\GROKMACD\SniperTrendEA_v8.6.mq5'; $Src866='E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5'
$Exp86='SniperTrendEA_v8.6_groktrue_20260619.ex5'; $Exp866='SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
$Ex586='D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6_groktrue_20260619.ex5'; $Ex5866='D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
$SetA='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_robust_main_case0502.set'
$SetB='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set'
$SetC='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set'
$SetD='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_conservative_case0401.set'
$Objs=@(
[pscustomobject]@{Id='A';Ver='v8.6';Role='v8.6 robust case0502';Set=$SetA;Src=$Src86;Exp=$Exp86;Ex5=$Ex586;Class='reference'},
[pscustomobject]@{Id='B';Ver='v8.66';Role='v8.66 robust case0010';Set=$SetB;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='main'},
[pscustomobject]@{Id='C';Ver='v8.66';Role='v8.66 aggressive case0005';Set=$SetC;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='aggressive_observation'},
[pscustomobject]@{Id='D';Ver='v8.66';Role='v8.66 conservative case0401';Set=$SetD;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='conservative_observation'})
function N($x){if($null -eq $x -or [string]::IsNullOrWhiteSpace([string]$x)){0.0}else{[double](([string]$x -replace ',','') -replace ' ','')}}
function Log($title,$items){$st=Get-Date -Format 'yyyy-MM-dd HH:mm:ss K';$txt="`n## $st - $title`n"+(($items|%{"- $_"}) -join "`n")+"`n";[IO.File]::AppendAllText($Log,$txt,[Text.UTF8Encoding]::new($true))}
function CsvS($x){if($null -eq $x){return ''};$s=[string]$x;if($s -match '[,"`r`n]'){'"'+$s.Replace('"','""')+'"'}else{$s}}
function RunPR($module,$obj,$label,$from,$to,$case){$ver=if($obj.Ver -eq 'v8.66'){'v866'}else{'v86'};$rid="${ver}_$($obj.Id)_${module}_${label}_${Batch}_case$('{0:d4}' -f [int]$case)";$r=Invoke-Mt5Backtest -RunId $rid -Version $obj.Ver -Window $label -Stage $module -Round 1 -CaseId $case -SourceFile $obj.Src -ExpertFileName $obj.Exp -Ex5File $obj.Ex5 -BaseSet $obj.Set -Overrides @{} -FromDate $from -ToDate $to -CandidateClass $obj.Class -Decision $module -Notes "production readiness $module $label $($obj.Role)" -TimeoutSeconds 1200;$m=Get-ReportMetrics $r.Report;return [pscustomobject]@{run_id=$r.RunId;module=$module;object_id=$obj.Id;version=$obj.Ver;set_role=$obj.Role;period=$label;from=$from;to=$to;status=$r.Status;net_profit=$m.net_profit;profit_factor=$m.profit_factor;max_equity_dd=$m.max_equity_dd;max_equity_dd_pct=$m.max_equity_dd_pct;total_trades=$m.total_trades;win_rate=$m.win_rate;report=$r.Report;set_file=$r.Set;config=$r.Config;metrics=$r.Metrics}}
function MaxLoseStreak($rows){$max=0;$cur=0;$loss=0;$maxloss=0;foreach($r in $rows){$n=N $r.net_profit;if($n -lt 0){$cur++;$loss+=$n;if($cur -gt $max){$max=$cur};if($loss -lt $maxloss){$maxloss=$loss}}else{$cur=0;$loss=0}};return [pscustomobject]@{Count=$max;Loss=[math]::Round($maxloss,2)}}
function Summ($rows,$periodName){$rows|Group-Object object_id,version,set_role|%{$g=$_.Group;$nets=@($g|%{N $_.net_profit});$pfs=@($g|%{N $_.profit_factor});$dds=@($g|%{N $_.max_equity_dd_pct});$prof=@($g|?{(N $_.net_profit) -gt 0}).Count;$total=($nets|Measure -Sum).Sum;$best=$g|Sort-Object {[double](N $_.net_profit)} -Descending|select -First 1;$worst=$g|Sort-Object {[double](N $_.net_profit)}|select -First 1;$streak=MaxLoseStreak $g;$share=if($total -ne 0){[math]::Round((N $best.net_profit)/$total*100,2)}else{0};$ratio=[math]::Round($prof/$g.Count*100,2);$rating='good';if($ratio -lt 45 -or $share -gt 50){$rating='risk'}elseif($ratio -lt 60 -or $share -gt 35){$rating='watch'};[pscustomobject]@{object_id=$g[0].object_id;version=$g[0].version;set_role=$g[0].set_role;period_count=$g.Count;completed_count=@($g|? status -eq completed).Count;total_net_profit=[math]::Round($total,2);profitable_period_count=$prof;profitable_period_ratio=$ratio;worst_period=$worst.period;best_period=$best.period;worst_period_profit=$worst.net_profit;best_period_profit=$best.net_profit;max_single_period_profit_share=$share;max_consecutive_losing_periods=$streak.Count;max_consecutive_losing_period_loss=$streak.Loss;pf_avg=[math]::Round(($pfs|Measure -Average).Average,2);pf_min=[math]::Round(($pfs|Measure -Minimum).Minimum,2);max_equity_dd_pct_max=[math]::Round(($dds|Measure -Maximum).Maximum,2);stability_rating=$rating;decision=if($rating -eq 'good'){'pass'}elseif($rating -eq 'watch'){'watch'}else{'risk'};notes="production readiness $periodName summary"}}
}# Task 1: repair Stage 1 summary path display
$Stage1='E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_stage1_summary.md'
$stageTxt=Get-Content -LiteralPath $Stage1 -Raw
$stageTxt=$stageTxt.Replace('$Master','E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\pressure_walkforward_master_matrix.csv').Replace('$DateCsv','E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\date_shift_summary.csv').Replace('$RevCsv','E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2020_2026_to_2012_2019.csv').Replace('$FwdCsv','E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\walkforward_2012_2019_to_2020_2026.csv').Replace('$SpreadCsv','E:\CODEXMACD\HCSJ\matrix\pressure_walkforward\spread_feasibility_summary.csv')
$fixedStage1='E:\CODEXMACD\HCSJ\matrix\production_readiness\pressure_walkforward_stage1_summary_paths_fixed.md'
[IO.File]::WriteAllText($fixedStage1,$stageTxt,[Text.UTF8Encoding]::new($true))
Log '12h Task 1 integrity review completed' @("Fixed stage1 path display copy=$fixedStage1","No raw historical matrix changed","Production readiness matrix dir=$MDir")

# Task 2: quarterly breakdown 2012Q1-2023Q4
$qRows=@();$case=1
foreach($y in 2012..2023){foreach($q in 1..4){$sm=(($q-1)*3)+1;$em=$sm+2;$from=(Get-Date -Year $y -Month $sm -Day 1).ToString('yyyy.MM.dd');$endDate=(Get-Date -Year $y -Month $em -Day 1).AddMonths(1).AddDays(-1);$to=$endDate.ToString('yyyy.MM.dd');$label=('{0}Q{1}' -f $y,$q);foreach($o in $Objs){$qRows+=RunPR 'quarterly' $o $label $from $to $case;$case++}}}
$qRows|Export-Csv -LiteralPath $QMatrix -NoTypeInformation -Encoding UTF8
$qSum=Summ $qRows 'quarterly'
$qSum|Export-Csv -LiteralPath $QSummary -NoTypeInformation -Encoding UTF8
Log '12h Task 2 quarterly breakdown completed' @("Runs=$($qRows.Count)","Matrix=$QMatrix","Summary=$QSummary","B rating=$((($qSum|? object_id -eq 'B')|select -First 1).stability_rating)")

# Task 3: monthly breakdown core B/C 2012.01-2023.12
$mRows=@();$case=1;$core=$Objs|?{$_.Id -in @('B','C')}
foreach($y in 2012..2023){foreach($mo in 1..12){$from=(Get-Date -Year $y -Month $mo -Day 1).ToString('yyyy.MM.dd');$to=(Get-Date -Year $y -Month $mo -Day 1).AddMonths(1).AddDays(-1).ToString('yyyy.MM.dd');$label=('{0}{1:d2}' -f $y,$mo);foreach($o in $core){$mRows+=RunPR 'monthly_core' $o $label $from $to $case;$case++}}}
$mRows|Export-Csv -LiteralPath $MMatrix -NoTypeInformation -Encoding UTF8
$mSum=Summ $mRows 'monthly_core'
$mSum|Export-Csv -LiteralPath $MSummary -NoTypeInformation -Encoding UTF8
Log '12h Task 3 monthly core breakdown completed' @("Runs=$($mRows.Count)","Matrix=$MMatrix","Summary=$MSummary","B rating=$((($mSum|? object_id -eq 'B')|select -First 1).stability_rating)","C rating=$((($mSum|? object_id -eq 'C')|select -First 1).stability_rating)")

# Task 4: fixed-spread blocker investigation
$iniHits=@()
try{$iniHits=Get-ChildItem -LiteralPath 'E:\CODEXMACD' -Recurse -Filter '*.ini' -File -ErrorAction SilentlyContinue | Select-String -Pattern '^\s*(Spread|SpreadMode|FixedSpread)\s*=' -ErrorAction SilentlyContinue | Select-Object Path,LineNumber,Line}catch{}
$spreadRows=@()
if($iniHits.Count -gt 0){$decision='candidate_fields_found_unverified'}else{$decision='blocked'}
$spreadRows+=[pscustomobject]@{timestamp=(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K');decision=$decision;candidate_field_count=$iniHits.Count;notes='No verified MT5 fixed-spread config hook in existing project runner. Do not fabricate spread stress.'}
$spreadRows|Export-Csv -LiteralPath $SpreadCsv -NoTypeInformation -Encoding UTF8
$note="# Fixed Spread Feasibility Recheck`n`nDecision: $decision`n`nCandidate spread-field hits: $($iniHits.Count)`n`nConclusion: true fixed-spread pressure remains blocked/inconclusive until MT5 config hook is independently verified. Metadata-only spread runs are not valid evidence.`n"
[IO.File]::WriteAllText($SpreadNotes,$note,[Text.UTF8Encoding]::new($true))
Log '12h Task 4 fixed-spread blocker investigation completed' @("Decision=$decision","CandidateFieldHits=$($iniHits.Count)","Csv=$SpreadCsv","Notes=$SpreadNotes")

# Task 5: slippage-test design
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SlipPlan) | Out-Null
$slipPlanTxt=@"
# Slippage Test EA Design

Goal: design a temporary slippage-pressure method without modifying production v8.66/v8.67 source.

Decision: requires_temp_ea_or_external_execution_model.

Reason: current verified MT5 batch runner does not expose a proven slippage simulation setting. Any direct config-only result would be unreliable until verified.

Temporary EA name if approved later:

```text
E:\CODEXMACD\SniperTrendEA_v8.67_slippage_test.mq5
```

Rules:

- Do not replace production EA.
- Keep entry/exit logic equivalent to v8.67 production-ready line.
- Add slippage simulation only around order price assumptions or post-report analysis.
- Test levels: 0, 1, 2, 3, 5.
- Archive every run.
- Compare robust B and aggressive C first.

Deliverable before implementation:

- User approval or explicit unattended instruction allowing temporary test EA creation.
"@
[IO.File]::WriteAllText($SlipPlan,$slipPlanTxt,[Text.UTF8Encoding]::new($true))
$slipFeas="# Slippage Test Feasibility`n`nDecision: requires_temp_ea_or_external_execution_model`n`nCurrent production EA was not modified. A separate design plan was created at:`n`n$SlipPlan`n"
[IO.File]::WriteAllText($SlipMd,$slipFeas,[Text.UTF8Encoding]::new($true))
Log '12h Task 5 slippage-test design completed' @("Decision=requires_temp_ea_or_external_execution_model","Plan=$SlipPlan","Feasibility=$SlipMd","ProductionEAChanged=false")
[pscustomobject]@{Status='completed';QMatrix=$QMatrix;QSummary=$QSummary;MMatrix=$MMatrix;MSummary=$MSummary;Spread=$SpreadCsv;Slippage=$SlipPlan}|Format-List