# 回测归档约定（HCSJ）

- 回测配置与结果归档路径：`E:\CODEXMACD\HCSJ\backtest_archive`
- 每次回测必须输出到唯一目录：`yyyyMMdd_HHmmss_版本标签`
- 若版本更新，可改成 `v8.64_softmerge_fix1_r1`、`v8.64_softmerge_fix1_r2` 等作为 `-VersionTag`
- 禁止覆盖旧目录

推荐流程（新增）

1. 运行 MT5 回测：
   ```powershell
   powershell -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\run_and_archive_backtest.ps1" -ConfigPath "E:\CODEXMACD\mt5_configs\sniper_v864_softmerge_fix1_soft_risk_H4_XAUUSD_2020_2025.ini" -VersionTag "v8.64_fix1_soft_risk"
   ```

2. 只做归档（不重复跑回测）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File "E:\CODEXMACD\HCSJ\run_and_archive_backtest.ps1" -ConfigPath "..." -VersionTag "..." -NoRun
   ```

归档结果默认保留：

- 回测 INI
- 参数 `.set`
- EA 引用文件（`.ex5` / `.mq5`）
- 回测报告（`.htm/.html/.xml`）
- `archive_manifest.txt`
