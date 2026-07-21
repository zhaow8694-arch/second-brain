//+------------------------------------------------------------------+
//|                                          ZWei_SniperEA_v1.0.mq5  |
//|            Z-Wei Sniper Trading System  5-Layer Quality Filter   |
//|                  基于 Z-Wei 交易体系 36 篇论文完整实现               |
//+------------------------------------------------------------------+
#property copyright "Z-Wei Trading System"
#property version   "1.00"
#property strict
#include <Trade/Trade.mqh>
CTrade trade;

//+------------------------------------------------------------------+
//| INPUTS  对应 SniperTrendEA v8.5                                  |
//+------------------------------------------------------------------+
input double   InpRiskPercent        = 0.5;     // 单笔风险%
input double   InpMaxOppositeShadow  = 0.20;    // 反向影线/总长上限
input double   InpMinBodyRatio       = 0.60;    // 最小实体占比
input double   InpMaxCandleATR       = 2.5;     // 危险K线ATR倍数
input int      InpATRPeriod          = 14;      // ATR周期
input int      InpMA200Period        = 200;     // MA200
input double   InpMA200BufferATR     = 0.0;     // MA200自适应缓冲(0=严格)
input int      InpADXPeriod          = 14;      // ADX周期
input double   InpADXThreshold       = 20.0;    // ADX阈值
input int      InpMACDFast           = 12;      // MACD快线
input int      InpMACDSlow           = 26;      // MACD慢线
input int      InpMACDSignal         = 9;       // MACD信号线
input bool     InpRequireFollowThrough = false; // 跟随确认(保守=true)
input int      InpFollowThroughBars  = 3;       // 跟随确认回溯
input int      InpMinTrendlineTouches = 3;      // 趋势线最少触碰
input double   InpATRStopMult        = 2.0;     // 止损ATR倍数
input double   InpATRTrailMult       = 1.5;     // 移动止损ATR倍数
input double   InpATRTPMult          = 3.0;     // 止盈ATR倍数
input bool     InpEnableLong         = true;    // 允许多单
input bool     InpEnableShort        = true;    // 允许空单
input int      InpMagicNumber        = 20260620; // 魔术号


//+------------------------------------------------------------------+
//| GLOBALS                                                          |
//+------------------------------------------------------------------+
int maHandle, adxHandle, atrHandle, macdHandle;
datetime lastBarTime;
double ma200Buffer;

// Evil MACD 预警状态
enum ENUM_MACD_WARNING { WARNING_NONE=0, WARNING_BOTTOM=1, WARNING_TOP=2 };
ENUM_MACD_WARNING macdWarning;
int warningBar;  // 预警出现时的K线位置

// 当前活跃的趋势线
struct TrendLine {
   double slope, intercept;
   int touchCount, startBar, endBar;
   bool isValid, isSupport; // support=上升趋势线, resistance=下降趋势线
};
TrendLine activeTL;

// 上次突破信息 (用于跟随确认和调试)
struct BreakoutInfo {
   double bodyRatio, oppositeWick, rangeATRRatio, breakoutDistance;
   bool isClean, isDanger;
};
BreakoutInfo lastBreakout;

//+------------------------------------------------------------------+
//| INIT                                                             |
//+------------------------------------------------------------------+
int OnInit() {
   maHandle  = iMA(_Symbol,PERIOD_D1,InpMA200Period,0,MODE_EMA,PRICE_CLOSE);
   adxHandle = iADX(_Symbol,_Period,InpADXPeriod);
   atrHandle = iATR(_Symbol,_Period,InpATRPeriod);
   macdHandle= iMACD(_Symbol,_Period,InpMACDFast,InpMACDSlow,InpMACDSignal,PRICE_CLOSE);
   if(maHandle<0||adxHandle<0||atrHandle<0||macdHandle<0) return INIT_FAILED;
   lastBarTime=0; macdWarning=WARNING_NONE; warningBar=-1;
   ZeroMemory(activeTL); ZeroMemory(lastBreakout);
   Print("[ZWei] EA initialized on ", _Symbol, " ", EnumToString(_Period));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int r) { IndicatorRelease(maHandle); IndicatorRelease(adxHandle); IndicatorRelease(atrHandle); IndicatorRelease(macdHandle); }

//+------------------------------------------------------------------+
//| UTILS                                                            |
//+------------------------------------------------------------------+
double GetBuf(int h,int b,int s) { double v[]; CopyBuffer(h,b,s,1,v); return ArraySize(v)>0?v[0]:0; }

double CandleRange(int s) { return iHigh(_Symbol,_Period,s) - iLow(_Symbol,_Period,s); }

double GetATR(int s) { return GetBuf(atrHandle,0,s); }

bool IsNewBar() {
   datetime t = iTime(_Symbol,_Period,0);
   if(t != lastBarTime) { lastBarTime=t; return true; }
   return false;
}

// 计算仓位 - 基于账户风险百分比
double CalcLot(double slPoints) {
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = bal * InpRiskPercent / 100.0;
   double tickVal = SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   double tickSz  = SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double valPerPt = tickVal / tickSz;
   if(valPerPt <= 0) return SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double lot = riskMoney / (slPoints * valPerPt);
   double minL=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxL=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   if(lot<minL) lot=minL; if(lot>maxL) lot=maxL;
   return NormalizeDouble(lot,2);
}


//+------------------------------------------------------------------+
//| 第1层: 方向正确 - MA200日线趋势 + ADX                              |
//| 论文: v8.4, "方向正确是入场的前提"                                  |
//+------------------------------------------------------------------+
bool Layer1_DirectionCheck(bool isLong) {
   // --- MA200 趋势过滤 ---
   double ma200 = GetBuf(maHandle,0,1);
   double atmTR = GetATR(1);
   ma200Buffer = atmTR * InpMA200BufferATR;  // 自适应缓冲
   double price = iClose(_Symbol,PERIOD_D1,1);

   if(isLong && price < ma200 - ma200Buffer) {
      Print("[ZWei] Layer1 FAIL Long: price=",price," < MA200=",ma200);
      return false;
   }
   if(!isLong && price > ma200 + ma200Buffer) {
      Print("[ZWei] Layer1 FAIL Short: price=",price," > MA200=",ma200);
      return false;
   }

   // --- ADX 趋势强度 ---
   double adx = GetBuf(adxHandle,0,1);
   if(adx < InpADXThreshold) {
      Print("[ZWei] Layer1 FAIL: ADX=",adx," < ",InpADXThreshold," (震荡市,不交易)");
      return false;  // 论文: "震荡市中趋势线方法会失效,保持空仓"
   }

   return true;
}

//+------------------------------------------------------------------+
//| 第2层: 结构成立 - Evil MACD预警 + 趋势线检测                         |
//| 论文: Evil MACD 4.0, 底部/顶部预警信号                              |
//+------------------------------------------------------------------+
bool DetectEvilMACDWarning() {
   // Evil MACD 底部预警: MACD柱连续下降后首次回升 (或柱线创低但价格未创新低=背离)
   // Evil MACD 顶部预警: MACD柱连续上升后首次下降
   // 简化实现: 检测MACD柱状图的局部极值转折

   double macdMain = GetBuf(macdHandle,0,2);
   double macdSig  = GetBuf(macdHandle,1,2);
   double hist2    = macdMain - macdSig;

   macdMain = GetBuf(macdHandle,0,1);
   macdSig  = GetBuf(macdHandle,1,1);
   double hist1    = macdMain - macdSig;

   // 底部预警: 柱状图由负转正 或 负值开始缩小
   if(hist2 < 0 && hist1 > hist2) {
      macdWarning = WARNING_BOTTOM;
      warningBar = 1;
      return true;
   }

   // 顶部预警: 柱状图由正转负 或 正值开始缩小
   if(hist2 > 0 && hist1 < hist2) {
      macdWarning = WARNING_TOP;
      warningBar = 1;
      return true;
   }

   // 检查背离 (简化: 价格新低但MACD柱未新低)
   double priceNow = iClose(_Symbol,_Period,1);
   double pricePrev= iClose(_Symbol,_Period,5);
   macdMain = GetBuf(macdHandle,0,5);
   macdSig  = GetBuf(macdHandle,1,5);
   double hist5 = macdMain - macdSig;

   if(priceNow < pricePrev && hist1 > hist5) {  // 价格新低, MACD抬高 = 底背离
      macdWarning = WARNING_BOTTOM; warningBar = 1; return true;
   }
   if(priceNow > pricePrev && hist1 < hist5) {  // 价格新高, MACD降低 = 顶背离
      macdWarning = WARNING_TOP; warningBar = 1; return true;
   }

   // 预警过期 (超过20根K线未触发)
   if(warningBar > 20) { macdWarning = WARNING_NONE; warningBar = -1; }
   return (macdWarning != WARNING_NONE);
}

// 检测趋势线: 寻找支撑/阻力线
// 论文: "趋势线至少3次触碰, 趋势线本质上是一种短期共识"
bool DetectTrendLine() {
   ZeroMemory(activeTL);
   activeTL.isValid = false;

   // 找近期 swing highs 和 swing lows (回溯30根K线)
   int lookback = 30;
   double swingsH[], swingsL[], prices[];
   int barIdxH[], barIdxL[];
   ArrayResize(swingsH, 0); ArrayResize(barIdxH, 0);
   ArrayResize(swingsL, 0); ArrayResize(barIdxL, 0);

   for(int i=2; i<lookback-2; i++) {
      double h = iHigh(_Symbol,_Period,i);
      double l = iLow(_Symbol,_Period,i);
      // 摆动高点
      if(h >= iHigh(_Symbol,_Period,i-1) && h >= iHigh(_Symbol,_Period,i+1) &&
         h >= iHigh(_Symbol,_Period,i-2) && h >= iHigh(_Symbol,_Period,i+2)) {
         int sz = ArraySize(swingsH); ArrayResize(swingsH,sz+1); ArrayResize(barIdxH,sz+1);
         swingsH[sz]=h; barIdxH[sz]=i;
      }
      // 摆动低点
      if(l <= iLow(_Symbol,_Period,i-1) && l <= iLow(_Symbol,_Period,i+1) &&
         l <= iLow(_Symbol,_Period,i-2) && l <= iLow(_Symbol,_Period,i+2)) {
         int sz = ArraySize(swingsL); ArrayResize(swingsL,sz+1); ArrayResize(barIdxL,sz+1);
         swingsL[sz]=l; barIdxL[sz]=i;
      }
   }

   // 对每对摇摆点检查是否能形成趋势线 (3次以上触碰)
   int bestTouches = 0; double bestSlope = 0, bestIntercept = 0;
   int bestStart = 0, bestEnd = 0; bool bestIsSupport = false;

   // 检查下降趋势线 (连接 swing highs)
   for(int a=0; a<ArraySize(swingsH); a++) {
      for(int b=a+1; b<ArraySize(swingsH); b++) {
         if(barIdxH[a] <= barIdxH[b]) continue;
         double slope = (swingsH[a] - swingsH[b]) / (barIdxH[a] - barIdxH[b]);
         double intercept = swingsH[a] - slope * barIdxH[a];
         // 下降趋势线: slope > 0 (bar序号越大=越早, 价格越低 [因为barIdxH[a]>barIdxH[b]])
         // 其实是 slope<0 (从左到右下降), 但因为bar索引倒序, slope>0表示正常下降
         int touches = 2; // a和b本身算2次
         for(int c=0; c<ArraySize(swingsH); c++) {
            if(c==a||c==b) continue;
            double linePrice = intercept + slope * barIdxH[c];
            if(MathAbs(swingsH[c] - linePrice) < GetATR(1) * 0.3) touches++;
         }
         if(touches >= InpMinTrendlineTouches && touches > bestTouches) {
            bestTouches=touches; bestSlope=slope; bestIntercept=intercept;
            bestStart=barIdxH[a]; bestEnd=barIdxH[b]; bestIsSupport=false;
         }
      }
   }

   // 检查上升趋势线 (连接 swing lows)
   for(int a=0; a<ArraySize(swingsL); a++) {
      for(int b=a+1; b<ArraySize(swingsL); b++) {
         if(barIdxL[a] <= barIdxL[b]) continue;
         double slope = (swingsL[a] - swingsL[b]) / (barIdxL[a] - barIdxL[b]);
         double intercept = swingsL[a] - slope * barIdxL[a];
         int touches = 2;
         for(int c=0; c<ArraySize(swingsL); c++) {
            if(c==a||c==b) continue;
            double linePrice = intercept + slope * barIdxL[c];
            if(MathAbs(swingsL[c] - linePrice) < GetATR(1) * 0.3) touches++;
         }
         if(touches >= InpMinTrendlineTouches && touches > bestTouches) {
            bestTouches=touches; bestSlope=slope; bestIntercept=intercept;
            bestStart=barIdxL[a]; bestEnd=barIdxL[b]; bestIsSupport=true;
         }
      }
   }

   if(bestTouches >= InpMinTrendlineTouches) {
      activeTL.slope=bestSlope; activeTL.intercept=bestIntercept;
      activeTL.touchCount=bestTouches; activeTL.startBar=bestStart;
      activeTL.endBar=bestEnd; activeTL.isValid=true;
      activeTL.isSupport=bestIsSupport;
      return true;
   }
   return false;
}

// 检测趋势线突破
// 论文: "突破不仅要看收盘价是否越过趋势线,还要突破幅度是否足够清晰"
bool CheckBreakout(bool isLong) {
   if(!activeTL.isValid) return false;

   double close1 = iClose(_Symbol,_Period,1);
   double close2 = iClose(_Symbol,_Period,2);
   double linePrice1 = activeTL.intercept + activeTL.slope * 1;  // bar=1 的趋势线价格
   double linePrice2 = activeTL.intercept + activeTL.slope * 2;

   // 突破方向必须和预警方向一致
   if(isLong && macdWarning != WARNING_BOTTOM) return false;
   if(!isLong && macdWarning != WARNING_TOP) return false;

   // 对于下降趋势线 (阻力线, isSupport=false): 做多需要向上突破
   // 对于上升趋势线 (支撑线, isSupport=true): 做空需要向下突破
   if(isLong && activeTL.isSupport) return false;    // 做多应该突破下降趋势线
   if(!isLong && !activeTL.isSupport) return false;  // 做空应该突破上升趋势线

   // 突破检查
   bool broken;
   if(isLong)
      broken = (close1 > linePrice1) && (close2 <= linePrice2); // 刚突破
   else
      broken = (close1 < linePrice1) && (close2 >= linePrice2);

   if(!broken) return false;

   // 突破幅度 (论文: 不能刚好贴着趋势线)
   double dist = MathAbs(close1 - linePrice1);
   lastBreakout.breakoutDistance = dist / (_Point * 10);  // 以10点为单位

   // 突破幅度太小 = 低质量
   if(dist < GetATR(1) * 0.1) {
      Print("[ZWei] Layer2 FAIL: Breakout too marginal, dist=",dist/_Point,"pts");
      return false;
   }

   Print("[ZWei] Layer2 PASS: Trendline broken. Touches=",activeTL.touchCount,
         " isSupport=",activeTL.isSupport," dist=",dist/_Point,"pts");
   return true;
}

//+------------------------------------------------------------------+
//| 第3层: K线干脆 - 反向影线/总长 <= 20%                              |
//| 论文: v8.5 第3层, 市场结构观察 #26-2-2                             |
//| "做多最忌讳上影线(卖压在最后压制),做空最忌讳下影线(买盘在最后承接)"    |
//| 关键纠正: 分母是K线总长(range),不是实体!                            |
//+------------------------------------------------------------------+
bool Layer3_CandleCleanCheck(bool isLong) {
   double open  = iOpen(_Symbol,_Period,1);
   double close = iClose(_Symbol,_Period,1);
   double high  = iHigh(_Symbol,_Period,1);
   double low   = iLow(_Symbol,_Period,1);
   double range = high - low;
   if(range <= 0) return false;

   double body = MathAbs(close - open);
   double bodyRatio = body / range;           // 实体/总长
   double upperWick = high - MathMax(open,close);
   double lowerWick = MathMin(open,close) - low;
   double upperRatio = upperWick / range;     // 上影/总长 (论文标准)
   double lowerRatio = lowerWick / range;     // 下影/总长 (论文标准)

   lastBreakout.bodyRatio = bodyRatio;

   // 实体占比检查 (论文: 60%)
   if(bodyRatio < InpMinBodyRatio) {
      Print("[ZWei] Layer3 FAIL: BodyRatio=",DoubleToString(bodyRatio*100,0),"% < ",InpMinBodyRatio*100,"%");
      lastBreakout.isClean = false; return false;
   }

   // 方向性影线惩罚
   if(isLong) {
      lastBreakout.oppositeWick = upperRatio;
      if(upperRatio > InpMaxOppositeShadow) {
         Print("[ZWei] Layer3 FAIL Long: UpperWick/Range=",DoubleToString(upperRatio*100,0),"%");
         lastBreakout.isClean = false; return false;
      }
   } else {
      lastBreakout.oppositeWick = lowerRatio;
      if(lowerRatio > InpMaxOppositeShadow) {
         Print("[ZWei] Layer3 FAIL Short: LowerWick/Range=",DoubleToString(lowerRatio*100,0),"%");
         lastBreakout.isClean = false; return false;
      }
   }

   // 十字星检查 (论文: 多空分歧)
   if(bodyRatio < 0.30 && upperRatio > 0.20 && lowerRatio > 0.20) {
      Print("[ZWei] Layer3 FAIL: Doji detected");
      lastBreakout.isClean = false; return false;
   }

   lastBreakout.isClean = true;
   return true;
}


//+------------------------------------------------------------------+
//| 第4层: 不追耗竭 - 危险K线过滤 (论文: The Dangerous Candle)          |
//| "强劲动能 != 可持续动能, 振幅>ATR*2.5倍是订单失衡(FVG)耗竭点"        |
//+------------------------------------------------------------------+
bool Layer4_DangerCheck() {
   double atr   = GetATR(1);
   double range = CandleRange(1);
   double ratio = range / MathMax(atr, _Point);

   lastBreakout.rangeATRRatio = ratio;

   // 论文核心逻辑: IsDangerousCandle: range > atr * InpMaxCandleATR
   if(range > atr * InpMaxCandleATR) {
      Print("[ZWei] Layer4 FAIL: Dangerous candle. Range/ATR=",DoubleToString(ratio,1));
      lastBreakout.isDanger = true; return false;
   }

   // 补充: 振幅突然增大 (论文: "实体增大过于突兀,持续性未知")
   double avgRange = 0;
   for(int i=2; i<=6; i++) avgRange += CandleRange(i);
   avgRange /= 5.0;
   if(avgRange > 0 && range > avgRange * 2.5) {
      Print("[ZWei] Layer4 FAIL: Sudden expansion vs 5-bar avg");
      lastBreakout.isDanger = true; return false;
   }

   lastBreakout.isDanger = false;
   return true;
}

//+------------------------------------------------------------------+
//| 第5层: 共识形成 - 点火与跟随 (论文: Ignition and Follow-Through)     |
//| "真正的趋势启动需要共识形成, 突破K线收盘价创近N根K线极值"            |
//+------------------------------------------------------------------+
bool Layer5_FollowThrough(bool isLong) {
   if(!InpRequireFollowThrough) return true;  // 保守参数, 关闭则跳过

   double close = iClose(_Symbol,_Period,1);

   double extreme;
   if(isLong) {
      // 做多: 收盘价必须创近N根K线最高
      extreme = -DBL_MAX;
      for(int i=2; i<=2+InpFollowThroughBars; i++)
         if(iHigh(_Symbol,_Period,i) > extreme) extreme = iHigh(_Symbol,_Period,i);
      if(close <= extreme) {
         Print("[ZWei] Layer5 FAIL Long: close=",close," <= extreme=",extreme);
         return false;
      }
   } else {
      // 做空: 收盘价必须创近N根K线最低
      extreme = DBL_MAX;
      for(int i=2; i<=2+InpFollowThroughBars; i++)
         if(iLow(_Symbol,_Period,i) < extreme) extreme = iLow(_Symbol,_Period,i);
      if(close >= extreme) {
         Print("[ZWei] Layer5 FAIL Short: close=",close," >= extreme=",extreme);
         return false;
      }
   }

   Print("[ZWei] Layer5 PASS: Follow-through confirmed");
   return true;
}


//+------------------------------------------------------------------+
//| 入场信号 - 5层串联过滤                                             |
//| 论文: v8.5 "5层质量过滤全部通过才会入场"                            |
//+------------------------------------------------------------------+
// 论文哲学: "我宁愿放过100个机会,也不在低质量的环境中浪费一颗子弹"
// 任何一层不通过, 立即返回false, 不做交易

bool LongSignal() {
   if(!InpEnableLong) return false;

   Print("[ZWei] === Checking Long Signal ===");

   // Layer 1: 方向正确
   if(!Layer1_DirectionCheck(true)) return false;

   // Layer 2: 结构成立 - Evil MACD预警 + 趋势线突破
   if(!DetectEvilMACDWarning()) { Print("[ZWei] Layer2: No MACD warning"); return false; }
   if(macdWarning != WARNING_BOTTOM) { Print("[ZWei] Layer2: Not a bottom warning"); return false; }
   if(!DetectTrendLine()) { Print("[ZWei] Layer2: No valid trendline"); return false; }
   if(!CheckBreakout(true)) { Print("[ZWei] Layer2: No breakout"); return false; }

   // Layer 3: K线干脆
   if(!Layer3_CandleCleanCheck(true)) return false;

   // Layer 4: 不追耗竭
   if(!Layer4_DangerCheck()) return false;

   // Layer 5: 共识形成
   if(!Layer5_FollowThrough(true)) return false;

   Print("[ZWei] >>> LONG SIGNAL CONFIRMED <<<");
   return true;
}

bool ShortSignal() {
   if(!InpEnableShort) return false;

   Print("[ZWei] === Checking Short Signal ===");

   if(!Layer1_DirectionCheck(false)) return false;
   if(!DetectEvilMACDWarning()) { Print("[ZWei] Layer2: No MACD warning"); return false; }
   if(macdWarning != WARNING_TOP) { Print("[ZWei] Layer2: Not a top warning"); return false; }
   if(!DetectTrendLine()) { Print("[ZWei] Layer2: No valid trendline"); return false; }
   if(!CheckBreakout(false)) { Print("[ZWei] Layer2: No breakout"); return false; }
   if(!Layer3_CandleCleanCheck(false)) return false;
   if(!Layer4_DangerCheck()) return false;
   if(!Layer5_FollowThrough(false)) return false;

   Print("[ZWei] >>> SHORT SIGNAL CONFIRMED <<<");
   return true;
}

//+------------------------------------------------------------------+
//| 交易执行                                                           |
//+------------------------------------------------------------------+
void ExecuteTrade(bool isLong) {
   double atr = GetATR(1);
   double slPts = atr * InpATRStopMult / _Point;
   double tpPts = atr * InpATRTPMult / _Point;
   double lot = CalcLot(slPts);

   double price, sl, tp;
   if(isLong) {
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      sl = price - atr * InpATRStopMult;
      tp = price + atr * InpATRTPMult;
   } else {
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      sl = price + atr * InpATRStopMult;
      tp = price - atr * InpATRTPMult;
   }

   trade.SetExpertMagicNumber(InpMagicNumber);
   bool ok;
   if(isLong) ok = trade.Buy(lot, _Symbol, price, sl, tp, "ZWei Long");
   else       ok = trade.Sell(lot, _Symbol, price, sl, tp, "ZWei Short");

   if(ok) {
      Print("[ZWei] TRADE OPENED: ", isLong?"LONG":"SHORT",
            " Lot=",lot," Price=",price," SL=",sl," TP=",tp);
      // 入场后重置预警, 防止重复入场
      macdWarning = WARNING_NONE; warningBar = -1;
   } else {
      Print("[ZWei] TRADE FAILED: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| 移动止损 - 论文: "推止损不是为了多赚,而是为了活下来"                |
//+------------------------------------------------------------------+
void ManageTrailing() {
   for(int i=PositionsTotal()-1; i>=0; i--) {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;

      double atr = GetATR(1);
      double trail = atr * InpATRTrailMult;
      double currentSl = PositionGetDouble(POSITION_SL);
      bool isLong = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;
      double price = isLong ? SymbolInfoDouble(_Symbol,SYMBOL_BID)
                            : SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double newSl;

      if(isLong) {
         newSl = price - trail;
         // 只向有利方向移动 (论文: "保护已有浮盈")
         if(newSl > currentSl && newSl > PositionGetDouble(POSITION_PRICE_OPEN) * 0.995)
            trade.PositionModify(ticket, newSl, 0);
      } else {
         newSl = price + trail;
         if((currentSl == 0 || newSl < currentSl) && newSl < PositionGetDouble(POSITION_PRICE_OPEN) * 1.005)
            trade.PositionModify(ticket, newSl, 0);
      }
   }
}

//+------------------------------------------------------------------+
//| 主循环                                                             |
//+------------------------------------------------------------------+
void OnTick() {
   if(!IsNewBar()) return;   // 每根新K线判断一次

   // 先管理现有持仓的移动止损
   if(PositionsTotal() > 0)
      ManageTrailing();

   // 论文: "我们宁愿空仓, 也不在低质量机会中浪费子弹"
   // 单品种只持一单
   bool hasPos = false;
   for(int i=0; i<PositionsTotal(); i++) {
      ulong t = PositionGetTicket(i);
      if(PositionSelectByTicket(t) && PositionGetInteger(POSITION_MAGIC)==InpMagicNumber
         && PositionGetString(POSITION_SYMBOL)==_Symbol) { hasPos=true; break; }
   }
   if(hasPos) return;

   // 检查入场信号
   if(LongSignal())  ExecuteTrade(true);
   else if(ShortSignal()) ExecuteTrade(false);

   // 论文: 交易哲学 - "当市场无法用规律解释时,空仓"
   // 没有任何信号 = 空仓, 是正确的决策
}
//+------------------------------------------------------------------+
//|  End of ZWei_SniperEA_v1.0.mq5                                   |
//+------------------------------------------------------------------+
