//+------------------------------------------------------------------+
//|                  Vegas_Trend_Master_H4_Multi_V4.1_Optimized.mq5  |
//|                  Vegas 多品种趋势系统 V4.1 风控修复优化版          |
//+------------------------------------------------------------------+
#property copyright "编码助手"
#property version   "4.10"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade        trade;
CPositionInfo posInfo;

//+------------------------------------------------------------------+
//| 输入参数                                                          |
//+------------------------------------------------------------------+
input string   InpSymbols                  = "XAUUSD,EURUSD,SP500,CHINA50"; // 交易品种，必须与券商品种名完全一致
input double   InpRiskPercent              = 0.50;      // 单笔理论风险比例，按真实SL计算 (%)
input int      InpMagicNumber              = 888888;    // EA魔术码
input bool     InpUseBreakEven             = true;      // 部分平仓后是否尝试移动服务器SL到保本
input int      InpBreakEvenBufferPoints    = 0;         // 保本SL额外锁利点数，0=开仓价
input int      InpSLBufferPoints           = 50;        // 初始SL相对EMA338缓冲点数
input int      InpSlippagePoints           = 30;        // 最大允许滑点/偏差点数
input int      InpMaxSpreadPoints          = 300;       // 最大允许点差，<=0 表示不限制
input int      InpMaxSimultaneousPositions = 4;         // 本EA最大同时持仓数，<=0 表示不限制
input int      InpTimerSeconds             = 60;        // 多品种轮询秒数
input bool     InpEnableNotifications      = true;      // 是否发送手机推送
input int      InpReportHourBeijing        = 11;        // 每日报告北京时间小时

//--- 固化参数
const double   OPTIMIZED_PARTIAL_CLOSE = 0.50; // 部分平仓比例 50%
const int      OPTIMIZED_ADX_PERIOD    = 14;   // ADX周期
const double   OPTIMIZED_ADX_THRESHOLD = 22.0; // ADX趋势阈值

//--- 均线参数
input int      InpEma12  = 12;
input int      InpEma144 = 144;
input int      InpEma169 = 169;
input int      InpEma288 = 288;
input int      InpEma338 = 338;
input int      InpEma576 = 576;
input int      InpEma676 = 676;

//+------------------------------------------------------------------+
//| 结构体与全局变量                                                  |
//+------------------------------------------------------------------+
struct SymbolData
  {
   string   symbolName;
   int      h_ema12;
   int      h_ema144;
   int      h_ema169;
   int      h_ema288;
   int      h_ema338;
   int      h_ema576;
   int      h_ema676;
   int      h_adx;
   datetime lastBarTime;
   bool     isValid;
  };

SymbolData symbols[];
int        lastReportDate = -1; // YYYYMMDD，修复跨月不发送问题

//+------------------------------------------------------------------+
//| 工具函数                                                          |
//+------------------------------------------------------------------+
bool IsSpaceChar(ushort ch)
  {
   return(ch == 32 || ch == 9 || ch == 10 || ch == 13);
  }

string TrimString(string s)
  {
   while(StringLen(s) > 0 && IsSpaceChar(StringGetCharacter(s, 0)))
      s = StringSubstr(s, 1);

   while(StringLen(s) > 0)
     {
      int last = StringLen(s) - 1;
      if(IsSpaceChar(StringGetCharacter(s, last)))
         s = StringSubstr(s, 0, last);
      else
         break;
     }

   return s;
  }

datetime GetBeijingTime()
  {
   return(TimeGMT() + 8 * 3600);
  }

int GetDateKey(datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   return(dt.year * 10000 + dt.mon * 100 + dt.day);
  }

double NormalizePrice(string sym, double price)
  {
   int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   return NormalizeDouble(price, digits);
  }

void ReleaseHandle(int &handle)
  {
   if(handle != INVALID_HANDLE)
     {
      IndicatorRelease(handle);
      handle = INVALID_HANDLE;
     }
  }

//+------------------------------------------------------------------+
//| 初始化单个品种                                                    |
//+------------------------------------------------------------------+
bool InitSymbolData(int index, string sym)
  {
   symbols[index].symbolName  = sym;
   symbols[index].h_ema12     = INVALID_HANDLE;
   symbols[index].h_ema144    = INVALID_HANDLE;
   symbols[index].h_ema169    = INVALID_HANDLE;
   symbols[index].h_ema288    = INVALID_HANDLE;
   symbols[index].h_ema338    = INVALID_HANDLE;
   symbols[index].h_ema576    = INVALID_HANDLE;
   symbols[index].h_ema676    = INVALID_HANDLE;
   symbols[index].h_adx       = INVALID_HANDLE;
   symbols[index].lastBarTime = 0;
   symbols[index].isValid     = false;

   if(sym == "")
     {
      Print("⚠️ 跳过空品种名");
      return false;
     }

   if(!SymbolSelect(sym, true))
     {
      Print("❌ 品种无法加入市场报价：", sym, "。请检查券商品种名称是否完全一致。");
      return false;
     }

   symbols[index].h_ema12  = iMA(sym, PERIOD_H4, InpEma12,  0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema144 = iMA(sym, PERIOD_H4, InpEma144, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema169 = iMA(sym, PERIOD_H4, InpEma169, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema288 = iMA(sym, PERIOD_H4, InpEma288, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema338 = iMA(sym, PERIOD_H4, InpEma338, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema576 = iMA(sym, PERIOD_H4, InpEma576, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_ema676 = iMA(sym, PERIOD_H4, InpEma676, 0, MODE_EMA, PRICE_CLOSE);
   symbols[index].h_adx    = iADX(sym, PERIOD_H4, OPTIMIZED_ADX_PERIOD);

   if(symbols[index].h_ema12  == INVALID_HANDLE ||
      symbols[index].h_ema144 == INVALID_HANDLE ||
      symbols[index].h_ema169 == INVALID_HANDLE ||
      symbols[index].h_ema288 == INVALID_HANDLE ||
      symbols[index].h_ema338 == INVALID_HANDLE ||
      symbols[index].h_ema576 == INVALID_HANDLE ||
      symbols[index].h_ema676 == INVALID_HANDLE ||
      symbols[index].h_adx    == INVALID_HANDLE)
     {
      Print("❌ 指标句柄创建失败：", sym, "，错误码=", GetLastError());
      return false;
     }

   symbols[index].isValid = true;
   Print("✅ 品种初始化成功：", sym);
   return true;
  }

//+------------------------------------------------------------------+
//| EA初始化                                                          |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePoints);
   trade.SetAsyncMode(false);

   ushort separator = StringGetCharacter(",", 0);
   string result[];
   int count = StringSplit(InpSymbols, separator, result);

   if(count <= 0)
     {
      Print("❌ InpSymbols为空，EA初始化失败。");
      return INIT_FAILED;
     }

   ArrayResize(symbols, count);

   int validCount = 0;
   for(int i = 0; i < count; i++)
     {
      string sym = TrimString(result[i]);
      if(InitSymbolData(i, sym))
         validCount++;
     }

   if(validCount <= 0)
     {
      Print("❌ 没有任何有效品种，EA初始化失败。");
      return INIT_FAILED;
     }

   int timerSeconds = InpTimerSeconds;
   if(timerSeconds < 1)
      timerSeconds = 60;
   EventSetTimer(timerSeconds);

   Print("🚀 Vegas V4.1 风控修复优化版启动。有效品种数量：", validCount);
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| EA卸载                                                            |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();

   for(int i = 0; i < ArraySize(symbols); i++)
     {
      ReleaseHandle(symbols[i].h_ema12);
      ReleaseHandle(symbols[i].h_ema144);
      ReleaseHandle(symbols[i].h_ema169);
      ReleaseHandle(symbols[i].h_ema288);
      ReleaseHandle(symbols[i].h_ema338);
      ReleaseHandle(symbols[i].h_ema576);
      ReleaseHandle(symbols[i].h_ema676);
      ReleaseHandle(symbols[i].h_adx);
     }

   Print("🛑 Vegas V4.1 已卸载，原因代码：", reason);
  }

//+------------------------------------------------------------------+
//| Tick与Timer                                                       |
//+------------------------------------------------------------------+
void OnTick()
  {
   ProcessAllSymbols();
  }

void OnTimer()
  {
   ProcessAllSymbols();
  }

void ProcessAllSymbols()
  {
   for(int i = 0; i < ArraySize(symbols); i++)
      ProcessSymbol(i);

   CheckAndSendDailyReport();
  }

//+------------------------------------------------------------------+
//| 当前交易环境检查                                                  |
//+------------------------------------------------------------------+
bool IsTradingEnvironmentReady(string sym, ENUM_ORDER_TYPE orderType)
  {
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
     {
      Print("⚠️ 终端自动交易未允许。");
      return false;
     }

   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
     {
      Print("⚠️ EA自动交易未允许。");
      return false;
     }

   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      Print("⚠️ 当前账户不允许交易。");
      return false;
     }

   long tradeMode = SymbolInfoInteger(sym, SYMBOL_TRADE_MODE);
   if(tradeMode == SYMBOL_TRADE_MODE_DISABLED || tradeMode == SYMBOL_TRADE_MODE_CLOSEONLY)
     {
      Print("⚠️ 品种当前不可开仓：", sym);
      return false;
     }

   if(orderType == ORDER_TYPE_BUY && tradeMode == SYMBOL_TRADE_MODE_SHORTONLY)
     {
      Print("⚠️ 品种只允许做空，跳过做多：", sym);
      return false;
     }

   if(orderType == ORDER_TYPE_SELL && tradeMode == SYMBOL_TRADE_MODE_LONGONLY)
     {
      Print("⚠️ 品种只允许做多，跳过做空：", sym);
      return false;
     }

   return true;
  }

double GetSpreadPoints(string sym)
  {
   MqlTick tick;
   if(!SymbolInfoTick(sym, tick))
      return -1.0;

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(point <= 0.0 || tick.ask <= 0.0 || tick.bid <= 0.0)
      return -1.0;

   return((tick.ask - tick.bid) / point);
  }

bool IsSpreadAcceptable(string sym)
  {
   if(InpMaxSpreadPoints <= 0)
      return true;

   double spreadPoints = GetSpreadPoints(sym);
   if(spreadPoints < 0.0)
     {
      Print("⚠️ 无法获取点差，跳过开仓：", sym);
      return false;
     }

   if(spreadPoints > InpMaxSpreadPoints)
     {
      Print("⚠️ 点差过大，跳过开仓：", sym,
            "，当前点差=", DoubleToString(spreadPoints, 1),
            "，限制=", InpMaxSpreadPoints);
      return false;
     }

   return true;
  }

int CountEAOpenPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i))
        {
         if((int)posInfo.Magic() == InpMagicNumber)
            count++;
        }
     }
   return count;
  }

bool CanOpenMorePositions()
  {
   if(InpMaxSimultaneousPositions <= 0)
      return true;

   int current = CountEAOpenPositions();
   if(current >= InpMaxSimultaneousPositions)
     {
      Print("⚠️ 本EA当前持仓数已达上限，跳过新开仓。当前=", current,
            "，上限=", InpMaxSimultaneousPositions);
      return false;
     }

   return true;
  }

//+------------------------------------------------------------------+
//| 获取本EA某品种的首个持仓                                          |
//+------------------------------------------------------------------+
bool GetFirstEAPosition(string sym,
                        ulong &ticket,
                        ulong &identifier,
                        ENUM_POSITION_TYPE &type,
                        double &volume,
                        double &openPrice,
                        double &sl,
                        double &tp)
  {
   ticket     = 0;
   identifier = 0;
   volume     = 0.0;
   openPrice  = 0.0;
   sl         = 0.0;
   tp         = 0.0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i))
        {
         if(posInfo.Symbol() == sym && (int)posInfo.Magic() == InpMagicNumber)
           {
            ticket     = posInfo.Ticket();
            identifier = (ulong)posInfo.Identifier();
            type       = posInfo.PositionType();
            volume     = posInfo.Volume();
            openPrice  = posInfo.PriceOpen();
            sl         = posInfo.StopLoss();
            tp         = posInfo.TakeProfit();
            return true;
           }
        }
     }

   return false;
  }

//+------------------------------------------------------------------+
//| 核心逻辑：处理单个品种                                            |
//+------------------------------------------------------------------+
void ProcessSymbol(int index)
  {
   if(index < 0 || index >= ArraySize(symbols))
      return;

   if(!symbols[index].isValid)
      return;

   string sym = symbols[index].symbolName;

   datetime currentBarTime = iTime(sym, PERIOD_H4, 0);
   if(currentBarTime == 0)
      return;

   if(currentBarTime == symbols[index].lastBarTime)
      return;

   double ema12[], ema144[], ema169[], ema288[], ema338[], ema576[], ema676[], adx[];
   ArraySetAsSeries(ema12,  true);
   ArraySetAsSeries(ema144, true);
   ArraySetAsSeries(ema169, true);
   ArraySetAsSeries(ema288, true);
   ArraySetAsSeries(ema338, true);
   ArraySetAsSeries(ema576, true);
   ArraySetAsSeries(ema676, true);
   ArraySetAsSeries(adx,    true);

   if(CopyBuffer(symbols[index].h_ema12,  0, 0, 3, ema12)  < 3) return;
   if(CopyBuffer(symbols[index].h_ema144, 0, 0, 3, ema144) < 3) return;
   if(CopyBuffer(symbols[index].h_ema169, 0, 0, 3, ema169) < 3) return;
   if(CopyBuffer(symbols[index].h_ema288, 0, 0, 3, ema288) < 3) return;
   if(CopyBuffer(symbols[index].h_ema338, 0, 0, 3, ema338) < 3) return;
   if(CopyBuffer(symbols[index].h_ema576, 0, 0, 3, ema576) < 3) return;
   if(CopyBuffer(symbols[index].h_ema676, 0, 0, 3, ema676) < 3) return;
   if(CopyBuffer(symbols[index].h_adx,    0, 0, 3, adx)    < 3) return;

   double closePrice1 = iClose(sym, PERIOD_H4, 1);
   if(closePrice1 <= 0.0)
      return;

   ulong posTicket = 0;
   ulong posIdentifier = 0;
   ENUM_POSITION_TYPE posType = POSITION_TYPE_BUY;
   double currentVolume = 0.0;
   double openPrice = 0.0;
   double currentSL = 0.0;
   double currentTP = 0.0;

   if(GetFirstEAPosition(sym, posTicket, posIdentifier, posType, currentVolume, openPrice, currentSL, currentTP))
     {
      ManageExistingPosition(sym, posTicket, posIdentifier, posType,
                             currentVolume, openPrice, currentSL, currentTP,
                             closePrice1, ema288[1], ema338[1]);

      symbols[index].lastBarTime = currentBarTime;
      return;
     }

   //--- 没有持仓才寻找新信号
   bool isTrending = (adx[1] > OPTIMIZED_ADX_THRESHOLD);

   bool bullAlignment = (ema144[1] > ema169[1]) && (ema576[1] > ema676[1]);
   bool bullSlope     = (ema169[1] > ema169[2]) && (ema676[1] > ema676[2]); // 使用已收盘K线，避免当前K线漂移
   bool bullCross     = (ema12[1] > ema144[1] && ema12[1] > ema169[1]) &&
                        (ema12[2] <= ema144[2] || ema12[2] <= ema169[2]);

   bool bearAlignment = (ema144[1] < ema169[1]) && (ema576[1] < ema676[1]);
   bool bearSlope     = (ema169[1] < ema169[2]) && (ema676[1] < ema676[2]); // 使用已收盘K线，避免当前K线漂移
   bool bearCross     = (ema12[1] < ema144[1] && ema12[1] < ema169[1]) &&
                        (ema12[2] >= ema144[2] || ema12[2] >= ema169[2]);

   if(isTrending && bullAlignment && bullSlope && bullCross)
     {
      double desiredSL = ema338[1] - InpSLBufferPoints * SymbolInfoDouble(sym, SYMBOL_POINT);
      OpenPosition(sym, ORDER_TYPE_BUY, desiredSL, "Vegas Bull V4.1");
     }
   else if(isTrending && bearAlignment && bearSlope && bearCross)
     {
      double desiredSL = ema338[1] + InpSLBufferPoints * SymbolInfoDouble(sym, SYMBOL_POINT);
      OpenPosition(sym, ORDER_TYPE_SELL, desiredSL, "Vegas Bear V4.1");
     }

   symbols[index].lastBarTime = currentBarTime;
  }

//+------------------------------------------------------------------+
//| 持仓管理                                                          |
//+------------------------------------------------------------------+
void ManageExistingPosition(string sym,
                            ulong ticket,
                            ulong identifier,
                            ENUM_POSITION_TYPE type,
                            double volume,
                            double openPrice,
                            double currentSL,
                            double currentTP,
                            double closePrice1,
                            double ema288Value,
                            double ema338Value)
  {
   bool isPartiallyClosed = HasPartiallyClosed(identifier);

   if(type == POSITION_TYPE_BUY)
     {
      if(closePrice1 < ema338Value)
        {
         ClosePositionByTicket(ticket, sym, "📉 多头全部清仓：跌破防守底线 EMA338");
         return;
        }

      if(InpUseBreakEven && isPartiallyClosed && closePrice1 < openPrice)
        {
         ClosePositionByTicket(ticket, sym, "🛡️ 多头触发保本止损：剩余仓位安全出局");
         return;
        }

      if(!isPartiallyClosed && closePrice1 < ema288Value)
        {
         double closeVol = NormalizeCloseVolume(sym, volume * OPTIMIZED_PARTIAL_CLOSE, volume);
         if(closeVol > 0.0)
           {
            if(PartialClosePosition(ticket, sym, closeVol, "💰 多头获利减仓 50%：跌破第一平仓线 EMA288"))
               EnsureBreakEvenStop(sym, ticket, type, openPrice, currentSL, currentTP);
           }
         else
           {
            Print("ℹ️ [", sym, "] 当前手数过小，无法安全部分平仓，保持原仓位。");
           }
         return;
        }

      if(InpUseBreakEven && isPartiallyClosed)
         EnsureBreakEvenStop(sym, ticket, type, openPrice, currentSL, currentTP);
     }
   else if(type == POSITION_TYPE_SELL)
     {
      if(closePrice1 > ema338Value)
        {
         ClosePositionByTicket(ticket, sym, "📈 空头全部清仓：突破防守底线 EMA338");
         return;
        }

      if(InpUseBreakEven && isPartiallyClosed && closePrice1 > openPrice)
        {
         ClosePositionByTicket(ticket, sym, "🛡️ 空头触发保本止损：剩余仓位安全出局");
         return;
        }

      if(!isPartiallyClosed && closePrice1 > ema288Value)
        {
         double closeVol = NormalizeCloseVolume(sym, volume * OPTIMIZED_PARTIAL_CLOSE, volume);
         if(closeVol > 0.0)
           {
            if(PartialClosePosition(ticket, sym, closeVol, "💰 空头获利减仓 50%：突破第一平仓线 EMA288"))
               EnsureBreakEvenStop(sym, ticket, type, openPrice, currentSL, currentTP);
           }
         else
           {
            Print("ℹ️ [", sym, "] 当前手数过小，无法安全部分平仓，保持原仓位。");
           }
         return;
        }

      if(InpUseBreakEven && isPartiallyClosed)
         EnsureBreakEvenStop(sym, ticket, type, openPrice, currentSL, currentTP);
     }
  }

//+------------------------------------------------------------------+
//| 开仓：真实SL + 风险手数 + 返回码检查                              |
//+------------------------------------------------------------------+
bool OpenPosition(string sym, ENUM_ORDER_TYPE orderType, double desiredSL, string comment)
  {
   if(!CanOpenMorePositions())
      return false;

   if(!IsTradingEnvironmentReady(sym, orderType))
      return false;

   if(!IsSpreadAcceptable(sym))
      return false;

   double slPrice = 0.0;
   if(!NormalizeInitialStopLoss(sym, orderType, desiredSL, slPrice))
     {
      Print("⚠️ [", sym, "] 初始SL无效，跳过开仓。desiredSL=", DoubleToString(desiredSL, (int)SymbolInfoInteger(sym, SYMBOL_DIGITS)));
      return false;
     }

   double lotSize = CalculateLotSizeSafe(sym, slPrice, orderType);
   if(lotSize <= 0.0)
     {
      Print("⚠️ [", sym, "] 计算手数为0，跳过开仓。可能原因：风险过低、最小手数风险超标、SL距离异常或保证金不足。");
      return false;
     }

   trade.SetTypeFillingBySymbol(sym);
   trade.SetDeviationInPoints(InpSlippagePoints);
   ResetLastError();

   bool ok = false;
   if(orderType == ORDER_TYPE_BUY)
      ok = trade.Buy(lotSize, sym, 0.0, slPrice, 0.0, comment);
   else if(orderType == ORDER_TYPE_SELL)
      ok = trade.Sell(lotSize, sym, 0.0, slPrice, 0.0, comment);

   if(ok)
     {
      string dir = (orderType == ORDER_TYPE_BUY) ? "多头" : "空头";
      NotifyTrade("✅ [" + sym + "] " + dir + "开仓成功，手数=" + DoubleToString(lotSize, 2) +
                  "，SL=" + DoubleToString(slPrice, (int)SymbolInfoInteger(sym, SYMBOL_DIGITS)));
      return true;
     }

   LogTradeFailure(sym, "开仓");
   return false;
  }

//+------------------------------------------------------------------+
//| 初始止损规范化：保证方向正确，并满足券商最小止损距离              |
//+------------------------------------------------------------------+
bool NormalizeInitialStopLoss(string sym, ENUM_ORDER_TYPE orderType, double desiredSL, double &slOut)
  {
   slOut = 0.0;

   MqlTick tick;
   if(!SymbolInfoTick(sym, tick))
      return false;

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(point <= 0.0 || tick.ask <= 0.0 || tick.bid <= 0.0)
      return false;

   int stopLevelPoints = (int)SymbolInfoInteger(sym, SYMBOL_TRADE_STOPS_LEVEL);
   if(stopLevelPoints < 0)
      stopLevelPoints = 0;

   double minDistance = stopLevelPoints * point;

   if(orderType == ORDER_TYPE_BUY)
     {
      double maxSL = tick.bid - minDistance;
      if(desiredSL >= maxSL)
         desiredSL = maxSL;

      if(desiredSL <= 0.0 || desiredSL >= tick.bid)
         return false;
     }
   else if(orderType == ORDER_TYPE_SELL)
     {
      double minSL = tick.ask + minDistance;
      if(desiredSL <= minSL)
         desiredSL = minSL;

      if(desiredSL <= tick.ask)
         return false;
     }
   else
      return false;

   slOut = NormalizePrice(sym, desiredSL);
   return(slOut > 0.0);
  }

bool IsStopValidForCurrentPrice(string sym, ENUM_POSITION_TYPE type, double slPrice)
  {
   MqlTick tick;
   if(!SymbolInfoTick(sym, tick))
      return false;

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(point <= 0.0 || tick.ask <= 0.0 || tick.bid <= 0.0 || slPrice <= 0.0)
      return false;

   int stopLevelPoints = (int)SymbolInfoInteger(sym, SYMBOL_TRADE_STOPS_LEVEL);
   if(stopLevelPoints < 0)
      stopLevelPoints = 0;

   double minDistance = stopLevelPoints * point;

   if(type == POSITION_TYPE_BUY)
      return(slPrice < tick.bid && (tick.bid - slPrice) >= minDistance - point * 0.5);

   if(type == POSITION_TYPE_SELL)
      return(slPrice > tick.ask && (slPrice - tick.ask) >= minDistance - point * 0.5);

   return false;
  }

//+------------------------------------------------------------------+
//| 风险手数：使用 OrderCalcProfit，适配黄金/指数/CFD                 |
//+------------------------------------------------------------------+
double CalculateLotSizeSafe(string sym, double slPrice, ENUM_ORDER_TYPE orderType)
  {
   if(InpRiskPercent <= 0.0)
      return 0.0;

   MqlTick tick;
   if(!SymbolInfoTick(sym, tick))
      return 0.0;

   double price = 0.0;
   if(orderType == ORDER_TYPE_BUY)
      price = tick.ask;
   else if(orderType == ORDER_TYPE_SELL)
      price = tick.bid;
   else
      return 0.0;

   if(price <= 0.0 || slPrice <= 0.0)
      return 0.0;

   if(orderType == ORDER_TYPE_BUY && slPrice >= price)
      return 0.0;

   if(orderType == ORDER_TYPE_SELL && slPrice <= price)
      return 0.0;

   double riskAmount = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPercent / 100.0;
   if(riskAmount <= 0.0)
      return 0.0;

   double lossOneLot = 0.0;
   if(!OrderCalcProfit(orderType, sym, 1.0, price, slPrice, lossOneLot))
     {
      Print("⚠️ [", sym, "] OrderCalcProfit失败，错误码=", GetLastError());
      return 0.0;
     }

   lossOneLot = MathAbs(lossOneLot);
   if(lossOneLot <= 0.0)
      return 0.0;

   double rawLot = riskAmount / lossOneLot;
   double lot = NormalizeVolumeFloor(sym, rawLot);
   if(lot <= 0.0)
      return 0.0;

   double checkLoss = 0.0;
   if(OrderCalcProfit(orderType, sym, lot, price, slPrice, checkLoss))
     {
      if(MathAbs(checkLoss) > riskAmount * 1.05)
        {
         Print("⚠️ [", sym, "] 最小手数或步长导致实际风险超标，跳过。理论风险=", DoubleToString(riskAmount, 2),
               "，实际风险=", DoubleToString(MathAbs(checkLoss), 2));
         return 0.0;
        }
     }

   double margin = 0.0;
   if(OrderCalcMargin(orderType, sym, lot, price, margin))
     {
      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      if(margin > freeMargin * 0.95)
        {
         Print("⚠️ [", sym, "] 保证金不足，跳过。需要=", DoubleToString(margin, 2),
               "，可用=", DoubleToString(freeMargin, 2));
         return 0.0;
        }
     }

   return lot;
  }

//+------------------------------------------------------------------+
//| 手数规范化：低于最小手数返回0，不再强制开最小手数                 |
//+------------------------------------------------------------------+
double NormalizeVolumeFloor(string sym, double vol)
  {
   double minLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);

   if(vol <= 0.0 || minLot <= 0.0 || maxLot <= 0.0 || stepLot <= 0.0)
      return 0.0;

   double lot = MathFloor(vol / stepLot + 1e-8) * stepLot;
   lot = NormalizeDouble(lot, 8);

   if(lot > maxLot)
      lot = maxLot;

   if(lot < minLot)
      return 0.0;

   return NormalizeDouble(lot, 8);
  }

//+------------------------------------------------------------------+
//| 部分平仓手数规范化：避免把剩余仓位压到最小手数以下                |
//+------------------------------------------------------------------+
double NormalizeCloseVolume(string sym, double desiredVol, double currentVol)
  {
   double minLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);

   if(desiredVol <= 0.0 || currentVol <= 0.0 || minLot <= 0.0 || stepLot <= 0.0)
      return 0.0;

   if(currentVol <= minLot)
      return 0.0;

   double closeVol = MathFloor(desiredVol / stepLot + 1e-8) * stepLot;
   closeVol = NormalizeDouble(closeVol, 8);

   if(closeVol < minLot)
      return 0.0;

   if(closeVol >= currentVol)
      return 0.0;

   double remain = NormalizeDouble(currentVol - closeVol, 8);
   if(remain < minLot)
      return 0.0;

   return closeVol;
  }

//+------------------------------------------------------------------+
//| 交易执行辅助                                                      |
//+------------------------------------------------------------------+
bool ClosePositionByTicket(ulong ticket, string sym, string reason)
  {
   trade.SetTypeFillingBySymbol(sym);
   trade.SetDeviationInPoints(InpSlippagePoints);
   ResetLastError();

   if(trade.PositionClose(ticket, (ulong)InpSlippagePoints))
     {
      NotifyTrade("✅ [" + sym + "] " + reason);
      return true;
     }

   LogTradeFailure(sym, "全部平仓");
   return false;
  }

bool PartialClosePosition(ulong ticket, string sym, double closeVol, string reason)
  {
   trade.SetTypeFillingBySymbol(sym);
   trade.SetDeviationInPoints(InpSlippagePoints);
   ResetLastError();

   if(trade.PositionClosePartial(ticket, closeVol, (ulong)InpSlippagePoints))
     {
      NotifyTrade("✅ [" + sym + "] " + reason + "，平仓手数=" + DoubleToString(closeVol, 2));
      return true;
     }

   LogTradeFailure(sym, "部分平仓");
   return false;
  }

void EnsureBreakEvenStop(string sym,
                         ulong ticket,
                         ENUM_POSITION_TYPE type,
                         double openPrice,
                         double currentSL,
                         double currentTP)
  {
   if(!InpUseBreakEven || openPrice <= 0.0)
      return;

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(point <= 0.0)
      return;

   double beSL = openPrice;
   if(type == POSITION_TYPE_BUY)
      beSL = openPrice + InpBreakEvenBufferPoints * point;
   else if(type == POSITION_TYPE_SELL)
      beSL = openPrice - InpBreakEvenBufferPoints * point;
   else
      return;

   beSL = NormalizePrice(sym, beSL);

   if(type == POSITION_TYPE_BUY)
     {
      if(currentSL >= beSL - point * 0.5)
         return;
     }
   else if(type == POSITION_TYPE_SELL)
     {
      if(currentSL > 0.0 && currentSL <= beSL + point * 0.5)
         return;
     }

   if(!IsStopValidForCurrentPrice(sym, type, beSL))
     {
      Print("ℹ️ [", sym, "] 当前价格距离不足，暂不能把SL移动到保本。");
      return;
     }

   ResetLastError();
   if(trade.PositionModify(ticket, beSL, currentTP))
     {
      NotifyTrade("🛡️ [" + sym + "] 已将剩余仓位SL移动到保本：" +
                  DoubleToString(beSL, (int)SymbolInfoInteger(sym, SYMBOL_DIGITS)));
      return;
     }

   LogTradeFailure(sym, "移动保本SL");
  }

void LogTradeFailure(string sym, string action)
  {
   Print("❌ [", sym, "] ", action,
         "失败，retcode=", trade.ResultRetcode(),
         "，描述=", trade.ResultRetcodeDescription(),
         "，lastError=", GetLastError());
  }

//+------------------------------------------------------------------+
//| 推送通知                                                          |
//+------------------------------------------------------------------+
void NotifyTrade(string message)
  {
   Print(message);

   if(InpEnableNotifications)
      SendNotification(message);
  }

//+------------------------------------------------------------------+
//| 查询历史记录判断是否已部分平仓                                    |
//+------------------------------------------------------------------+
bool HasPartiallyClosed(ulong position_identifier)
  {
   if(position_identifier == 0)
      return false;

   if(HistorySelectByPosition(position_identifier))
     {
      int deals = HistoryDealsTotal();
      int outDeals = 0;

      for(int i = 0; i < deals; i++)
        {
         ulong dealTicket = HistoryDealGetTicket(i);
         if(dealTicket == 0)
            continue;

         if(HistoryDealGetInteger(dealTicket, DEAL_ENTRY) == DEAL_ENTRY_OUT)
            outDeals++;
        }

      if(outDeals > 0)
         return true;
     }

   return false;
  }

//+------------------------------------------------------------------+
//| 每日报告：北京时间指定小时，只统计本EA魔术码交易                  |
//+------------------------------------------------------------------+
void CheckAndSendDailyReport()
  {
   datetime beijingTime = GetBeijingTime();
   MqlDateTime dt;
   TimeToStruct(beijingTime, dt);

   if(dt.hour != InpReportHourBeijing)
      return;

   int todayKey = GetDateKey(beijingTime);
   if(todayKey == lastReportDate)
      return;

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   int eaPosCount = CountEAOpenPositions();

   datetime serverTime = TimeCurrent();
   MqlDateTime sdt;
   TimeToStruct(serverTime, sdt);

   datetime startOfTodayServer     = serverTime - (sdt.hour * 3600 + sdt.min * 60 + sdt.sec);
   datetime startOfYesterdayServer = startOfTodayServer - 86400;
   datetime endOfYesterdayServer   = startOfTodayServer - 1;

   double yesterdayProfit = 0.0;
   int yesterdayDeals = 0;

   if(HistorySelect(startOfYesterdayServer, endOfYesterdayServer))
     {
      int deals = HistoryDealsTotal();
      for(int i = 0; i < deals; i++)
        {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket == 0)
            continue;

         if((int)HistoryDealGetInteger(ticket, DEAL_MAGIC) != InpMagicNumber)
            continue;

         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_SWAP);
         yesterdayProfit += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
         yesterdayDeals++;
        }
     }

   string report = "📊【Vegas V4.1 每日简报】\n";
   report += "时间：北京时间 " + IntegerToString(InpReportHourBeijing) + ":00\n";
   report += "--------------------\n";
   report += "💰 账户余额：$" + DoubleToString(balance, 2) + "\n";
   report += "⚖️ 动态净值：$" + DoubleToString(equity, 2) + "\n";
   report += "📦 本EA当前持仓：" + IntegerToString(eaPosCount) + " 单\n";
   report += "📄 昨日本EA成交：" + IntegerToString(yesterdayDeals) + " 笔\n";
   report += "--------------------\n";

   if(yesterdayProfit > 0.0)
      report += "🎉 昨日本EA盈亏：+$" + DoubleToString(yesterdayProfit, 2);
   else if(yesterdayProfit < 0.0)
      report += "📉 昨日本EA盈亏：-$" + DoubleToString(MathAbs(yesterdayProfit), 2);
   else
      report += "⏸️ 昨日本EA盈亏：$0.00";

   NotifyTrade(report);
   lastReportDate = todayKey;
  }
//+------------------------------------------------------------------+
