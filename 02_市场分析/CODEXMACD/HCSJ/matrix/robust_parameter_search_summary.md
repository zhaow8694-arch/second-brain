# v8.6 vs v8.66 多周期稳健最优参数寻找与过拟合验证总结

生成时间：2026-06-19 07:02:19 +08:00

## 1. 执行范围

本轮按照方案 E:\CODEXMACD\docs\superpowers\plans\2026-06-19-v86-v866-robust-parameter-search.md 执行，目标不是单周期最高利润，而是在防过拟合约束下寻找可继续开发的最佳设定。

已完成回测记录：$completed / 102 条完成。

覆盖内容：

- 固定参数基线：v8.6 与 v8.66，各 3 个强制时间段。
- v8.6 有界参数搜索：风险/出场参数小范围候选，跨 3 个强制时间段验证。
- v8.66 风控层搜索：风险百分比、仓位缩放、峰值回撤阀门候选。
- v8.66 结构层搜索：结构评分软因子、突破分数、结构惩罚/质量下限候选。
- 敏感性验证：候选附近轻微扰动。
- 年度拆解：两个主候选覆盖 2012-2023 单年结果。
- 可选控制窗口：最终候选覆盖 2020-2025 与 2020-2026.06.30。

归档位置：

- 主矩阵：$matrix
- 评分表：$scorePath
- 最终候选 set 目录：$finalDir
- 最终候选 manifest：$manifest
- 回测报告根目录：E:\CODEXMACD\HCSJ\backtest_archive

## 2. 固定参数基线结果

| run_id | version | window | net_profit | profit_factor | max_equity_dd_pct | total_trades | win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v86_2015-2019_fixed_round01_case0001_retry2 | v8.6 | 2015-2019 | 13194.10 | 1.12 | 39.72 | 155 | 37.42 |
| v86_2012-2014_fixed_round01_case0001 | v8.6 | 2012-2014 | 25321.25 | 1.32 | 39.51 | 95 | 35.79 |
| v86_2017-2023_fixed_round01_case0001 | v8.6 | 2017-2023 | 68055.85 | 1.26 | 46.91 | 230 | 42.61 |
| v866_2012-2014_fixed_round01_case0001 | v8.66 | 2012-2014 | 25345.33 | 1.33 | 39.39 | 95 | 35.79 |
| v866_2015-2019_fixed_round01_case0001 | v8.66 | 2015-2019 | 13113.95 | 1.12 | 39.63 | 155 | 37.42 |
| v866_2017-2023_fixed_round01_case0001 | v8.66 | 2017-2023 | 67048.75 | 1.26 | 46.78 | 230 | 42.61 |

固定基线结论：

- v8.66 r68 固定参数与 v8.6 固定参数在三段窗口内交易数一致或接近，没有通过减少交易次数制造稳定。
- v8.66 在 2012-2014 略高，在 2015-2019 与 2017-2023 略低，整体和 v8.6 原始固定基线接近。
- 这说明 v8.66 没有明显破坏 grok8.6 的原始收益骨架，但固定基线阶段也没有明显拉开优势。

## 3. 跨窗口参数组评分摘录

评分只是辅助筛选，最终结论同时参考回撤、年度分布、敏感性和 2020-2026 锚点。

| Version | Stage | Case | Class | NetSum | MinNet | AvgPF | MaxEquityDDPct | Trades | RobustnessScore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v8.6 | common_search | 5 | watchlist | 150642.36 | 19028.03 | 1.29 | 49.9 | 503 | 78 |
| v8.6 | sensitivity_stress | 502 | stress | 150662.82 | 19675.31 | 1.28 | 51.65 | 494 | 77 |
| v8.6 | common_search | 2 | conservative | 88374.3 | 12905.56 | 1.27 | 39.65 | 480 | 63 |
| v8.66 | sensitivity_stress | 401 | stress | 93569.2 | 12775.21 | 1.26 | 41.81 | 480 | 62 |
| v8.66 | risk_search | 4 | conservative | 97416.07 | 13182.13 | 1.25 | 43.29 | 480 | 61 |
| v8.66 | sensitivity_stress | 402 | stress | 100920.92 | 13136.8 | 1.25 | 44.71 | 480 | 61 |
| v8.66 | structure_search | 10 | watchlist | 106839.33 | 13268.74 | 1.23 | 46.9 | 480 | 60 |
| v8.66 | sensitivity_stress | 1002 | stress | 106264.77 | 13338.84 | 1.24 | 46.52 | 480 | 60 |
| v8.66 | sensitivity_stress | 1001 | stress | 106841.97 | 13274.1 | 1.23 | 46.9 | 480 | 60 |
| v8.66 | structure_search | 8 | watchlist | 106424.55 | 13326.33 | 1.23 | 46.91 | 480 | 59 |
| v8.66 | risk_search | 3 | aggressive | 106350.15 | 13316.56 | 1.23 | 46.89 | 480 | 59 |
| v8.66 | structure_search | 11 | watchlist | 106345.92 | 13316.56 | 1.23 | 46.89 | 480 | 59 |
| v8.66 | structure_search | 7 | structure-control | 106412.86 | 13202.06 | 1.23 | 46.88 | 480 | 59 |
| v8.66 | fixed_baseline | 1 | baseline | 105508.03 | 13113.95 | 1.24 | 46.78 | 480 | 59 |

重要观察：

- v8.6 case0005 / case0502 在三段强制窗口的总收益最高，但最大净值回撤比例也更高，并且 case0501 的附近扰动在 2015-2019 掉到 2,639.39，说明 v8.6 出场参数存在中等敏感性。
- v8.66 case0010 及其 stress case1001 / case1002 结果非常接近，说明结构评分参数在 75-85 附近没有出现断崖。
- v8.66 conservative case0401 / case0004 降低回撤时交易数仍保持 480，说明不是通过大幅减少交易次数来降低风险。

## 4. 最终候选参数包

最终候选已经复制到：

$finalDir

候选说明：

- 8.6_robust_main_case0502.set：v8.6 高收益且比 case0501 更稳定的主候选，但回撤偏高。
- 8.6_aggressive_case0005.set：v8.6 高收益进攻候选，存在参数敏感性风险。
- 8.6_conservative_case0002.set：v8.6 保守候选，收益降低但回撤更低。
- 8.66_robust_main_case0010.set：v8.66 主推稳健候选，结构参数扰动稳定，2020-2026 几乎贴住旧锚点。
- 8.66_aggressive_case0005.set：v8.66 高收益候选，收益大幅提高但回撤也明显提高，只适合观察或进一步压力测试。
- 8.66_conservative_case0401.set：v8.66 低回撤候选，交易数不塌缩，适合风控方向研究。

## 5. 2020-2025 与 2020-2026 控制窗口

| run_id | version | window | candidate_class | net_profit | profit_factor | max_equity_dd | max_equity_dd_pct | total_trades |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v86_2020-2025_control_robust_case0502 | v8.6 | 2020-2025 | control-robust | 289919.86 | 1.78 | 81520.52 | 40.31 | 201 |
| v86_2020-2026_control_robust_case0502 | v8.6 | 2020-2026 | control-robust | 489512.30 | 2.07 | 129165.44 | 24.36 | 215 |
| v86_2020-2025_control_aggressive_case0005 | v8.6 | 2020-2025 | control-aggressive | 269550.48 | 1.74 | 70642.79 | 39.89 | 207 |
| v86_2020-2026_control_aggressive_case0005 | v8.6 | 2020-2026 | control-aggressive | 475720.24 | 2.07 | 123307.33 | 24.27 | 221 |
| v86_2020-2025_control_conservative_case0002 | v8.6 | 2020-2025 | control-conservative | 215522.96 | 2.00 | 48780.51 | 28.84 | 189 |
| v86_2020-2026_control_conservative_case0002 | v8.6 | 2020-2026 | control-conservative | 314203.80 | 2.22 | 73503.34 | 20.63 | 203 |
| v866_2020-2025_control_robust_case0010 | v8.66 | 2020-2025 | control-robust | 355945.87 | 2.02 | 87369.64 | 34.57 | 189 |
| v866_2020-2026_control_robust_case0010 | v8.66 | 2020-2026 | control-robust | 556052.56 | 2.27 | 149127.97 | 24.11 | 203 |
| v866_2020-2025_control_aggressive_case0005 | v8.66 | 2020-2025 | control-aggressive | 443339.80 | 2.02 | 117904.70 | 23.29 | 189 |
| v866_2020-2026_control_aggressive_case0005 | v8.66 | 2020-2026 | control-aggressive | 716968.27 | 2.29 | 203843.44 | 25.69 | 203 |
| v866_2020-2025_control_conservative_case0401 | v8.66 | 2020-2025 | control-conservative | 249474.53 | 2.00 | 58081.86 | 30.59 | 189 |
| v866_2020-2026_control_conservative_case0401 | v8.66 | 2020-2026 | control-conservative | 371235.57 | 2.23 | 90894.02 | 21.73 | 203 |

锚点对齐结论：

- 旧 grok8.6 已知锚点：557,505.36 USD。
- v8.66 robust case0010 在 2020-2026.06.30 净利润 $(MdEscape @{run_id=v866_2020-2026_control_robust_case0010; version=v8.66; window=2020-2026; candidate_class=control-robust; net_profit=556052.56; profit_factor=2.27; max_equity_dd=149127.97; max_equity_dd_pct=24.11; total_trades=203}.net_profit)，约为旧锚点的 $retV866Robust%，PF $(MdEscape @{run_id=v866_2020-2026_control_robust_case0010; version=v8.66; window=2020-2026; candidate_class=control-robust; net_profit=556052.56; profit_factor=2.27; max_equity_dd=149127.97; max_equity_dd_pct=24.11; total_trades=203}.profit_factor)，交易 $(MdEscape @{run_id=v866_2020-2026_control_robust_case0010; version=v8.66; window=2020-2026; candidate_class=control-robust; net_profit=556052.56; profit_factor=2.27; max_equity_dd=149127.97; max_equity_dd_pct=24.11; total_trades=203}.total_trades)。
- v8.66 aggressive case0005 在 2020-2026.06.30 净利润 $(MdEscape @{run_id=v866_2020-2026_control_aggressive_case0005; version=v8.66; window=2020-2026; candidate_class=control-aggressive; net_profit=716968.27; profit_factor=2.29; max_equity_dd=203843.44; max_equity_dd_pct=25.69; total_trades=203}.net_profit)，约为旧锚点的 $retV866Agg%，但最大净值回撤 $(MdEscape @{run_id=v866_2020-2026_control_aggressive_case0005; version=v8.66; window=2020-2026; candidate_class=control-aggressive; net_profit=716968.27; profit_factor=2.29; max_equity_dd=203843.44; max_equity_dd_pct=25.69; total_trades=203}.max_equity_dd)，风险显著增加。
- v8.6 robust case0502 在 2020-2026.06.30 净利润 $(MdEscape @{run_id=v86_2020-2026_control_robust_case0502; version=v8.6; window=2020-2026; candidate_class=control-robust; net_profit=489512.30; profit_factor=2.07; max_equity_dd=129165.44; max_equity_dd_pct=24.36; total_trades=215}.net_profit)，约为旧锚点的 $retV86Robust%，说明它在早期分段优秀，但在原主锚点窗口不如 v8.66 robust。

## 6. 年度拆解

年度拆解只针对两个主候选：v8.6 case0502 与 v8.66 case0010。

| version | window | run_id | net_profit | profit_factor | total_trades |
| --- | --- | --- | --- | --- | --- |
| v8.6 | 2012 | v86_2012_yearly_round01_case0502 | 3917.31 | 1.21 | 33 |
| v8.6 | 2013 | v86_2013_yearly_round01_case0502 | 38081.41 | 3.01 | 29 |
| v8.6 | 2014 | v86_2014_yearly_round01_case0502 | 4603.73 | 1.20 | 35 |
| v8.6 | 2015 | v86_2015_yearly_round01_case0502 | -4597.74 | 0.68 | 32 |
| v8.6 | 2016 | v86_2016_yearly_round01_case0502 | 17039.21 | 1.64 | 27 |
| v8.6 | 2017 | v86_2017_yearly_round01_case0502 | -2137.23 | 0.87 | 38 |
| v8.6 | 2018 | v86_2018_yearly_round01_case0502 | 20374.03 | 2.04 | 24 |
| v8.6 | 2019 | v86_2019_yearly_round01_case0502 | -4385.70 | 0.79 | 39 |
| v8.6 | 2020 | v86_2020_yearly_round01_case0502 | 33783.30 | 2.09 | 33 |
| v8.6 | 2021 | v86_2021_yearly_round01_case0502 | 635.99 | 1.04 | 33 |
| v8.6 | 2022 | v86_2022_yearly_round01_case0502 | 4139.33 | 1.23 | 39 |
| v8.6 | 2023 | v86_2023_yearly_round01_case0502 | -2725.17 | 0.80 | 35 |
| v8.66 | 2012 | v866_2012_yearly_round01_case0010 | -1808.98 | 0.90 | 31 |
| v8.66 | 2013 | v866_2013_yearly_round01_case0010 | 29720.37 | 2.77 | 29 |
| v8.66 | 2014 | v866_2014_yearly_round01_case0010 | 2295.28 | 1.11 | 35 |
| v8.66 | 2015 | v866_2015_yearly_round01_case0010 | -4755.31 | 0.63 | 31 |
| v8.66 | 2016 | v866_2016_yearly_round01_case0010 | 14460.36 | 1.67 | 27 |
| v8.66 | 2017 | v866_2017_yearly_round01_case0010 | -629.50 | 0.96 | 37 |
| v8.66 | 2018 | v866_2018_yearly_round01_case0010 | 15040.81 | 1.84 | 24 |
| v8.66 | 2019 | v866_2019_yearly_round01_case0010 | -5048.89 | 0.74 | 38 |
| v8.66 | 2020 | v866_2020_yearly_round01_case0010 | 13833.58 | 1.62 | 29 |
| v8.66 | 2021 | v866_2021_yearly_round01_case0010 | 4501.11 | 1.23 | 33 |
| v8.66 | 2022 | v866_2022_yearly_round01_case0010 | 14170.98 | 1.86 | 37 |
| v8.66 | 2023 | v866_2023_yearly_round01_case0010 | -2509.94 | 0.82 | 34 |

年度结论：

- v8.6 case0502 在 2013、2018、2020 表现很强，但 2015、2017、2019、2023 为负，说明高收益有明显年份依赖。
- v8.66 case0010 在 2013、2016、2018、2020、2021、2022 表现较好，但 2012、2015、2017、2019、2023 为负，仍有年份波动。
- 两个主候选都不能称为“无过拟合风险”；v8.66 的参数扰动稳定性更好，v8.6 的收益弹性更强但敏感性更高。

## 7. 过拟合判断

v8.6：中度过拟合/参数敏感风险。

理由：

- case0005/case0502 在三段窗口表现强，但附近扰动 case0501 在 2015-2019 明显下滑。
- 年度拆解显示利润集中在少数年份，部分年份为负。
- v8.6 可以找到更高收益设定，但更像“收益弹性强、参数敏感也强”的版本。

v8.66：轻度到中度过拟合风险。

理由：

- 结构参数 75/80/85 附近结果接近，没有明显断崖。
- 风控保守候选降低回撤时没有减少交易次数。
- 年度表现仍有负年份，不能判定为无风险。
- v8.66 robust case0010 在 2020-2026 几乎贴住 grok8.6 旧收益锚点，是当前最符合“保住收益主线 + 不明显增加结构风险”的候选。

## 8. 推荐结论

当前主推继续开发参数：

$finalDir\v8.66_robust_main_case0010.set

推荐理由：

- 在原主锚点 2020-2026.06.30 几乎达到 v8.6 旧锚点：$retV866Robust%。
- PF 与交易次数保持在原收益骨架附近。
- 结构参数轻微扰动没有断崖。
- 相比 v8.66 aggressive，风险更可控。

高收益观察参数：

$finalDir\v8.66_aggressive_case0005.set

使用限制：

- 净利润显著更高，但最大净值回撤也明显更高。
- 不建议直接作为主线实盘/模拟参数，应该进入额外压力测试。

保守风控观察参数：

$finalDir\v8.66_conservative_case0401.set

使用价值：

- 回撤降低，交易数不塌缩。
- 适合后续研究“降低回撤阀门”的方向，但收益牺牲明显。

v8.6 参考参数：

- $finalDir\v8.6_robust_main_case0502.set
- $finalDir\v8.6_aggressive_case0005.set
- $finalDir\v8.6_conservative_case0002.set

v8.6 结论：

- v8.6 在早期分段可以通过出场参数获得更高收益。
- 但它在 2020-2026 主锚点不如 v8.66 robust case0010。
- 因此 v8.6 更适合作为收益弹性研究参考，不建议替代 v8.66 当前主线。

## 9. 被淘汰/降级的参数区域

- v8.6 case0501：虽然 2012 表现很强，但 2015-2019 净利润只有 2,639.39，判定为敏感性过强，淘汰为主候选。
- v8.6 case0004：三段总收益低，交易数下降，淘汰。
- v8.66 aggressive case0005：不淘汰，但降级为高收益观察，原因是 2020-2026 最大净值回撤上升到 $(MdEscape @{run_id=v866_2020-2026_control_aggressive_case0005; version=v8.66; window=2020-2026; candidate_class=control-aggressive; net_profit=716968.27; profit_factor=2.29; max_equity_dd=203843.44; max_equity_dd_pct=25.69; total_trades=203}.max_equity_dd)。
- v8.66 structure off / neutral：与 case0010 接近，但 case0010 在结构扰动验证中更适合作为结构主线。

## 10. 残余风险

- 本轮没有执行固定点差放大压力测试，因为当前项目中没有已验证的 MT5 固定点差配置字段，贸然加入可能导致 tester 口径不一致。
- 年度拆解是通过逐年回测完成，未进一步拆到季度/月度。
- v8.66 aggressive case0005 收益很高，需要额外做点差、滑点、手续费、不同经纪商数据源压力验证。
- 本轮未修改 EA 源码，只寻找参数；如果后续继续开发代码，应以 v8.66 robust case0010 作为主线 set。

## 11. 下一步建议

1. 以 8.66_robust_main_case0010.set 作为下一轮代码开发/前向模拟主线。
2. 对 8.66_aggressive_case0005.set 单独做更严格压力测试，确认高收益是否只是加仓放大的结果。
3. 如果目标继续降低回撤，优先研究 8.66_conservative_case0401.set 的风控机制，而不是继续大改入场信号。