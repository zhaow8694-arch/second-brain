//+------------------------------------------------------------------+
//|                                         SniperTrendEA_v8.62.mq5 |
//|                    鍩轰簬濞佺澶秼鍔跨嚎绐佺牬 + Evil MACD 鐙欏嚮寮忎氦鏄撶郴缁?|
//|                    v8.6 - 鍔ㄨ兘纭涓庣偣鐏け璐ョ鐞嗙増                |
//|                                                                  |
//|  v8.6 鍦?v8.5 鍩虹涓婃柊澧烇細                                        |
//|                                                                  |
//|  銆?銆戝弻鍚戝崥寮堣繃婊?(WickConflict)锛?                              |
//|       鎬诲奖绾?> 瀹炰綋鏃舵嫆缁濆叆鍦猴紝杩囨护鍗佸瓧鏄?閽堝舰绛変綆璐ㄩ噺绐佺牬銆?      |
//|       鈥斺€?瀵瑰簲銆奛ot All Breakouts Are Equal銆嬨€奣rade Like a Pro銆? |
//|                                                                  |
//|  銆?銆戝姩鑳戒紭鍔跨‘璁?(MomentumDominance)锛?                         |
//|       绐佺牬K绾垮疄浣撻』寮轰簬杩慛鏍瑰弽鍚慘绾挎渶澶у疄浣擄紝纭鍔ㄨ兘杞崲銆?      |
//|       鈥斺€?瀵瑰簲銆婂競鍦虹粨鏋勮瀵熴€嬨€奌igh-Probability Structure Shift銆?|
//|                                                                  |
//|  銆?銆戠偣鐏け璐ュ揩閫熷钩浠?(IgnitionExit)锛?                          |
//|       鍏ュ満鍚庤嫢鍑虹幇鍙嶅悜鍚炴病/鏃犺窡闅忥紝鍦ㄥ皬浜忔崯鑼冨洿鍐呭揩閫熺鍦恒€?      |
//|       鈥斺€?瀵瑰簲銆婄偣鐏笌璺熼殢 (Ignition and Follow-Through)銆?      |
//|                                                                  |
//|  瀹屾暣淇濈暀 v8.5 浜斿眰杩囨护 + v8.4 澶氬洜瀛愭鏋躲€?                      |
//|                                                                  |
//|  v8.61 鏂板杩囨护寮哄害棰勮锛氫繚瀹?v8.5) / 鍧囪　(榛樿) / 绉瀬           |
//|  v8.62 蹇呬慨锛歱ending淇濈暀鑷宠秴鏃?/ 鐐瑰樊淇濇姢 / stops level鏍￠獙        |
//+------------------------------------------------------------------+
#property copyright "SniperTrendEA v8.62 - Wyckoff + Evil MACD + Z-Wei Philosophy"
#property version   "8.63"
#property strict

//--- 杩囨护寮哄害棰勮锛堣В鍐?v8.5 寮€浠撹繃灏戦棶棰橈級
enum ENUM_FILTER_PRESET
{
   FILTER_CONSERVATIVE = 0,  // 淇濆畧锛歷8.5 鍘熺増鍙傛暟锛屼笅鍗曞皯銆佽川閲忛珮
   FILTER_BALANCED     = 1,  // 鍧囪　锛氭帹鑽愰粯璁わ紝閫傚害澧炲姞涓嬪崟棰戠巼
   FILTER_AGGRESSIVE   = 2,  // 绉瀬锛氭槑鏄炬斁瀹斤紝涓嬪崟鏇村
   FILTER_CUSTOM       = 3   // 鑷畾涔夛細浣跨敤涓嬫柟鎵嬪姩鍙傛暟
};

//--- 杈撳叆鍙傛暟
input group "=== 杩囨护寮哄害棰勮锛坴8.62锛?=="
input ENUM_FILTER_PRESET InpFilterPreset = FILTER_BALANCED; // 杩囨护寮哄害锛氫繚瀹?鍧囪　/绉瀬/鑷畾涔?
input group "=== MACD 鍙傛暟 ==="
input int    InpFastEMA        = 12;
input int    InpSlowEMA        = 26;
input int    InpSignalSMA      = 9;

input group "=== MA200 瓒嬪娍杩囨护锛坴8.5: Buffer 鏀圭敤 ATR 鍊嶆暟锛?=="
input int    InpMA200Period    = 200;
input bool   InpUseMA200Filter = true;
input double InpMA200BufferATR = 0.2;       // 浠?FILTER_CUSTOM 鏃剁敓鏁?
input group "=== 鍏ュ満璐ㄩ噺杩囨护锛坴8.5锛屼粎 FILTER_CUSTOM 鏃剁敓鏁堬級==="
input double InpBodyRatio          = 0.55;  // K绾垮疄浣撳崰姣旓紙鍧囪　榛樿 0.55锛?input double InpMaxCandleATR       = 3.0;   // 鍗遍櫓K绾块槇鍊硷紙鍧囪　榛樿 3.0锛?input double InpMaxOppositeShadow  = 0.30;  // 鍙嶅悜褰辩嚎涓婇檺锛堝潎琛￠粯璁?30%锛?input bool   InpRequireFollowThrough = false;
input int    InpFollowThroughBars  = 3;
input int    InpConfirmBars        = 3;     // 缈昏浆纭绛夊緟K绾匡紙鍧囪　榛樿 3锛?input bool   InpRequireMACDDir     = false;

input group "=== 鍏ュ満璐ㄩ噺杩囨护锛坴8.6锛屼粎 FILTER_CUSTOM 鏃剁敓鏁堬級==="
input bool   InpUseWickConflictFilter   = true;
input double InpMaxWickToBodyRatio       = 1.5;   // 鍧囪　榛樿 1.5
input bool   InpRequireMomentumDominance = true;
input int    InpMomentumLookback         = 5;
input double InpMomentumMinRatio         = 0.85;  // 鍧囪　榛樿 0.85

input group "=== Structure Filter (v8.6) ==="
input bool   InpUseStructureFilter      = true;  // 鍚敤瓒嬪娍绾跨粨鏋勮繃婊?input bool   InpRejectNoStructure       = false; // 涓嶅瓨鍦ㄧ粨鏋勬椂鏄惁鎷掔粷涓嬪崟
input int    InpSwingLookback           = 3;     // 宸﹀彸鎽嗗姩纭鐨勫洖鐪嬫煴鏁?input int    InpStructureScanBars       = 80;    // 鎵弿鍘嗗彶K绾挎潯鏁?input int    InpMinTrendlineTouches     = 3;     // 瓒嬪娍绾挎渶灏戞湁鏁堣Е鍙婃暟
input double InpTrendlineTouchATR       = 0.25;  // 瑙﹀強瀹瑰樊锛圓TR鍊嶆暟锛?input double InpMinBreakoutDistanceATR  = 0.10;  // 瓒嬪娍绾跨獊鐮存渶灏忚窛绂伙紙ATR鍊嶆暟锛?input double InpMinBreakoutScore        = 70.0;  // 缁撴瀯璇勫垎鏈€浣庨槇鍊?input bool   InpShowStructureDebug      = false; // 鎵撳嵃缁撴瀯璇勫垎淇℃伅

input group "=== ADX 瓒嬪娍杩囨护 (v8.4) ==="
input bool   InpUseADX          = false;
input int    InpADXPeriod       = 14;
input double InpADXThreshold    = 25.0;

input group "=== 鏃堕棿杩囨护 (v8.4) ==="
input bool   InpUseTimeFilter   = false;
input int    InpStartHour       = 8;
input int    InpEndHour         = 20;

input group "=== 娉㈠姩鐜囪繃婊?(v8.4) ==="
input bool   InpUseATRFilter    = false;
input int    InpATRFilterPeriod = 20;
input double InpATRFilterRatio  = 1.0;

input group "=== 鏃ョ嚎瓒嬪娍纭 (v8.4) ==="
input bool   InpUseDailyFilter  = false;

input group "=== 椋庨櫓绠＄悊 ==="
input double InpRiskPercent    = 0.42;
input double InpATRMultiplier  = 1.55;
input int    InpATRPeriod      = 14;
input double InpTrailingStart  = 4.5;
input double InpTrailingStep   = 2.2;
input int    InpMaxPositions   = 1;

input group "=== 鎸佷粨绠＄悊锛坴8.6 鏂板锛?=="
input bool   InpUseIgnitionExit     = true;   // 鐐圭伀澶辫触蹇€熷钩浠?input int    InpIgnitionMaxBars     = 3;      // 鍏ュ満鍚庤瀵烱绾挎暟
input double InpIgnitionEngulfRatio = 0.82;   // 鍙嶅悜瀹炰綋/鍏ュ満瀹炰綋 瑙﹀彂闃堝€?input double InpIgnitionMaxLossATR  = 0.85;    // 浠呭湪姝TR浜忔崯鑼冨洿鍐呮墽琛岀偣鐏鎹?
input group "=== 浜ゆ槗淇濇姢锛坴8.62锛?=="
input bool   InpUseSpreadFilter = true;   // 鐐瑰樊杩囧ぇ鏃惰烦杩囧紑浠?input int    InpMaxSpreadPoints = 45;     // 鏈€澶у厑璁哥偣宸紙points锛?=浠呭綋寮€鍏冲紑鍚椂鐢ㄩ粯璁わ級

input group "=== 入场质量（软约束）==="
input bool   InpUseEntryQualityFilter   = true;      // 关闭后退回传统硬过滤
input double InpMinEntryQuality         = 0.45;      // 质量低于此值则拒绝入场
input double InpWickConflictPenalty     = 0.65;      // 影线过长的下调因子
input double InpMomentumPenalty         = 0.70;      // 动能不占优的下调因子
input double InpNoStructurePenalty      = 0.70;      // 无结构时的下调因子（保持不拒单）
input double InpMinStructureQualityFloor= 0.35;      // 结构评分不足时的最低保底因子
input double InpSpreadPenaltyFloor      = 0.50;      // 点差超阈值时最低保底因子
input bool   InpDebugEntryQuality       = true;      // 是否输出每笔交易的入场质量日志

input group "=== 浜ゆ槗璁剧疆 ==="
input int    InpMagicNumber    = 20260618;
input string InpComment        = "SniperEA_v8.62";
input bool   InpEnableBuy      = true;
input bool   InpEnableSell     = true;
input bool   InpDebugMode      = true;

//--- 鎸囨爣鍙ユ焺
int g_macdHandle;
int g_atrHandle;
int g_ma200Handle;
int g_adxHandle = INVALID_HANDLE;
int g_atrFilterHandle = INVALID_HANDLE;
int g_dailyMA200Handle = INVALID_HANDLE;

//--- 寰呭叆鍦虹姸鎬?bool     g_pendingBuy  = false;
bool     g_pendingSell = false;
int      g_pendingBars = 0;

//--- K绾挎椂闂存埑
datetime g_lastTrailBarTime = 0;
datetime g_lastEntryBarTime = 0;

//--- 鍏ュ満璺熻釜锛堢偣鐏け璐ユ娴嬶級
datetime g_entryBarTime  = 0;
double   g_entryBodySize = 0;

//--- 鐢熸晥涓殑杩囨护鍙傛暟锛堢敱棰勮鎴栨墜鍔ㄥ弬鏁板啓鍏ワ級
double g_bodyRatio;
double g_maxCandleATR;
double g_maxOppositeShadow;
double g_ma200BufferATR;
int    g_confirmBars;
bool   g_requireFollowThrough;
int    g_followThroughBars;
bool   g_useWickConflict;
double g_maxWickToBody;
bool   g_requireMomentum;
int    g_momentumLookback;
double g_momentumMinRatio;
string g_presetName = "";

//+------------------------------------------------------------------+
//| 搴旂敤杩囨护寮哄害棰勮                                                  |
//+------------------------------------------------------------------+
void ApplyFilterPreset()
{
   switch(InpFilterPreset)
   {
      case FILTER_CONSERVATIVE:
         g_bodyRatio            = 0.60;
         g_maxCandleATR         = 2.5;
         g_maxOppositeShadow    = 0.20;
         g_ma200BufferATR       = 0.0;
         g_confirmBars          = 4;
         g_requireFollowThrough = false;
         g_followThroughBars    = 3;
         g_useWickConflict      = true;
         g_maxWickToBody        = 1.0;
         g_requireMomentum      = true;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 1.0;
         g_presetName           = "淇濆畧(v8.5)";
         break;

      case FILTER_BALANCED:
         g_bodyRatio            = 0.55;
         g_maxCandleATR         = 3.0;
         g_maxOppositeShadow    = 0.30;
         g_ma200BufferATR       = 0.2;
         g_confirmBars          = 3;
         g_requireFollowThrough = false;
         g_followThroughBars    = 3;
         g_useWickConflict      = true;
         g_maxWickToBody        = 1.5;
         g_requireMomentum      = true;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 0.85;
         g_presetName           = "鍧囪　(鎺ㄨ崘)";
         break;

      case FILTER_AGGRESSIVE:
         g_bodyRatio            = 0.50;
         g_maxCandleATR         = 3.5;
         g_maxOppositeShadow    = 0.35;
         g_ma200BufferATR       = 0.3;
         g_confirmBars          = 3;
         g_requireFollowThrough = false;
         g_followThroughBars    = 2;
         g_useWickConflict      = false;
         g_maxWickToBody        = 2.0;
         g_requireMomentum      = false;
         g_momentumLookback     = 5;
         g_momentumMinRatio     = 0.75;
         g_presetName           = "绉瀬";
         break;

      default:
         g_bodyRatio            = InpBodyRatio;
         g_maxCandleATR         = InpMaxCandleATR;
         g_maxOppositeShadow    = InpMaxOppositeShadow;
         g_ma200BufferATR       = InpMA200BufferATR;
         g_confirmBars          = InpConfirmBars;
         g_requireFollowThrough = InpRequireFollowThrough;
         g_followThroughBars    = InpFollowThroughBars;
         g_useWickConflict      = InpUseWickConflictFilter;
         g_maxWickToBody        = InpMaxWickToBodyRatio;
         g_requireMomentum      = InpRequireMomentumDominance;
         g_momentumLookback     = InpMomentumLookback;
         g_momentumMinRatio     = InpMomentumMinRatio;
         g_presetName           = "鑷畾涔?;
         break;
   }
}

//+------------------------------------------------------------------+
//| 鍒濆鍖?                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   g_macdHandle = iMACD(_Symbol, PERIOD_CURRENT, InpFastEMA, InpSlowEMA, InpSignalSMA, PRICE_CLOSE);
   if(g_macdHandle == INVALID_HANDLE) return INIT_FAILED;

   g_atrHandle = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   if(g_atrHandle == INVALID_HANDLE) return INIT_FAILED;

   g_ma200Handle = iMA(_Symbol, PERIOD_CURRENT, InpMA200Period, 0, MODE_SMA, PRICE_CLOSE);
   if(g_ma200Handle == INVALID_HANDLE) return INIT_FAILED;

   if(InpUseADX)
   {
      g_adxHandle = iADX(_Symbol, PERIOD_CURRENT, InpADXPeriod);
      if(g_adxHandle == INVALID_HANDLE) return INIT_FAILED;
   }

   if(InpUseATRFilter)
   {
      g_atrFilterHandle = iMA(_Symbol, PERIOD_CURRENT, InpATRFilterPeriod, 0, MODE_SMA, g_atrHandle);
      if(g_atrFilterHandle == INVALID_HANDLE) return INIT_FAILED;
   }

   if(InpUseDailyFilter)
   {
      g_dailyMA200Handle = iMA(_Symbol, PERIOD_D1, 200, 0, MODE_SMA, PRICE_CLOSE);
      if(g_dailyMA200Handle == INVALID_HANDLE) return INIT_FAILED;
   }

   g_pendingBuy       = false;
   g_pendingSell      = false;
   g_pendingBars      = 0;
   g_lastTrailBarTime = 0;
   g_lastEntryBarTime = 0;
   g_entryBarTime     = 0;
   g_entryBodySize    = 0;

   ApplyFilterPreset();

   Print("SniperTrendEA v8.62 鍒濆鍖栨垚鍔?| ", _Symbol, " ", EnumToString(Period()),
         " | 棰勮:", g_presetName,
         " | 瀹炰綋鈮?, DoubleToString(g_bodyRatio * 100, 0), "%",
         " | 鍙嶅悜褰扁墹", DoubleToString(g_maxOppositeShadow * 100, 0), "%",
         " | 鍗遍櫓K鈮?, g_maxCandleATR, "脳ATR",
         " | 鍗氬紙:", g_useWickConflict ? "ON" : "OFF",
         " | 鍔ㄨ兘:", g_requireMomentum ? "ON" : "OFF",
         " | 鐐圭伀姝㈡崯:", InpUseIgnitionExit ? "ON" : "OFF");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| 閲婃斁                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(g_macdHandle  != INVALID_HANDLE) IndicatorRelease(g_macdHandle);
   if(g_atrHandle   != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
   if(g_ma200Handle != INVALID_HANDLE) IndicatorRelease(g_ma200Handle);
   if(g_adxHandle   != INVALID_HANDLE) IndicatorRelease(g_adxHandle);
   if(g_atrFilterHandle  != INVALID_HANDLE) IndicatorRelease(g_atrFilterHandle);
   if(g_dailyMA200Handle != INVALID_HANDLE) IndicatorRelease(g_dailyMA200Handle);
   Comment("");
}

//+------------------------------------------------------------------+
//| 涓婚€昏緫                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == 0) return;

   int posCount = CountPositions();

   // 鎸佷粨绠＄悊锛堟瘡鏍筀绾夸竴娆★級
   if(currentBarTime != g_lastTrailBarTime && posCount > 0)
   {
      g_lastTrailBarTime = currentBarTime;
      double atrBuf[]; ArrayResize(atrBuf, 2); ArraySetAsSeries(atrBuf, true);
      if(CopyBuffer(g_atrHandle, 0, 1, 2, atrBuf) >= 2 && atrBuf[0] > 0)
      {
         SyncEntryTracking();
         ManageIgnitionExit(atrBuf[0]);
         if(CountPositions() > 0)
            ManageTrailingStop(atrBuf[0]);
      }
   }

   if(posCount == 0)
   {
      g_entryBarTime  = 0;
      g_entryBodySize = 0;
   }

   // 鍏ュ満閫昏緫锛堟瘡鏍筀绾夸竴娆★級
   if(currentBarTime == g_lastEntryBarTime) return;
   g_lastEntryBarTime = currentBarTime;

   double macdMain[], macdSig[], atrBuf2[], ma200Buf[];
   ArrayResize(macdMain, 4); ArrayResize(macdSig, 4); ArrayResize(atrBuf2, 4); ArrayResize(ma200Buf, 3);
   ArraySetAsSeries(macdMain, true); ArraySetAsSeries(macdSig, true);
   ArraySetAsSeries(atrBuf2, true); ArraySetAsSeries(ma200Buf, true);

   if(CopyBuffer(g_macdHandle, 0, 0, 4, macdMain) < 4 ||
      CopyBuffer(g_macdHandle, 1, 0, 4, macdSig) < 4 ||
      CopyBuffer(g_atrHandle, 0, 0, 4, atrBuf2) < 4 ||
      CopyBuffer(g_ma200Handle, 0, 0, 3, ma200Buf) < 3) return;

   double hist1 = macdMain[1] - macdSig[1];
   double hist2 = macdMain[2] - macdSig[2];
   double macd1 = macdMain[1];
   double macd2 = macdMain[2];
   double atr1  = atrBuf2[1];
   double ma200 = ma200Buf[1];

   if(atr1 <= 0 || ma200 <= 0) return;

   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   double bodyRatio = GetBodyRatio(1);

   double ma200Buffer = atr1 * g_ma200BufferATR;
   bool aboveMA200 = (prevClose > ma200 + ma200Buffer);
   bool belowMA200 = (prevClose < ma200 - ma200Buffer);

   bool adxOk = true, timeOk = true, atrFilterOk = true;
   bool dailyUp = true, dailyDown = true;

   if(InpUseADX && g_adxHandle != INVALID_HANDLE)
   {
      double adxBuf[]; ArrayResize(adxBuf, 2); ArraySetAsSeries(adxBuf, true);
      if(CopyBuffer(g_adxHandle, 0, 0, 2, adxBuf) >= 2)
         adxOk = (adxBuf[1] > InpADXThreshold);
   }

   if(InpUseTimeFilter)
   {
      MqlDateTime dt; TimeToStruct(currentBarTime, dt);
      if(InpStartHour <= InpEndHour)
         timeOk = (dt.hour >= InpStartHour && dt.hour <= InpEndHour);
      else
         timeOk = (dt.hour >= InpStartHour || dt.hour <= InpEndHour);
   }

   if(InpUseATRFilter && g_atrFilterHandle != INVALID_HANDLE)
   {
      double atrAvgBuf[]; ArrayResize(atrAvgBuf, 2); ArraySetAsSeries(atrAvgBuf, true);
      if(CopyBuffer(g_atrFilterHandle, 0, 0, 2, atrAvgBuf) >= 2)
         atrFilterOk = (atr1 > atrAvgBuf[1] * InpATRFilterRatio);
   }

   if(InpUseDailyFilter && g_dailyMA200Handle != INVALID_HANDLE)
   {
      double dMaBuf[]; ArrayResize(dMaBuf, 2); ArraySetAsSeries(dMaBuf, true);
      if(CopyBuffer(g_dailyMA200Handle, 0, 0, 2, dMaBuf) >= 2)
      {
         double dClose = iClose(_Symbol, PERIOD_D1, 1);
         dailyUp   = (dClose > dMaBuf[1]);
         dailyDown = (dClose < dMaBuf[1]);
      }
   }

   if(InpDebugMode)
   {
      string trendStr = "闇囪崱鍖?;
      if(aboveMA200) trendStr = "澶氬ご瓒嬪娍";
      if(belowMA200) trendStr = "绌哄ご瓒嬪娍";
      Comment("SniperEA v8.62 | 棰勮:", g_presetName, " | ", _Symbol, " ", EnumToString(Period()), "\n",
              "瓒嬪娍:", trendStr, " | MA200:", DoubleToString(ma200, _Digits),
              " | 鏀剁洏:", DoubleToString(prevClose, _Digits), "\n",
              "ATR:", DoubleToString(atr1, _Digits),
              " | 瀹炰綋:", DoubleToString(bodyRatio * 100, 1), "%",
              " (闇€鈮?, DoubleToString(g_bodyRatio * 100, 0), "%)",
              " | 褰?浣?", DoubleToString(GetWickToBodyRatio(1), 2), "\n",
              "鍔ㄨ兘:", g_requireMomentum ?
                     (HasMomentumDominance(true, 1) ? "澶歄K" : "澶氬急") : "OFF",
              " | 鍗氬紙:", IsWickConflictCandle(1) ? "鍐茬獊" : "骞插噣", "\n",
              "ADX:", adxOk ? "OK" : "FAIL",
              " | 鎸佷粨:", CountPositions(), "/", InpMaxPositions,
              " | 鐐圭伀鐩戞帶:", (g_entryBarTime > 0 && InpUseIgnitionExit) ? "ON" : "OFF");
   }

   posCount = CountPositions();
   if(posCount < InpMaxPositions)
   {
      bool flipUp   = (hist1 > 0 && hist2 <= 0);
      bool flipDown = (hist1 < 0 && hist2 >= 0);

      if(flipUp && InpEnableBuy && !g_pendingBuy)
      {
         if(!InpUseMA200Filter || aboveMA200)
         { g_pendingSell = false; g_pendingBuy = true; g_pendingBars = 0; }
      }

      if(flipDown && InpEnableSell && !g_pendingSell)
      {
         if(!InpUseMA200Filter || belowMA200)
         { g_pendingBuy = false; g_pendingSell = true; g_pendingBars = 0; }
      }

      if(g_pendingBuy || g_pendingSell)
      {
         g_pendingBars++;
         if(g_pendingBars > g_confirmBars)
         { g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0; }
         else
         {
             bool macdUp   = (macd1 >= macd2);
             bool macdDown = (macd1 <= macd2);
             bool dangerCandle = IsDangerousCandle(1, atr1);
             bool wickConflict = IsWickConflictCandle(1);
             bool structureOk = true;
             bool momentumOk = true;
             bool spreadOk = true;
             STrendlineInfo structureInfo;
             ResetTrendlineInfo(structureInfo);
             double structureQuality = 1.0;
             double wickPenalty = 1.0;
             double momentumPenalty = 1.0;
             double spreadQuality = 1.0;
             double entryQuality = 1.0;
             int spreadPoints = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
             if(spreadPoints < 0) spreadPoints = 0;

             if(g_pendingBuy)
                structureOk = GetStructureQualityFactor(true, atr1, dangerCandle, structureInfo, structureQuality);
             else if(g_pendingSell)
                structureOk = GetStructureQualityFactor(false, atr1, dangerCandle, structureInfo, structureQuality);

             if(g_pendingBuy)
                momentumOk = HasMomentumDominance(true, 1);
             else if(g_pendingSell)
                momentumOk = HasMomentumDominance(false, 1);

             if(g_useWickConflict && wickConflict)
                wickPenalty = ClampDouble(InpWickConflictPenalty, 0.0, 1.0);

             if(!g_requireMomentum || momentumOk)
                momentumPenalty = 1.0;
             else
                momentumPenalty = ClampDouble(InpMomentumPenalty, 0.0, 1.0);

             spreadOk = IsSpreadAcceptable();
             if(!InpUseSpreadFilter || spreadOk || InpMaxSpreadPoints <= 0)
                spreadQuality = 1.0;
             else
                spreadQuality = ClampDouble((double)InpMaxSpreadPoints / (double)MathMax(spreadPoints, 1), ClampDouble(InpSpreadPenaltyFloor, 0.0, 1.0), 1.0);

             if(!InpUseEntryQualityFilter)
                entryQuality = 1.0;
             else
                entryQuality = ClampDouble(structureQuality * wickPenalty * momentumPenalty * spreadQuality, 0.0, 1.0);

            if(g_pendingBuy && IsBullishCandle(1) && bodyRatio >= g_bodyRatio &&
               (!InpRequireMACDDir || macdUp) && (!InpUseMA200Filter || aboveMA200) &&
                adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyUp))
            {
               if(dangerCandle)
               {
                  Print("銆愬嵄闄㎏绾?澶氥€戞尟骞?", g_maxCandleATR, "脳ATR锛屾湰鏍硅烦杩囷紝淇濈暀pending");
               }
                else if(!InpUseEntryQualityFilter && wickConflict)
                {
                   Print("入场信号影线冲突，略过");
                }
                else if(!InpUseEntryQualityFilter && InpUseStructureFilter && structureOk && structureInfo.valid && structureInfo.score < InpMinBreakoutScore)
                {
                   Print("结构未通过且未配置退化接收：直接拒绝，score=", DoubleToString(structureInfo.score, 1));
                }
                else if(InpUseEntryQualityFilter && entryQuality < InpMinEntryQuality)
                {
                   if(InpDebugEntryQuality)
                   {
                      Print("入场质量不足，买入跳过 | quality=", DoubleToString(entryQuality, 3),
                            " wick=", DoubleToString(wickPenalty, 2),
                            " momentum=", DoubleToString(momentumPenalty, 2),
                            " structure=", DoubleToString(structureQuality, 2),
                            " spread=", DoubleToString(spreadQuality, 2),
                            " spreadPts=", spreadPoints);
                   }
                }
                else if(GetUpperShadowRatio(1) > g_maxOppositeShadow)
                {
                   Print("銆愪笂褰辫繃闀?澶氥€戞湰鏍硅烦杩囷紝淇濈暀pending");
                }
                else if(!InpUseEntryQualityFilter && g_requireMomentum && !momentumOk)
                {
                   Print("銆愬姩鑳戒笉瓒?澶氥€戝疄浣撴湭寮轰簬杩?, g_momentumLookback, "鏍归槾绾匡紝鏈牴璺宠繃锛屼繚鐣檖ending");
                }
               else if(g_requireFollowThrough && !IsHighestClose(1, g_followThroughBars))
               {
                  Print("銆愯窡闅忕‘璁ゅけ璐?澶氥€戞湭鍒涙柊楂橈紝绛夊緟");
               }
                else if(!spreadOk && !InpUseEntryQualityFilter)
                {
                   Print("銆愮偣宸繃澶?澶氥€戝綋鍓嶇偣宸?", SymbolInfoInteger(_Symbol, SYMBOL_SPREAD),
                         " > ", InpMaxSpreadPoints, "锛屾湰鏍硅烦杩囷紝淇濈暀pending");
                }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                  double sl = NormalizeDouble(ep - atr1 * InpATRMultiplier, _Digits);
                  if(!NormalizeStopForOpen(ORDER_TYPE_BUY, ep, sl))
                  {
                     Print("銆愭鎹熻窛绂讳笉瓒?澶氥€戞棤娉曟弧瓒崇粡绾晢鏈€灏忔鎹熻窛绂伙紝鏈牴璺宠繃锛屼繚鐣檖ending");
                  }
                  else
                  {
                     double lot = CalculateLotSize(ep - sl);
                     if(InpUseEntryQualityFilter && lot > 0)
                        lot = MathFloor(lot * entryQuality / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
                      Print("銆愬紑澶氥€戝疄浣?", DoubleToString(bodyRatio * 100, 1), "%",
                            " | 褰?浣?", DoubleToString(GetWickToBodyRatio(1), 2),
                            " | EP:", ep, " SL:", sl, " Lot:", lot,
                            " | EntryQ:", DoubleToString(entryQuality, 3));
                     if(lot > 0 && OpenPosition(ORDER_TYPE_BUY, ep, sl, lot))
                     {
                        g_pendingBuy = false; g_pendingBars = 0;
                     }
                  }
               }
            }

            if(g_pendingSell && IsBearishCandle(1) && bodyRatio >= g_bodyRatio &&
               (!InpRequireMACDDir || macdDown) && (!InpUseMA200Filter || belowMA200) &&
                 adxOk && timeOk && atrFilterOk && (!InpUseDailyFilter || dailyDown))
            {
               if(dangerCandle)
               {
                  Print("銆愬嵄闄㎏绾?绌恒€戞尟骞?", g_maxCandleATR, "脳ATR锛屾湰鏍硅烦杩囷紝淇濈暀pending");
               }
                else if(!InpUseEntryQualityFilter && wickConflict)
                {
                   Print("入场信号影线冲突，略过");
                }
                else if(!InpUseEntryQualityFilter && InpUseStructureFilter && structureOk && structureInfo.valid && structureInfo.score < InpMinBreakoutScore)
                {
                   Print("结构未通过且未配置退化接收：直接拒绝，score=", DoubleToString(structureInfo.score, 1));
                }
                else if(InpUseEntryQualityFilter && entryQuality < InpMinEntryQuality)
                {
                   if(InpDebugEntryQuality)
                   {
                      Print("入场质量不足，卖出跳过 | quality=", DoubleToString(entryQuality, 3),
                            " wick=", DoubleToString(wickPenalty, 2),
                            " momentum=", DoubleToString(momentumPenalty, 2),
                            " structure=", DoubleToString(structureQuality, 2),
                            " spread=", DoubleToString(spreadQuality, 2),
                            " spreadPts=", spreadPoints);
                   }
                }
               else if(GetLowerShadowRatio(1) > g_maxOppositeShadow)
               {
                  Print("銆愪笅褰辫繃闀?绌恒€戞湰鏍硅烦杩囷紝淇濈暀pending");
               }
                else if(!InpUseEntryQualityFilter && g_requireMomentum && !momentumOk)
                {
                   Print("銆愬姩鑳戒笉瓒?绌恒€戝疄浣撴湭寮轰簬杩?, g_momentumLookback, "鏍归槼绾匡紝鏈牴璺宠繃锛屼繚鐣檖ending");
                }
               else if(g_requireFollowThrough && !IsLowestClose(1, g_followThroughBars))
               {
                  Print("銆愯窡闅忕‘璁ゅけ璐?绌恒€戞湭鍒涙柊浣庯紝绛夊緟");
               }
                else if(!spreadOk && !InpUseEntryQualityFilter)
                {
                   Print("銆愮偣宸繃澶?绌恒€戝綋鍓嶇偣宸?", SymbolInfoInteger(_Symbol, SYMBOL_SPREAD),
                         " > ", InpMaxSpreadPoints, "锛屾湰鏍硅烦杩囷紝淇濈暀pending");
                }
               else
               {
                  double ep = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                  double sl = NormalizeDouble(ep + atr1 * InpATRMultiplier, _Digits);
                  if(!NormalizeStopForOpen(ORDER_TYPE_SELL, ep, sl))
                  {
                     Print("銆愭鎹熻窛绂讳笉瓒?绌恒€戞棤娉曟弧瓒崇粡绾晢鏈€灏忔鎹熻窛绂伙紝鏈牴璺宠繃锛屼繚鐣檖ending");
                  }
                  else
                  {
                      double lot = CalculateLotSize(sl - ep);
                      if(InpUseEntryQualityFilter && lot > 0)
                         lot = MathFloor(lot * entryQuality / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
                      Print("銆愬紑绌恒€戝疄浣?", DoubleToString(bodyRatio * 100, 1), "%",
                            " | 褰?浣?", DoubleToString(GetWickToBodyRatio(1), 2),
                            " | EP:", ep, " SL:", sl, " Lot:", lot,
                            " | EntryQ:", DoubleToString(entryQuality, 3));
                     if(lot > 0 && OpenPosition(ORDER_TYPE_SELL, ep, sl, lot))
                     {
                        g_pendingSell = false; g_pendingBars = 0;
                     }
                  }
               }
            }
         }
      }
   }
   else
   { g_pendingBuy = false; g_pendingSell = false; g_pendingBars = 0; }
}

//+------------------------------------------------------------------+
//| 銆恦8.6銆戠偣鐏け璐ュ揩閫熷钩浠?                                         |
//+------------------------------------------------------------------+
void ManageIgnitionExit(double atr)
{
   if(!InpUseIgnitionExit || atr <= 0 || g_entryBarTime == 0) return;

   int entryShift = iBarShift(_Symbol, PERIOD_CURRENT, g_entryBarTime, true);
   if(entryShift < 0) { g_entryBarTime = 0; return; }

   int barsSinceEntry = entryShift - 1;
   if(barsSinceEntry < 1 || barsSinceEntry > InpIgnitionMaxBars) return;

   double entryBody = g_entryBodySize;
   if(entryBody <= 0) entryBody = GetCandleBody(entryShift);

   double entryOpen  = iOpen (_Symbol, PERIOD_CURRENT, entryShift);
   double entryClose = iClose(_Symbol, PERIOD_CURRENT, entryShift);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      bool ignitionFailed = false;
      string failReason = "";

      if(posType == POSITION_TYPE_BUY)
      {
         if(IsIgnitionFailedLong(entryShift, entryBody, entryOpen, entryClose, failReason))
            ignitionFailed = true;
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         if(IsIgnitionFailedShort(entryShift, entryBody, entryOpen, entryClose, failReason))
            ignitionFailed = true;
      }

      if(!ignitionFailed) continue;

      double curPrice = (posType == POSITION_TYPE_BUY) ?
                        SymbolInfoDouble(_Symbol, SYMBOL_BID) :
                        SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double lossDist = (posType == POSITION_TYPE_BUY) ?
                        (openPrice - curPrice) : (curPrice - openPrice);

      if(lossDist <= atr * InpIgnitionMaxLossATR)
      {
         Print("銆愮偣鐏け璐ュ钩浠撱€?, failReason, " | 浜忔崯:", DoubleToString(lossDist, _Digits),
               " (鈮?, InpIgnitionMaxLossATR, "脳ATR)");
         ClosePosition(ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| 澶氬ご鐐圭伀澶辫触锛氬弽鍚戝悶娌?/ 鏃犺窡闅?                                   |
//+------------------------------------------------------------------+
bool IsIgnitionFailedLong(int entryShift, double entryBody, double entryOpen,
                          double entryClose, string &reason)
{
   double body1 = GetCandleBody(1);
   if(body1 <= 0) return false;

   if(IsBearishCandle(1) && body1 >= entryBody * InpIgnitionEngulfRatio)
   {
      reason = "鍙嶅悜闃寸嚎瀹炰綋鈮ュ叆鍦哄疄浣?;
      return true;
   }

   if(IsBearishCandle(1) &&
      iOpen(_Symbol, PERIOD_CURRENT, 1) >= entryClose &&
      iClose(_Symbol, PERIOD_CURRENT, 1) <= entryOpen)
   {
      reason = "鐪嬭穼鍚炴病鍏ュ満K绾?;
      return true;
   }

   if(IsBullishCandle(1) && GetUpperShadowRatio(1) > 0.45)
   {
      reason = "涓婂奖绾胯繃闀匡紝澶氭柟鍔ㄨ兘琛扮";
      return true;
   }

   if(IsBullishCandle(1) && entryShift >= 2)
   {
      double body2 = GetCandleBody(2);
      if(body2 > 0 && body1 < body2 * 0.6 && !IsHighestClose(1, 1))
      {
         reason = "璺熼殢涔忓姏锛氶槼绾跨缉閲忎笖鏈垱鏂伴珮";
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| 绌哄ご鐐圭伀澶辫触锛氬弽鍚戝悶娌?/ 鏃犺窡闅?                                   |
//+------------------------------------------------------------------+
bool IsIgnitionFailedShort(int entryShift, double entryBody, double entryOpen,
                           double entryClose, string &reason)
{
   double body1 = GetCandleBody(1);
   if(body1 <= 0) return false;

   if(IsBullishCandle(1) && body1 >= entryBody * InpIgnitionEngulfRatio)
   {
      reason = "鍙嶅悜闃崇嚎瀹炰綋鈮ュ叆鍦哄疄浣?;
      return true;
   }

   if(IsBullishCandle(1) &&
      iOpen(_Symbol, PERIOD_CURRENT, 1) <= entryClose &&
      iClose(_Symbol, PERIOD_CURRENT, 1) >= entryOpen)
   {
      reason = "鐪嬫定鍚炴病鍏ュ満K绾?;
      return true;
   }

   if(IsBearishCandle(1) && GetLowerShadowRatio(1) > 0.45)
   {
      reason = "涓嬪奖绾胯繃闀匡紝绌烘柟鍔ㄨ兘琛扮";
      return true;
   }

   if(IsBearishCandle(1) && entryShift >= 2)
   {
      double body2 = GetCandleBody(2);
      if(body2 > 0 && body1 < body2 * 0.6 && !IsLowestClose(1, 1))
      {
         reason = "璺熼殢涔忓姏锛氶槾绾跨缉閲忎笖鏈垱鏂颁綆";
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| 浠庢寔浠撴仮澶嶅叆鍦篕绾胯窡韪?                                            |
//+------------------------------------------------------------------+
void SyncEntryTracking()
{
   if(g_entryBarTime > 0) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      datetime posTime = (datetime)PositionGetInteger(POSITION_TIME);
      int shift = iBarShift(_Symbol, PERIOD_CURRENT, posTime, true);
      if(shift < 0) shift = 1;

      g_entryBarTime  = iTime(_Symbol, PERIOD_CURRENT, shift);
      g_entryBodySize = GetCandleBody(shift);
      break;
   }
}

//+------------------------------------------------------------------+
//| 绉诲姩姝㈢泩                                                          |
//+------------------------------------------------------------------+
void ManageTrailingStop(double atr)
{
   if(atr <= 0) return;
   double prevClose = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(prevClose <= 0) return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curSL     = PositionGetDouble(POSITION_SL);
      ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(posType == POSITION_TYPE_BUY)
      {
         double startLevel = openPrice + atr * InpTrailingStart;
         if(prevClose > startLevel)
         {
            double newSL = NormalizeDouble(prevClose - atr * InpTrailingStep, _Digits);
            if(newSL > curSL + _Point) ModifyStopLoss(ticket, newSL);
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double startLevel = openPrice - atr * InpTrailingStart;
         if(prevClose < startLevel)
         {
            double newSL = NormalizeDouble(prevClose + atr * InpTrailingStep, _Digits);
            if(curSL == 0 || newSL < curSL - _Point) ModifyStopLoss(ticket, newSL);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 銆恦8.6銆戝弻鍚戝崥寮堬細鎬诲奖绾?vs 瀹炰綋                                   |
//+------------------------------------------------------------------+
bool IsWickConflictCandle(int shift)
{
   if(!g_useWickConflict) return false;
   return (GetWickToBodyRatio(shift) > g_maxWickToBody);
}

double GetWickToBodyRatio(int shift)
{
   double body = GetCandleBody(shift);
   if(body <= 0) return 999.0;
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double wicks = (high - MathMax(open, close)) + (MathMin(open, close) - low);
   return wicks / body;
}

//+------------------------------------------------------------------+
//| 銆恦8.6銆戝姩鑳戒紭鍔匡細绐佺牬瀹炰綋寮轰簬杩戞湡鍙嶅悜K绾?                         |
//+------------------------------------------------------------------+
bool HasMomentumDominance(bool forBuy, int shift)
{
   if(!g_requireMomentum) return true;

   double entryBody = GetCandleBody(shift);
   if(entryBody <= 0) return false;

   double maxOppBody = 0;
   int lookback = MathMax(1, g_momentumLookback);

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isOpposite = forBuy ? IsBearishCandle(i) : IsBullishCandle(i);
      if(!isOpposite) continue;
      double b = GetCandleBody(i);
      if(b > maxOppBody) maxOppBody = b;
   }

   if(maxOppBody <= 0) return true;
   return (entryBody >= maxOppBody * g_momentumMinRatio);
}

//+------------------------------------------------------------------+
//| K绾垮疄浣擄紙缁濆鍊硷級                                                  |
//+------------------------------------------------------------------+
double GetCandleBody(int shift)
{
   return MathAbs(iClose(_Symbol, PERIOD_CURRENT, shift) -
                iOpen (_Symbol, PERIOD_CURRENT, shift));
}

//+------------------------------------------------------------------+
//| 銆恦8.5銆戝嵄闄㎏绾垮垽鏂?                                               |
//+------------------------------------------------------------------+
bool IsDangerousCandle(int shift, double atr)
{
   if(g_maxCandleATR <= 0 || atr <= 0) return false;
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   return (range > atr * g_maxCandleATR);
}

double GetUpperShadowRatio(int shift)
{
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double range = high - low;
   if(range <= 0) return 0;
   return (high - MathMax(open, close)) / range;
}

double GetLowerShadowRatio(int shift)
{
   double open  = iOpen (_Symbol, PERIOD_CURRENT, shift);
   double close = iClose(_Symbol, PERIOD_CURRENT, shift);
   double high  = iHigh (_Symbol, PERIOD_CURRENT, shift);
   double low   = iLow  (_Symbol, PERIOD_CURRENT, shift);
   double range = high - low;
   if(range <= 0) return 0;
   return (MathMin(open, close) - low) / range;
}

bool IsHighestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
      if(iClose(_Symbol, PERIOD_CURRENT, i) >= targetClose) return false;
   return true;
}

bool IsLowestClose(int shift, int lookback)
{
   double targetClose = iClose(_Symbol, PERIOD_CURRENT, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
      if(iClose(_Symbol, PERIOD_CURRENT, i) <= targetClose) return false;
   return true;
}

//+------------------------------------------------------------------+
//| v8.6 trendline structure scoring                                    |
//+------------------------------------------------------------------+
struct STrendlineInfo
{
   bool   valid;
   int    touches;
   int    anchorShiftOld;
   int    anchorShiftNew;
   double anchorPriceOld;
   double anchorPriceNew;
   double lineAtSignal;
   double breakoutDistance;
   double breakoutDistanceATR;
   double score;
};

void ResetTrendlineInfo(STrendlineInfo &info)
{
   info.valid = false;
   info.touches = 0;
   info.anchorShiftOld = -1;
   info.anchorShiftNew = -1;
   info.anchorPriceOld = 0.0;
   info.anchorPriceNew = 0.0;
   info.lineAtSignal = 0.0;
   info.breakoutDistance = 0.0;
   info.breakoutDistanceATR = 0.0;
   info.score = 0.0;
}

double ClampDouble(double value, double minValue, double maxValue)
{
   return MathMax(minValue, MathMin(maxValue, value));
}

bool IsSwingHigh(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double high = iHigh(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iHigh(_Symbol, PERIOD_CURRENT, shift - i) >= high) return false;
      if(iHigh(_Symbol, PERIOD_CURRENT, shift + i) >= high) return false;
   }
   return true;
}

bool IsSwingLow(int shift, int lookback)
{
   if(shift - lookback < 1) return false;
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(shift + lookback >= bars) return false;

   double low = iLow(_Symbol, PERIOD_CURRENT, shift);
   for(int i = 1; i <= lookback; i++)
   {
      if(iLow(_Symbol, PERIOD_CURRENT, shift - i) <= low) return false;
      if(iLow(_Symbol, PERIOD_CURRENT, shift + i) <= low) return false;
   }
   return true;
}

double LineValueAtShift(int oldShift, double oldPrice, int newShift, double newPrice, int targetShift)
{
   if(newShift == oldShift) return newPrice;
   double slope = (newPrice - oldPrice) / (double)(newShift - oldShift);
   return oldPrice + slope * (double)(targetShift - oldShift);
}

int CountTrendlineTouches(bool forBuy, int oldShift, double oldPrice, int newShift, double newPrice, double atr)
{
   if(atr <= 0) return 0;
   double touchDistance = atr * InpTrendlineTouchATR;
   int touches = 0;

   for(int shift = oldShift; shift >= newShift; shift--)
   {
      double lineValue = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, shift);
      double actual = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, shift) : iLow(_Symbol, PERIOD_CURRENT, shift);
      if(MathAbs(actual - lineValue) <= touchDistance)
         touches++;
   }

   return touches;
}

bool FindValidatedTrendline(bool forBuy, double atr, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(atr <= 0 || InpSwingLookback < 1 || InpMinTrendlineTouches < 2) return false;

   int bars = Bars(_Symbol, PERIOD_CURRENT);
   int maxShift = MathMin(InpStructureScanBars, bars - InpSwingLookback - 2);
   int minShift = InpSwingLookback + 1;
   if(maxShift <= minShift + InpSwingLookback) return false;

   for(int newShift = minShift; newShift <= maxShift - InpSwingLookback; newShift++)
   {
      bool newSwing = forBuy ? IsSwingHigh(newShift, InpSwingLookback) : IsSwingLow(newShift, InpSwingLookback);
      if(!newSwing) continue;

      double newPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, newShift) : iLow(_Symbol, PERIOD_CURRENT, newShift);

      for(int oldShift = newShift + InpSwingLookback; oldShift <= maxShift; oldShift++)
      {
         bool oldSwing = forBuy ? IsSwingHigh(oldShift, InpSwingLookback) : IsSwingLow(oldShift, InpSwingLookback);
         if(!oldSwing) continue;

         double oldPrice = forBuy ? iHigh(_Symbol, PERIOD_CURRENT, oldShift) : iLow(_Symbol, PERIOD_CURRENT, oldShift);
         if(forBuy && newPrice >= oldPrice) continue;
         if(!forBuy && newPrice <= oldPrice) continue;

         int touches = CountTrendlineTouches(forBuy, oldShift, oldPrice, newShift, newPrice, atr);
         if(touches < InpMinTrendlineTouches) continue;

         double lineAtSignal = LineValueAtShift(oldShift, oldPrice, newShift, newPrice, 1);
         double close = iClose(_Symbol, PERIOD_CURRENT, 1);
         double distance = forBuy ? close - lineAtSignal : lineAtSignal - close;
         double distanceATR = distance / atr;
         if(distanceATR < InpMinBreakoutDistanceATR) continue;

         bool better = (!info.valid ||
                        touches > info.touches ||
                        (touches == info.touches && newShift < info.anchorShiftNew));
         if(better)
         {
            info.valid = true;
            info.touches = touches;
            info.anchorShiftOld = oldShift;
            info.anchorShiftNew = newShift;
            info.anchorPriceOld = oldPrice;
            info.anchorPriceNew = newPrice;
            info.lineAtSignal = lineAtSignal;
            info.breakoutDistance = distance;
            info.breakoutDistanceATR = distanceATR;
         }
      }
   }

   return info.valid;
}

double CalculateBreakoutScore(bool forBuy, double atr, STrendlineInfo &info, bool dangerousCandle)
{
   double bodyRatio = GetBodyRatio(1);
   double bodyScore = (InpBodyRatio <= 0) ? 30.0 : ClampDouble(bodyRatio / InpBodyRatio, 0.0, 1.0) * 30.0;

   double shadow = forBuy ? GetUpperShadowRatio(1) : GetLowerShadowRatio(1);
   double shadowScore = 0.0;
   if(InpMaxOppositeShadow <= 0)
      shadowScore = (shadow <= 0) ? 25.0 : 0.0;
   else if(shadow <= InpMaxOppositeShadow)
      shadowScore = 25.0;
   else
      shadowScore = ClampDouble(1.0 - ((shadow - InpMaxOppositeShadow) / InpMaxOppositeShadow), 0.0, 1.0) * 25.0;

   double distanceTarget = InpMinBreakoutDistanceATR * 2.0;
   double distanceScore = (distanceTarget <= 0) ? 25.0 : ClampDouble(info.breakoutDistanceATR / distanceTarget, 0.0, 1.0) * 25.0;

   double score = bodyScore + shadowScore + distanceScore;
   if(dangerousCandle) score -= 30.0;
   if(InpRequireFollowThrough)
   {
      bool followOk = forBuy ? IsHighestClose(1, InpFollowThroughBars) : IsLowestClose(1, InpFollowThroughBars);
      if(followOk) score += 20.0;
   }

   return ClampDouble(score, 0.0, 100.0);
}

bool PassStructureFilter(bool forBuy, double atr, bool dangerousCandle, STrendlineInfo &info)
{
   ResetTrendlineInfo(info);
   if(!InpUseStructureFilter)
   {
      info.valid = true;
      info.score = 100.0;
      return true;
   }

   bool found = FindValidatedTrendline(forBuy, atr, info);
   if(!found)
   {
      if(InpShowStructureDebug)
         Print("銆恦8.6銆戠粨鏋勮繃婊? ", forBuy ? "澶氬崟" : "绌哄崟", "锛屾湭鍙戠幇鍙敤瓒嬪娍绾?);

      if(!InpRejectNoStructure)
      {
         info.valid = false;
         info.score = 100.0;
         return true;
      }
      return false;
   }

   info.score = CalculateBreakoutScore(forBuy, atr, info, dangerousCandle);
   if(InpShowStructureDebug)
   {
      Print("銆恦8.6銆戠粨鏋勮繃婊? ", forBuy ? "澶氬崟" : "绌哄崟",
            " | touches:", info.touches,
            " | line:", DoubleToString(info.lineAtSignal, _Digits),
            " | distanceATR:", DoubleToString(info.breakoutDistanceATR, 2),
            " | score:", DoubleToString(info.score, 1));
   }

   return (info.score >= InpMinBreakoutScore);
}

//+------------------------------------------------------------------+
//| 返回结构质量（0~1）并保留 InpRejectNoStructure 的硬拒逻辑                |
//+------------------------------------------------------------------+
bool GetStructureQualityFactor(bool forBuy, double atr, bool dangerousCandle, STrendlineInfo &info, double &quality)
{
   quality = 1.0;
   if(!InpUseStructureFilter)
   {
      info.valid = true;
      info.score = 100.0;
      return true;
   }

   bool found = FindValidatedTrendline(forBuy, atr, info);
   if(!found)
   {
      if(InpShowStructureDebug)
      {
         Print("结构评分: ", (forBuy ? "BUY" : "SELL"), " 未识别到有效结构");
      }

      if(!InpRejectNoStructure)
      {
         quality = ClampDouble(InpNoStructurePenalty, 0.0, 1.0);
         info.valid = false;
         info.score = 0.0;
         return true;
      }

      return false;
   }

   info.score = CalculateBreakoutScore(forBuy, atr, info, dangerousCandle);
   if(InpShowStructureDebug)
   {
      Print("结构评分: ", (forBuy ? "BUY" : "SELL"),
            " | touches:", info.touches,
            " | line:", DoubleToString(info.lineAtSignal, _Digits),
            " | distanceATR:", DoubleToString(info.breakoutDistanceATR, 2),
            " | score:", DoubleToString(info.score, 1));
   }

   if(InpMinBreakoutScore <= 0)
      quality = 1.0;
   else
      quality = ClampDouble(info.score / InpMinBreakoutScore, ClampDouble(InpMinStructureQualityFloor, 0.0, 1.0), 1.0);

   return true;
}

double GetBodyRatio(int shift)
{
   double range = iHigh(_Symbol, PERIOD_CURRENT, shift) - iLow(_Symbol, PERIOD_CURRENT, shift);
   if(range <= 0) return 0;
   return GetCandleBody(shift) / range;
}

bool IsBullishCandle(int shift)
{
   return iClose(_Symbol, PERIOD_CURRENT, shift) > iOpen(_Symbol, PERIOD_CURRENT, shift);
}

bool IsBearishCandle(int shift)
{
   return iClose(_Symbol, PERIOD_CURRENT, shift) < iOpen(_Symbol, PERIOD_CURRENT, shift);
}

//+------------------------------------------------------------------+
//| 銆恦8.62銆戠偣宸鏌?                                                 |
//+------------------------------------------------------------------+
bool IsSpreadAcceptable()
{
   if(!InpUseSpreadFilter) return true;
   int maxSpread = InpMaxSpreadPoints;
   if(maxSpread <= 0) maxSpread = 50;
   long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   return (spread <= maxSpread);
}

//+------------------------------------------------------------------+
//| 銆恦8.62銆戠粡绾晢鏈€灏忔鎹熻窛绂伙紙points 鈫?price锛?                     |
//+------------------------------------------------------------------+
double GetMinStopDistancePrice()
{
   long stopsLevel  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   long freezeLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   long level = (long)MathMax((double)stopsLevel, (double)freezeLevel);
   if(level <= 0) return 0;
   return level * _Point;
}

//+------------------------------------------------------------------+
//| 銆恦8.62銆戝紑浠撳墠鏍￠獙/淇姝㈡崯璺濈                                   |
//+------------------------------------------------------------------+
bool NormalizeStopForOpen(ENUM_ORDER_TYPE type, double price, double &sl)
{
   double minDist = GetMinStopDistancePrice();
   if(minDist <= 0) return true;

   if(type == ORDER_TYPE_BUY)
   {
      if(price - sl >= minDist) return true;
      sl = NormalizeDouble(price - minDist, _Digits);
      if(sl <= 0 || sl >= price)
      {
         Print("銆愭鎹熸牎楠屻€戝鍗曟鎹熸棤娉曟弧瓒虫渶灏忚窛绂?| price:", price, " minDist:", minDist);
         return false;
      }
      Print("銆愭鎹熻皟鏁淬€戝鍗曟鎹熸墿灞曡嚦缁忕邯鍟嗘渶灏忚窛绂?| 鏂癝L:", sl);
      return true;
   }

   if(sl - price >= minDist) return true;
   sl = NormalizeDouble(price + minDist, _Digits);
   if(sl <= price)
   {
      Print("銆愭鎹熸牎楠屻€戠┖鍗曟鎹熸棤娉曟弧瓒虫渶灏忚窛绂?| price:", price, " minDist:", minDist);
      return false;
   }
   Print("銆愭鎹熻皟鏁淬€戠┖鍗曟鎹熸墿灞曡嚦缁忕邯鍟嗘渶灏忚窛绂?| 鏂癝L:", sl);
   return true;
}

//+------------------------------------------------------------------+
//| 銆恦8.62銆戜慨鏀规鎹熷墠鏍￠獙璺濈                                        |
//+------------------------------------------------------------------+
bool IsStopDistanceValidForModify(ENUM_POSITION_TYPE posType, double newSL)
{
   double minDist = GetMinStopDistancePrice();
   if(minDist <= 0) return true;

   if(posType == POSITION_TYPE_BUY)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      return (bid - newSL >= minDist);
   }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return (newSL - ask >= minDist);
}

//+------------------------------------------------------------------+
//| 鎵嬫暟璁＄畻                                                          |
//+------------------------------------------------------------------+
double CalculateLotSize(double slDist)
{
   if(slDist <= 0) return 0;
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk     = balance * InpRiskPercent / 100.0;
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0 || tickVal <= 0) return 0;
   double lot = risk / (slDist / tickSize * tickVal);
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / step) * step;
   return MathMax(minL, MathMin(maxL, lot));
}

//+------------------------------------------------------------------+
//| 寮€浠擄紙鎴愬姛鏃惰褰曞叆鍦篕绾夸緵鐐圭伀妫€娴嬶級                                |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE type, double price, double sl, double lot)
{
   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_DEAL; req.symbol = _Symbol; req.volume = lot;
   req.type = type; req.price = price; req.sl = sl; req.tp = 0;
   req.deviation = 20; req.magic = InpMagicNumber; req.comment = InpComment;
   req.type_filling = ORDER_FILLING_IOC;
   if(!OrderSend(req, res))
   {
      Print("寮€浠撳け璐?| 閿欒:", GetLastError(), " | retcode:", res.retcode,
            " | ", res.comment, " | 绫诲瀷:", EnumToString(type), " | 鎵嬫暟:", lot);
      return false;
   }
   if(res.retcode != TRADE_RETCODE_DONE && res.retcode != TRADE_RETCODE_PLACED)
   {
      Print("寮€浠撴湭纭 | retcode:", res.retcode, " | ", res.comment);
      return false;
   }

   g_entryBarTime  = iTime(_Symbol, PERIOD_CURRENT, 1);
   g_entryBodySize = GetCandleBody(1);
   Print("寮€浠撴垚鍔?| 绁ㄥ彿:", res.order, " | 浠锋牸:", res.price,
         " | 鍏ュ満瀹炰綋:", DoubleToString(g_entryBodySize, _Digits));
   return true;
}

//+------------------------------------------------------------------+
//| 骞充粨                                                              |
//+------------------------------------------------------------------+
void ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;

   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);

   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action    = TRADE_ACTION_DEAL;
   req.position  = ticket;
   req.symbol    = _Symbol;
   req.volume    = volume;
   req.deviation = 20;
   req.magic     = InpMagicNumber;
   req.comment   = InpComment;

   if(posType == POSITION_TYPE_BUY)
   {
      req.type  = ORDER_TYPE_SELL;
      req.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   }
   else
   {
      req.type  = ORDER_TYPE_BUY;
      req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   }

   if(!OrderSend(req, res))
      Print("骞充粨澶辫触 | 绁ㄥ彿:", ticket, " | 閿欒:", GetLastError());
   else
   {
      Print("骞充粨鎴愬姛 | 绁ㄥ彿:", ticket);
      g_entryBarTime  = 0;
      g_entryBodySize = 0;
   }
}

//+------------------------------------------------------------------+
//| 淇敼姝㈡崯                                                          |
//+------------------------------------------------------------------+
void ModifyStopLoss(ulong ticket, double newSL)
{
   if(!PositionSelectByTicket(ticket)) return;

   double curSL = PositionGetDouble(POSITION_SL);
   newSL = NormalizeDouble(newSL, _Digits);
   if(MathAbs(newSL - curSL) < _Point) return;

   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   if(!IsStopDistanceValidForModify(posType, newSL))
   {
      Print("銆愪慨鏀规鎹熻烦杩囥€戣窛绂讳笉瓒?stops/freeze level | 绁ㄥ彿:", ticket, " | 鏂癝L:", newSL);
      return;
   }

   MqlTradeRequest req = {}; MqlTradeResult res = {};
   req.action = TRADE_ACTION_SLTP; req.position = ticket; req.symbol = _Symbol;
   req.sl = newSL; req.tp = PositionGetDouble(POSITION_TP);
   if(!OrderSend(req, res))
   {
      Print("淇敼姝㈡崯澶辫触 | 绁ㄥ彿:", ticket, " | 閿欒:", GetLastError(),
            " | retcode:", res.retcode, " | ", res.comment);
      return;
   }
   if(res.retcode != TRADE_RETCODE_DONE)
      Print("淇敼姝㈡崯鏈敓鏁?| 绁ㄥ彿:", ticket, " | retcode:", res.retcode, " | ", res.comment);
}

//+------------------------------------------------------------------+
//| 缁熻鎸佷粨鏁伴噺                                                       |
//+------------------------------------------------------------------+
int CountPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      count++;
   }
   return count;
}
//+------------------------------------------------------------------+

