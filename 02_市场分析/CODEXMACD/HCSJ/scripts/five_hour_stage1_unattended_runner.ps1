$ErrorActionPreference='Stop'
. 'E:\CODEXMACD\HCSJ\scripts\robust_search_runner.ps1'
$BatchStamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='E:\CODEXMACD'; $HCSJ=Join-Path $Root 'HCSJ'
$MDir=Join-Path $HCSJ 'matrix\pressure_walkforward'
$Master=Join-Path $MDir 'pressure_walkforward_master_matrix.csv'
$DateCsv=Join-Path $MDir 'date_shift_summary.csv'
$RevCsv=Join-Path $MDir 'walkforward_2020_2026_to_2012_2019.csv'
$FwdCsv=Join-Path $MDir 'walkforward_2012_2019_to_2020_2026.csv'
$SpreadCsv=Join-Path $MDir 'spread_feasibility_summary.csv'
$StageMd=Join-Path $MDir 'pressure_walkforward_stage1_summary.md'
$WorkLog=Join-Path $Root 'WORK_LOG.md'; $Handoff=Join-Path $Root 'HANDOFF_NEXT_WINDOW.md'
$Known=556052.56
$Src86='E:\GROKMACD\SniperTrendEA_v8.6.mq5'; $Src866='E:\CODEXMACD\SniperTrendEA_v8.66_grokbase_structure_risk_r68_dualperiod_candidate.mq5'
$Exp86='SniperTrendEA_v8.6_groktrue_20260619.ex5'; $Exp866='SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
$Ex586='D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.6_groktrue_20260619.ex5'; $Ex5866='D:\MT5测试\MetaTrader 5\MQL5\Experts\SniperTrendEA_v8.66_r68_dualperiod_candidate_20260619.ex5'
$SetA='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.6_robust_main_case0502.set'
$SetB='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_robust_main_case0010.set'
$SetC='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_aggressive_case0005.set'
$SetD='E:\CODEXMACD\HCSJ\set\final_candidates\20260619_070045_robust_parameter_search\v8.66_conservative_case0401.set'
$Set86Base='E:\CODEXMACD\HCSJ\set\v8.6_anchor_20251231_r54.set'; $Set866Base='E:\CODEXMACD\HCSJ\set\v8.66_20260630_structure_ultra0999_floor0995_r68.set'
$Objects=@(
[pscustomobject]@{Id='A';Ver='v8.6';Role='v8.6 robust case0502';Set=$SetA;Src=$Src86;Exp=$Exp86;Ex5=$Ex586;Class='reference'},
[pscustomobject]@{Id='B';Ver='v8.66';Role='v8.66 robust case0010';Set=$SetB;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='main'},
[pscustomobject]@{Id='C';Ver='v8.66';Role='v8.66 aggressive case0005';Set=$SetC;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='aggressive_observation'},
[pscustomobject]@{Id='D';Ver='v8.66';Role='v8.66 conservative case0401';Set=$SetD;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='conservative_observation'})
function N($x){if($null -eq $x -or [string]::IsNullOrWhiteSpace([string]$x)){0.0}else{[double](([string]$x -replace ',','') -replace ' ','')}}
function CS($x){if($null -eq $x){return ''};$s=[string]$x;if($s -match '[,"`r`n]'){'"'+$s.Replace('"','""')+'"'}else{$s}}
function Log($t,$lines){$st=Get-Date -Format 'yyyy-MM-dd HH:mm:ss K';$body="`n## $st - $t`n"+(($lines|%{"- $_"}) -join "`n")+"`n";[IO.File]::AppendAllText($WorkLog,$body,[Text.UTF8Encoding]::new($true))}
function Init(){New-Item -ItemType Directory -Force -Path $MDir | Out-Null; New-Item -ItemType Directory -Force -Path (Join-Path $HCSJ 'backtest_archive\pressure_walkforward\stage1_five_hour') | Out-Null; New-Item -ItemType Directory -Force -Path (Join-Path $HCSJ 'set\pressure_walkforward\stage1_five_hour') | Out-Null; New-Item -ItemType Directory -Force -Path (Join-Path $HCSJ 'logs\pressure_walkforward') | Out-Null; if(!(Test-Path $Master)){ $h='run_id,module,object_id,version,set_role,window,stage,case_id,status,source_file,ex5_file,set_file,config_file,report_file,start_date,end_date,symbol,timeframe,model,spread_mode,spread_level,slippage_level,deposit,leverage,net_profit,profit_retention_pct,profit_factor,max_balance_dd,max_balance_dd_pct,max_equity_dd,max_equity_dd_pct,relative_equity_dd,relative_equity_dd_pct,total_trades,trade_count_retention_pct,win_rate,avg_profit_per_trade,worst_period_flag,sensitivity_rating,decision,notes'; [IO.File]::WriteAllText($Master,$h+[Environment]::NewLine,[Text.UTF8Encoding]::new($true))}}
function AddRow($mod,$obj,$win,$stage,$case,$res,$from,$to,$decision,$notes,$spreadMode='current',$spreadLevel='current'){$m=if($res.Report -and (Test-Path $res.Report)){Get-ReportMetrics $res.Report}else{@{net_profit='';profit_factor='';max_balance_dd='';max_balance_dd_pct='';max_equity_dd='';max_equity_dd_pct='';relative_equity_dd='';relative_equity_dd_pct='';total_trades='';win_rate=''}};$net=N $m.net_profit;$tr=N $m.total_trades;$avg=if($tr -gt 0){[math]::Round($net/$tr,2)}else{''};$ret=if($win -eq '2020-2026' -and $obj.Id -in @('B','C','D')){[math]::Round($net/$Known*100,2)}else{''};$cols=@($res.RunId,$mod,$obj.Id,$obj.Ver,$obj.Role,$win,$stage,$case,$res.Status,$obj.Src,$obj.Ex5,$res.Set,$res.Config,$res.Report,$from,$to,'XAUUSD','H4','1',$spreadMode,$spreadLevel,'0','20000','100',$m.net_profit,$ret,$m.profit_factor,$m.max_balance_dd,$m.max_balance_dd_pct,$m.max_equity_dd,$m.max_equity_dd_pct,$m.relative_equity_dd,$m.relative_equity_dd_pct,$m.total_trades,'',$m.win_rate,$avg,'','',$decision,$notes);[IO.File]::AppendAllText($Master,(($cols|%{CS $_}) -join ',')+[Environment]::NewLine,[Text.UTF8Encoding]::new($true))}
function RunOne($mod,$obj,$win,$stage,$case,$from,$to,$ov,$decision,$notes,$spreadMode='current',$spreadLevel='current'){$ver=if($obj.Ver -eq 'v8.66'){'v866'}else{'v86'};$rw=($win -replace '[^0-9A-Za-z-]','_');$rid="${ver}_$($obj.Id)_${mod}_${rw}_${BatchStamp}_case$('{0:d4}' -f [int]$case)";$r=Invoke-Mt5Backtest -RunId $rid -Version $obj.Ver -Window $win -Stage $stage -Round 1 -CaseId $case -SourceFile $obj.Src -ExpertFileName $obj.Exp -Ex5File $obj.Ex5 -BaseSet $obj.Set -Overrides $ov -FromDate $from -ToDate $to -CandidateClass $obj.Class -Decision $decision -Notes $notes -TimeoutSeconds 1200;AddRow $mod $obj $win $stage $case $r $from $to $decision $notes $spreadMode $spreadLevel;return $r}
function Score($m){(N $m.net_profit)/10000+(N $m.profit_factor)*15-(N $m.max_equity_dd_pct)*0.4+(N $m.total_trades)/100}
function Std($a){$b=@($a);if($b.Count -le 1){0}else{$avg=($b|Measure -Average).Average;$s=0;foreach($x in $b){$s+=[math]::Pow($x-$avg,2)};[math]::Round([math]::Sqrt($s/($b.Count-1)),2)}}function Smoke(){ $o=$Objects|? Id -eq 'B'|select -First 1;$r=RunOne 'smoke' $o '2020-2026' 'smoke' 1 '2020.01.01' '2026.06.30' @{} 'smoke-test' 'five-hour smoke test';$net=N $r.NetProfit;$diff=[math]::Abs($net-$Known)/$Known*100;if($r.Status -ne 'completed' -or [string]::IsNullOrWhiteSpace($r.NetProfit) -or $diff -gt 1){Log 'Five-hour Task 1 smoke BLOCKED' @("RunId=$($r.RunId)","Status=$($r.Status)","Net=$($r.NetProfit)","DiffPct=$([math]::Round($diff,4))","Stopped before batch execution");throw 'Smoke test failed'};Log 'Five-hour Task 1 smoke completed' @("RunId=$($r.RunId)","Net=$($r.NetProfit)","PF=$($r.PF)","Trades=$($r.Trades)","DiffPct=$([math]::Round($diff,4))");return $r}
function DateShift(){ $wins=@(@{N='2012-2019';S='2012.01.01';E='2019.12.31'},@{N='2020-2026';S='2020.01.01';E='2026.06.30'});$sh=@(@{C=0;SM=0;EM=0;L='original'},@{C=1;SM=1;EM=0;L='start_plus_1m'},@{C=2;SM=3;EM=0;L='start_plus_3m'},@{C=3;SM=0;EM=-1;L='end_minus_1m'},@{C=4;SM=0;EM=-3;L='end_minus_3m'},@{C=5;SM=1;EM=-1;L='start_plus_1m_end_minus_1m'},@{C=6;SM=3;EM=-3;L='start_plus_3m_end_minus_3m'},@{C=7;SM=6;EM=-6;L='start_plus_6m_end_minus_6m'});$cnt=0;foreach($o in $Objects){foreach($w in $wins){$sb=[datetime]::ParseExact($w.S,'yyyy.MM.dd',$null);$eb=[datetime]::ParseExact($w.E,'yyyy.MM.dd',$null);foreach($s in $sh){$from=$sb.AddMonths($s.SM).ToString('yyyy.MM.dd');$to=$eb.AddMonths($s.EM).ToString('yyyy.MM.dd');$base=if($o.Id -eq 'A'){1000}elseif($o.Id -eq 'B'){2000}elseif($o.Id -eq 'C'){3000}else{4000};RunOne 'date_shift' $o $w.N $s.L ($base+$s.C) $from $to @{} 'date-shift' ("date shift $($s.L)")|Out-Null;$cnt++}}};$rows=Import-Csv $Master|? module -eq 'date_shift';$sum=$rows|Group object_id,version,set_role,window|%{$g=$_.Group;$nets=@($g|%{N $_.net_profit});$pfs=@($g|%{N $_.profit_factor});$dds=@($g|%{N $_.max_equity_dd_pct});$trs=@($g|%{N $_.total_trades});$mn=($nets|Measure -Minimum).Minimum;$pfmin=($pfs|Measure -Minimum).Minimum;$tmin=($trs|Measure -Minimum).Minimum;$tmax=($trs|Measure -Maximum).Maximum;$rating='low';if($mn -lt 0 -or $pfmin -lt 1.0 -or ($tmax -gt 0 -and $tmin/$tmax -lt .75)){$rating='high'}elseif($pfmin -lt 1.5 -or (Std $nets) -gt 100000){$rating='medium'};[pscustomobject]@{object_id=$g[0].object_id;version=$g[0].version;set_role=$g[0].set_role;base_window=$g[0].window;run_count=$g.Count;completed_count=@($g|? status -eq completed).Count;net_profit_avg=[math]::Round(($nets|Measure -Average).Average,2);net_profit_min=[math]::Round($mn,2);net_profit_max=[math]::Round(($nets|Measure -Maximum).Maximum,2);net_profit_std=Std $nets;pf_avg=[math]::Round(($pfs|Measure -Average).Average,2);pf_min=[math]::Round($pfmin,2);max_equity_dd_pct_max=[math]::Round(($dds|Measure -Maximum).Maximum,2);total_trades_min=$tmin;total_trades_max=$tmax;sensitivity_rating=$rating;decision=if($rating -eq 'high'){'do_not_promote'}elseif($rating -eq 'medium'){'watch'}else{'pass'};notes='stage1 date shift'}};$sum|Export-Csv $DateCsv -NoTypeInformation -Encoding UTF8;Log 'Five-hour Task 2 date-shift completed' @("Runs=$cnt","Summary=$DateCsv","High=$(@($sum|? sensitivity_rating -eq high).Count)","Medium=$(@($sum|? sensitivity_rating -eq medium).Count)");return $sum}
function WFCandidates(){ $v86=[pscustomobject]@{Id='WF86';Ver='v8.6';Role='v8.6 wf';Set=$Set86Base;Src=$Src86;Exp=$Exp86;Ex5=$Ex586;Class='wf'};$v866=[pscustomobject]@{Id='WF866';Ver='v8.66';Role='v8.66 wf';Set=$Set866Base;Src=$Src866;Exp=$Exp866;Ex5=$Ex5866;Class='wf'};$l=@();$v86c=@(@{C=1;R='v86 original';O=@{}},@{C=2;R='v86 risk040';O=@{InpRiskPercent='0.40'}},@{C=3;R='v86 risk050';O=@{InpRiskPercent='0.50'}},@{C=4;R='v86 risk060';O=@{InpRiskPercent='0.60'}},@{C=5;R='v86 atr130';O=@{InpATRMultiplier='1.30';InpTrailingStart='4.50';InpTrailingStep='2.20'}},@{C=6;R='v86 atr135';O=@{InpATRMultiplier='1.35';InpTrailingStart='4.70';InpTrailingStep='2.30'}},@{C=7;R='v86 atr125';O=@{InpATRMultiplier='1.25';InpTrailingStart='4.30';InpTrailingStep='2.10'}},@{C=8;R='v86 atr145';O=@{InpATRMultiplier='1.45';InpTrailingStart='5.00';InpTrailingStep='2.50'}},@{C=9;R='v86 original exit';O=@{InpATRMultiplier='1.50';InpTrailingStart='5.00';InpTrailingStep='2.50'}},@{C=10;R='v86 risk045 atr135';O=@{InpRiskPercent='0.45';InpATRMultiplier='1.35';InpTrailingStart='4.70';InpTrailingStep='2.30'}},@{C=11;R='v86 risk055 atr135';O=@{InpRiskPercent='0.55';InpATRMultiplier='1.35';InpTrailingStart='4.70';InpTrailingStep='2.30'}},@{C=12;R='v86 atr170';O=@{InpATRMultiplier='1.70';InpTrailingStart='5.50';InpTrailingStep='2.80'}});foreach($c in $v86c){$o=$v86.PSObject.Copy();$o.Role=$c.R;$l+=[pscustomobject]@{Obj=$o;Case=$c.C;Ov=$c.O;Role=$c.R}};$v866c=@(@{C=101;R='v866 base';O=@{}},@{C=102;R='v866 lot098';O=@{InpRiskLotScale='0.980'}},@{C=103;R='v866 lot100';O=@{InpRiskLotScale='1.000'}},@{C=104;R='v866 risk043';O=@{InpRiskPercent='0.430'}},@{C=105;R='v866 risk045';O=@{InpRiskPercent='0.450'}},@{C=106;R='v866 risk050';O=@{InpRiskPercent='0.500'}},@{C=107;R='v866 risk055';O=@{InpRiskPercent='0.550'}},@{C=108;R='v866 peak20';O=@{InpMaxPeakDDPercent='20.0';InpPeakDDWarningRatio='0.90';InpRiskLotScale='0.980'}},@{C=109;R='v866 struct off';O=@{InpRiskLotScale='1.000';InpUseStructureScore='false'}},@{C=110;R='v866 score60';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='60.0';InpNoStructurePenalty='0.998';InpMinStructureQualityFloor='0.995'}},@{C=111;R='v866 score70';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='70.0';InpNoStructurePenalty='0.999';InpMinStructureQualityFloor='0.995'}},@{C=112;R='v866 score75';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='75.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}},@{C=113;R='v866 score80';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='80.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}},@{C=114;R='v866 score85';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='85.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}},@{C=115;R='v866 neutral';O=@{InpRiskLotScale='1.000';InpUseStructureScore='true';InpNoStructurePenalty='1.000';InpMinStructureQualityFloor='1.000'}},@{C=116;R='v866 cons struct';O=@{InpRiskLotScale='0.995';InpUseStructureScore='true';InpMinBreakoutScore='80.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}},@{C=117;R='v866 aggr struct';O=@{InpRiskPercent='0.550';InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='80.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}},@{C=118;R='v866 cons risk struct';O=@{InpRiskPercent='0.430';InpRiskLotScale='1.000';InpUseStructureScore='true';InpMinBreakoutScore='80.0';InpNoStructurePenalty='0.995';InpMinStructureQualityFloor='0.990'}});foreach($c in $v866c){$o=$v866.PSObject.Copy();$o.Role=$c.R;$l+=[pscustomobject]@{Obj=$o;Case=$c.C;Ov=$c.O;Role=$c.R}};return $l}function Walk($mod,$trainW,$trainF,$trainT,$valW,$valF,$valT,$out,$label){$rows=@();$cands=WFCandidates;foreach($c in $cands){$r=RunOne $mod $c.Obj $trainW 'train' $c.Case $trainF $trainT $c.Ov 'wf-train' ($label+' train '+$c.Role);$m=Get-ReportMetrics $r.Report;$rows+=[pscustomobject]@{phase='train';candidate_case=$c.Case;version=$c.Obj.Ver;set_role=$c.Role;run_id=$r.RunId;window=$trainW;net_profit=$m.net_profit;profit_factor=$m.profit_factor;max_equity_dd_pct=$m.max_equity_dd_pct;total_trades=$m.total_trades;score=Score $m;decision='candidate';notes=$label}}
$tops=@();foreach($v in @('v8.6','v8.66')){$tops+=$rows|?{$_.phase -eq 'train' -and $_.version -eq $v}|sort score -desc|select -First 3}
foreach($t in $tops){$c=$cands|? Case -eq ([int]$t.candidate_case)|select -First 1;$r=RunOne $mod $c.Obj $valW 'validate' ([int]$c.Case+1000) $valF $valT $c.Ov 'wf-validate' ($label+' validate finalist '+$c.Role);$m=Get-ReportMetrics $r.Report;$rows+=[pscustomobject]@{phase='validate';candidate_case=$c.Case;version=$c.Obj.Ver;set_role=$c.Role;run_id=$r.RunId;window=$valW;net_profit=$m.net_profit;profit_factor=$m.profit_factor;max_equity_dd_pct=$m.max_equity_dd_pct;total_trades=$m.total_trades;score=Score $m;decision='validated';notes=$label};if($c.Obj.Ver -eq 'v8.6'){$s1=@{InpRiskPercent='0.480'};$s2=@{InpRiskPercent='0.520'}}else{$s1=@{InpRiskLotScale='0.995'};$s2=@{InpRiskLotScale='1.000'}};$idx=0;foreach($s in @($s1,$s2)){$idx++;$ov=@{};foreach($k in $c.Ov.Keys){$ov[$k]=$c.Ov[$k]};foreach($k in $s.Keys){$ov[$k]=$s[$k]};$cid=[int]$c.Case+(2000*$idx);$r2=RunOne $mod $c.Obj $valW ('sens'+$idx) $cid $valF $valT $ov 'wf-sensitivity' ($label+' sensitivity '+$idx+' '+$c.Role);$m2=Get-ReportMetrics $r2.Report;$rows+=[pscustomobject]@{phase=('sens'+$idx);candidate_case=$c.Case;version=$c.Obj.Ver;set_role=$c.Role;run_id=$r2.RunId;window=$valW;net_profit=$m2.net_profit;profit_factor=$m2.profit_factor;max_equity_dd_pct=$m2.max_equity_dd_pct;total_trades=$m2.total_trades;score=Score $m2;decision='sensitivity';notes=$label}}}
$rows|Export-Csv $out -NoTypeInformation -Encoding UTF8;Log ("Five-hour $label completed") @("Rows=$($rows.Count)","Summary=$out");return $rows}
function SpreadFeas(){ $o=$Objects|? Id -eq 'B'|select -First 1;$r1=RunOne 'spread_feasibility' $o '2020-2026' 'default_spread' 1 '2020.01.01' '2026.06.30' @{} 'spread-baseline' 'default/current spread' 'current' '1.0x';$r2=RunOne 'spread_feasibility' $o '2020-2026' 'metadata_wide_spread' 2 '2020.01.01' '2026.06.30' @{} 'spread-inconclusive' 'metadata-only wide spread; no verified MT5 fixed spread hook' 'metadata_only_unverified' '2.0x';$rows=@([pscustomobject]@{run_id=$r1.RunId;stage='default_spread';status=$r1.Status;net_profit=$r1.NetProfit;pf=$r1.PF;trades=$r1.Trades;spread_feasibility='baseline';notes='default/current spread'},[pscustomobject]@{run_id=$r2.RunId;stage='metadata_wide_spread';status=$r2.Status;net_profit=$r2.NetProfit;pf=$r2.PF;trades=$r2.Trades;spread_feasibility='inconclusive';notes='not valid as true spread stress evidence'});$rows|Export-Csv $SpreadCsv -NoTypeInformation -Encoding UTF8;Log 'Five-hour Task 5 spread feasibility completed with blocker' @("Summary=$SpreadCsv","Decision=inconclusive","Reason=current runner has no verified MT5 fixed-spread config hook");return $rows}
function Summary($smoke,$date,$rev,$fwd,$spread){$master=Import-Csv $Master;$bHigh=@($date|?{$_.object_id -eq 'B' -and $_.sensitivity_rating -eq 'high'}).Count;$cHigh=@($date|?{$_.object_id -eq 'C' -and $_.sensitivity_rating -eq 'high'}).Count;$main=if($bHigh -eq 0){'keep v8.66 robust case0010 as main candidate pending spread/slippage/monthly validation'}else{'retest v8.66 robust case0010 before v8.67'};$aggr=if($cHigh -eq 0){'keep aggressive as observation only; do not promote yet'}else{'keep aggressive as high-risk observation; do not promote'};$txt=@"
# Pressure Walk-Forward Stage 1 Summary

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')

## Paths
- Master matrix: `$Master`
- Date shift: `$DateCsv`
- Reverse walk-forward: `$RevCsv`
- Forward walk-forward: `$FwdCsv`
- Spread feasibility: `$SpreadCsv`

## Run counts
- Total rows: $($master.Count)
- Smoke: $(@($master|? module -eq 'smoke').Count)
- Date shift: $(@($master|? module -eq 'date_shift').Count)
- Reverse walk-forward: $(@($master|? module -eq 'walkforward_reverse').Count)
- Forward walk-forward: $(@($master|? module -eq 'walkforward_forward').Count)
- Spread feasibility: $(@($master|? module -eq 'spread_feasibility').Count)

## Smoke
- RunId: $($smoke.RunId)
- Status: $($smoke.Status)
- Net profit: $($smoke.NetProfit)
- PF: $($smoke.PF)
- Trades: $($smoke.Trades)

## Date shift
- High sensitivity groups: $(@($date|? sensitivity_rating -eq 'high').Count)
- Medium sensitivity groups: $(@($date|? sensitivity_rating -eq 'medium').Count)
- Object B high sensitivity groups: $bHigh
- Object C high sensitivity groups: $cHigh

## Walk-forward
- Reverse rows: $($rev.Count)
- Forward rows: $($fwd.Count)
- Use validation and sensitivity rows for final decisions, not training profit only.

## Spread feasibility
Result: inconclusive/blocker for true fixed-spread stress. The second run is metadata-only and must not be treated as spread-stress evidence.

## Decisions
- Main candidate: $main
- Aggressive candidate: $aggr
- Conservative candidate: keep as risk reference.
- v8.6 candidate: keep as reference.

## Next recommended block
Review these summaries first. Then either verify a real MT5 fixed-spread config hook, or move to quarterly breakdown before any v8.67 code changes.
"@;[IO.File]::WriteAllText($StageMd,$txt,[Text.UTF8Encoding]::new($true));Log 'Five-hour Task 6 stage summary completed' @("Summary=$StageMd","MainDecision=$main","AggressiveDecision=$aggr")}
function HandoffUpdate(){ $st=Get-Date -Format 'yyyy-MM-dd HH:mm:ss K';$add=@"

---

## $st - Five-hour unattended pressure validation Stage 1

Completed modules:
1. Smoke test
2. Date-shift test
3. Reverse walk-forward `2020-2026 -> 2012-2019`
4. Forward walk-forward `2012-2019 -> 2020-2026`
5. Spread feasibility check
6. Stage summary

Important paths:

```text
$StageMd
$Master
$DateCsv
$RevCsv
$FwdCsv
$SpreadCsv
```

Known blocker:

Fixed-spread feasibility is inconclusive. The current proven runner does not have a verified MT5 fixed-spread config hook, so metadata-only spread runs must not be used as real spread-stress evidence.

Next step:

Review Stage 1 summary. Then either verify true fixed-spread configuration or proceed to quarterly breakdown. Do not modify EA source before reviewing this stage.
"@;[IO.File]::AppendAllText($Handoff,$add,[Text.UTF8Encoding]::new($true));Log 'Five-hour Task 7 handoff updated' @("Handoff=$Handoff","StageSummary=$StageMd")}
Init;Log 'Five-hour unattended execution started' @("Plan=E:\CODEXMACD\docs\superpowers\plans\2026-06-20-five-hour-pressure-validation-workplan.md","BatchStamp=$BatchStamp","Rule=Smoke must pass before batch")
$sm=Smoke
$ds=DateShift
$rv=Walk 'walkforward_reverse' '2020-2026' '2020.01.01' '2026.06.30' '2012-2019' '2012.01.01' '2019.12.31' $RevCsv 'Task 3 reverse walk-forward'
$fw=Walk 'walkforward_forward' '2012-2019' '2012.01.01' '2019.12.31' '2020-2026' '2020.01.01' '2026.06.30' $FwdCsv 'Task 4 forward walk-forward'
$sp=SpreadFeas
Summary $sm $ds $rv $fw $sp
HandoffUpdate
Log 'Five-hour unattended execution completed' @("Master=$Master","StageSummary=$StageMd","Status=completed without EA source changes")
[pscustomobject]@{Status='completed';BatchStamp=$BatchStamp;Master=$Master;StageSummary=$StageMd;DateShift=$DateCsv;ReverseWalkForward=$RevCsv;ForwardWalkForward=$FwdCsv;SpreadFeasibility=$SpreadCsv}|Format-List