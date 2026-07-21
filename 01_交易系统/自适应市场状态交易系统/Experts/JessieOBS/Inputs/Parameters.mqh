#ifndef _PARAMETERS_MQH_
#define _PARAMETERS_MQH_

input group "========== 风险与资金管理 =========="
input double   InpRiskPercent        = 1.0;       // 单笔风险比例(%)
input double   InpMaxDailyLoss       = 5.0;       // 单日最大亏损比例(%)
input int      InpMaxConsecLoss      = 5;         // 最大连续亏损次数
input double   InpMaxTotalRisk       = 25.0;      // 账户权益安全线(%)
input bool     InpUseFixedLot        = false;     // 使用固定手数
input double   InpFixedLotSize       = 0.1;       // 固定手数(0=禁用)

input group "========== 行情判断模块 =========="
input int      InpADXPeriod          = 14;        // ADX周期
input double   InpADXTrendThreshold  = 25.0;      // ADX趋势阈值
input double   InpADXRangeThreshold  = 20.0;      // ADX震荡阈值
input int      InpMAPeriod           = 200;       // 长期均线周期(MA200)
input int      InpATRPeriod          = 14;        // ATR周期
input int      InpStateSwitchBars    = 5;         // 状态切换最小K线数
input double   InpStateConfidenceReq = 65.0;      // 状态切换置信度要求(%)

input group "========== 趋势策略参数 =========="
input int      InpTrendFastEMA       = 21;        // 趋势快线EMA周期
input int      InpTrendSlowEMA       = 55;        // 趋势慢线EMA周期
input double   InpTrendSLMultiplier  = 2.0;       // 趋势止损ATR倍数
input double   InpTrendTPMultiplier  = 3.5;       // 趋势止盈ATR倍数
input double   InpTrendTrailStart    = 1.5;       // 趋势移动止损启动(ATR倍数)
input double   InpTrendTrailStep     = 0.5;       // 趋势移动止损步长(ATR倍数)
input int      InpTrendMinADX        = 16;        // 趋势策略最低ADX
input int      InpTrendCooldownBars  = 1;         // 趋势策略冷却K线数

input group "========== 震荡策略参数 =========="
input int      InpRangeBBPeriod      = 20;        // 布林带周期
input double   InpRangeBBDeviations  = 2.0;       // 布林带标准差倍数
input int      InpRangeRSIPeriod     = 14;        // RSI周期
input double   InpRangeRSIOB         = 66.0;      // RSI超买阈值
input double   InpRangeRSIOS         = 34.0;      // RSI超卖阈值
input double   InpRangeSLMultiplier  = 0.9;       // 震荡止损ATR倍数
input double   InpRangeTPMultiplier  = 1.8;       // 震荡止盈ATR倍数
input double   InpRangeTrailStart    = 0.8;       // 震荡移动止损启动(ATR倍数)
input double   InpRangeTrailStep     = 0.3;       // 震荡移动止损步长(ATR倍数)
input int      InpRangeCooldownBars  = 1;         // 震荡策略冷却K线数

input group "========== 执行过滤 =========="
input double   InpMaxSpreadPoints    = 50.0;      // 最大允许点差(0=禁用)

input group "========== 持仓限制 =========="
input int      InpMaxTrendPositions  = 2;         // 趋势最大持仓数
input int      InpMaxRangePositions  = 1;         // 震荡最大持仓数
input int      InpMaxTotalPositions  = 3;         // 全局最大持仓数

input group "========== 交易时间过滤 =========="
input bool     InpUseTimeFilter      = false;     // 启用交易时间过滤
input int      InpStartHour          = 1;         // 开始交易(小时,服务器时间)
input int      InpEndHour            = 23;        // 结束交易(小时,服务器时间)
input bool     InpAvoidFridayClose   = true;      // 避开周五收盘
input int      InpFridayStopHour     = 20;        // 周五停止交易(小时)

input group "========== 日志与通知 =========="
input bool     InpEnableLogging      = true;      // 启用日志
input bool     InpEnableAlert        = false;     // 启用警报弹窗
input bool     InpEnablePushNotify   = false;     // 启用推送通知
input int      InpLogLevel           = LOG_INFO;  // 日志级别

#endif
