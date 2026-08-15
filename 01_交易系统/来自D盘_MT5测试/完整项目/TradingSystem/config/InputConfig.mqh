#ifndef INPUT_CONFIG_MQH
#define INPUT_CONFIG_MQH

input string InpEaName = "TradingSystem_v0.1.7_core_signal_log_throttle";
input long InpMagicNumber = 2026050901;
input bool InpEnableTrading = false;
input bool InpEnableDebugLog = true;
input ENUM_TIMEFRAMES InpSignalTimeframe = PERIOD_M5;
input int InpLogEveryNTicks = 100;
input bool InpPrintStartupConfig = true;
input bool InpEnableHeartbeatLog = false;
input bool InpEnableNewBarLog = true;
input bool InpPrintRuntimeSummary = true;
input bool InpPrintNewBarLog = true;
input int InpNewBarLogEveryN = 1000;
input bool InpPrintCoreLogStatsInSummary = true;
input bool InpPrintSignalLog = true;
input bool InpPrintSignalLogOnlyOnDirectionChange = true;
input int InpSignalLogEveryN = 1000;
input bool InpPrintSignalLogStatsInSummary = true;
input bool InpEnableEmaSignal = true;
input int InpFastEmaPeriod = 20;
input int InpSlowEmaPeriod = 50;
input int InpEmaLookbackShift = 1;
input double InpEmaMinDistancePoints = 0.0;
input bool InpEnableRiskObservation = true;
input double InpMaxSpreadPoints = 300.0;
input bool InpEnableTradingTimeFilter = false;
input int InpTradingStartHour = 0;
input int InpTradingEndHour = 23;
input int InpMaxOpenPositions = 1;
input bool InpPrintAccountStateOnInit = true;
input bool InpPrintRiskObservationLog = true;
input bool InpPrintRiskRejectLog = true;
input bool InpPrintRiskRejectOnlyOnReasonChange = true;
input int InpRiskRejectLogEveryN = 1000;
input bool InpPrintRiskLogStatsInSummary = true;

#endif
