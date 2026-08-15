//+------------------------------------------------------------------+
//|                                        Universal Range Osc EA v3.2 |
//|                                      Copyright 2026, Manus AI      |
//|                                       https://manus.im             |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Manus AI"
#property link      "https://manus.im"
#property version   "3.21"
#property description "Universal Range Oscillation EA based on BB, ADX, RSI, ATR"
#property description "Fixed TimeHour and TimeCurrent compilation errors for MQL5"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 输入参数
input double   RiskPercent       = 1.0;           // 每笔交易风险 (净值的 %)
input int      BBPeriod          = 20;            // 布林带周期
input double   BBDeviation       = 2.0;           // 布林带偏差
input int      ADXPeriod         = 14;            // ADX 周期
input int      RSIPeriod         = 14;            // RSI 周期
input int      ATRPeriod         = 14;            // ATR 周期
input double   StopLossATRMult   = 1.8;           // 止损 ATR 倍数
input double   TakeProfitMult    = 1.8;           // 止盈 ATR 倍数 (相对于止损)
input double   TrailingStopATR   = 1.0;           // 移动止损触发 (ATR 利润)
input double   TrailingDistATR   = 0.8;           // 移动止损距离 (ATR)
input double   DailyDrawdownLim  = 6.0;           // 每日回撤限制 (%)
input int      MaxConsecLoss     = 3;             // 暂停前最大连续亏损次数
input int      PauseMinutes      = 120;           // 连续亏损后暂停时长 (分钟)
input double   TotalDrawdownLim  = 10.0;          // 总回撤限制 (%)
input int      MagicNumber       = 20260502;      // 魔术字
input int      Slippage          = 30;            // 滑点 (Points)
input int      InpMaxSpread      = 30;            // 最大点差限制 (Points)
input int      InpStartHour      = 21;            // 交易开始小时 (MT5服务器时间)
input int      InpEndHour        = 2;             // 交易结束小时 (MT5服务器时间)

//--- 全局对象
CTrade         m_trade;                           // 交易对象
CPositionInfo  m_position;                        // 持仓信息
CSymbolInfo    m_symbol;                          // 交易品种信息
CAccountInfo   m_account;                         // 账户信息

//--- 指标句柄
int            hBB, hADX, hRSI, hATR;

//--- 缓冲区
double         bbUpper[], bbMiddle[], bbLower[], adxMain[], rsiBuffer[], atrBuffer[];

//--- 状态变量
datetime       lastBarTime = 0;
double         dailyStartEquity = 0;
int            consecLosses = 0;
datetime       pauseStart = 0;
bool           paused = false;
double         peakEquity = 0;
bool           systemStopped = false;

//+------------------------------------------------------------------+
//| 初始化函数                                                        |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(MagicNumber);
   m_symbol.Name(_Symbol);
   m_trade.SetDeviationInPoints(Slippage);
   
   hBB = iBands(_Symbol, _Period, BBPeriod, 0, BBDeviation, PRICE_CLOSE);
   hADX = iADX(_Symbol, _Period, ADXPeriod);
   hRSI = iRSI(_Symbol, _Period, RSIPeriod, PRICE_CLOSE);
   hATR = iATR(_Symbol, _Period, ATRPeriod);
   
   if(hBB == INVALID_HANDLE || hADX == INVALID_HANDLE || hRSI == INVALID_HANDLE || hATR == INVALID_HANDLE)
      return(INIT_FAILED);

   ArraySetAsSeries(bbUpper, true);
   ArraySetAsSeries(bbMiddle, true);
   ArraySetAsSeries(bbLower, true);
   ArraySetAsSeries(adxMain, true);
   ArraySetAsSeries(rsiBuffer, true);
   ArraySetAsSeries(atrBuffer, true);

   dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   peakEquity = dailyStartEquity;
   
   m_trade.SetAsyncMode(false);
   m_trade.SetTypeFillingBySymbol(_Symbol);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| 反初始化函数                                                      |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(hBB);
   IndicatorRelease(hADX);
   IndicatorRelease(hRSI);
   IndicatorRelease(hATR);
}

//+------------------------------------------------------------------+
//| 分时报价处理函数                                                  |
//+------------------------------------------------------------------+
void OnTick()
{
   if(systemStopped) return;
   if(!m_symbol.RefreshRates()) return;
   
   // 检查总回撤
   double currEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(currEquity > peakEquity) peakEquity = currEquity;
   if(peakEquity > 0 && (peakEquity - currEquity) / peakEquity * 100.0 >= TotalDrawdownLim)
   {
      systemStopped = true;
      Print("系统触发总回撤熔断限制。");
      return;
   }

   // 仅在 K 线闭合时处理新信号
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   if(currentBarTime == lastBarTime) 
   {
      // 实时管理持仓（如移动止损）
      ManagePositions();
      return;
   }
   lastBarTime = currentBarTime;

   // 更新指标数据
   if(!UpdateIndicators()) return;

   // 每日回撤检查
   if(!CheckDailyDrawdown()) return;

   // 连续亏损暂停检查
   if(paused)
   {
      if(TimeCurrent() - pauseStart >= PauseMinutes * 60)
      {
         paused = false;
         consecLosses = 0;
         Print("暂停结束，恢复交易。");
      }
      else return;
   }

   // 交易时段检查 (MQL5 兼容方式)
   MqlDateTime currTimeStruct;
   TimeCurrent(currTimeStruct);
   int currHour = currTimeStruct.hour;
   
   bool inTime = (InpStartHour < InpEndHour) ? (currHour >= InpStartHour && currHour < InpEndHour) 
                                             : (currHour >= InpStartHour || currHour < InpEndHour);
   if(!inTime) return;

   // 点差检查
   if(m_symbol.Spread() > InpMaxSpread) return;

   // 信号检测
   if(PositionsTotal() == 0)
   {
      CheckEntrySignals();
   }
}

//+------------------------------------------------------------------+
//| 更新指标数据                                                      |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(CopyBuffer(hBB, 0, 1, 2, bbUpper) <= 0) return false;
   if(CopyBuffer(hBB, 1, 1, 2, bbMiddle) <= 0) return false;
   if(CopyBuffer(hBB, 2, 1, 2, bbLower) <= 0) return false;
   if(CopyBuffer(hADX, 0, 1, 2, adxMain) <= 0) return false;
   if(CopyBuffer(hRSI, 0, 1, 2, rsiBuffer) <= 0) return false;
   if(CopyBuffer(hATR, 0, 1, 2, atrBuffer) <= 0) return false;
   return true;
}

//+------------------------------------------------------------------+
//| 每日回撤检查                                                      |
//+------------------------------------------------------------------+
bool CheckDailyDrawdown()
{
   MqlDateTime dt;
   TimeCurrent(dt);
   static int lastDay = -1;
   if(dt.day != lastDay)
   {
      lastDay = dt.day;
      dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }
   double dailyDD = (dailyStartEquity - AccountInfoDouble(ACCOUNT_EQUITY)) / dailyStartEquity * 100.0;
   return (dailyDD < DailyDrawdownLim);
}

//+------------------------------------------------------------------+
//| 持仓管理（移动止损与中轨平仓）                                      |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!m_position.SelectByIndex(i)) continue;
      if(m_position.Symbol() != _Symbol || m_position.Magic() != MagicNumber) continue;

      double profitDist = atrBuffer[0] * StopLossATRMult * TakeProfitMult;
      double trailTrigger = atrBuffer[0] * TrailingStopATR;
      double trailDist = atrBuffer[0] * TrailingDistATR;
      
      if(m_position.PositionType() == POSITION_TYPE_BUY)
      {
         double profit = m_symbol.Bid() - m_position.PriceOpen();
         // 移动止损
         if(profit >= trailTrigger)
         {
            double newSL = m_symbol.Bid() - trailDist;
            if(newSL > m_position.StopLoss())
               m_trade.PositionModify(m_position.Ticket(), newSL, m_position.TakeProfit());
         }
         // 中轨部分平仓
         if(m_symbol.Bid() <= bbMiddle[0] && profit < profitDist * 0.7)
         {
            m_trade.PositionClosePartial(m_position.Ticket(), m_position.Volume() / 2);
         }
      }
      else if(m_position.PositionType() == POSITION_TYPE_SELL)
      {
         double profit = m_position.PriceOpen() - m_symbol.Ask();
         if(profit >= trailTrigger)
         {
            double newSL = m_symbol.Ask() + trailDist;
            if(m_position.StopLoss() == 0 || newSL < m_position.StopLoss())
               m_trade.PositionModify(m_position.Ticket(), newSL, m_position.TakeProfit());
         }
         if(m_symbol.Ask() >= bbMiddle[0] && profit < profitDist * 0.7)
         {
            m_trade.PositionClosePartial(m_position.Ticket(), m_position.Volume() / 2);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| 入场信号检查                                                      |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
   double rsi = rsiBuffer[0];
   double adx = adxMain[0];
   double close = iClose(_Symbol, _Period, 1);
   double open = iOpen(_Symbol, _Period, 1);
   
   if(adx >= 25) return;

   // 多单：RSI < 30 + 触及下轨 + 收阳
   if(rsi < 30 && close <= bbLower[0] && close > open)
   {
      double lot = CalculateLotSize(close - (atrBuffer[0] * StopLossATRMult));
      if(lot > 0)
      {
         double sl = close - atrBuffer[0] * StopLossATRMult;
         double tp = close + (atrBuffer[0] * StopLossATRMult) * TakeProfitMult;
         m_trade.Buy(lot, _Symbol, m_symbol.Ask(), sl, tp, "Universal Range EA");
      }
   }
   // 空单：RSI > 70 + 触及上轨 + 收阴
   else if(rsi > 70 && close >= bbUpper[0] && close < open)
   {
      double lot = CalculateLotSize(close + (atrBuffer[0] * StopLossATRMult));
      if(lot > 0)
      {
         double sl = close + atrBuffer[0] * StopLossATRMult;
         double tp = close - (atrBuffer[0] * StopLossATRMult) * TakeProfitMult;
         m_trade.Sell(lot, _Symbol, m_symbol.Bid(), sl, tp, "Universal Range EA");
      }
   }
}

//+------------------------------------------------------------------+
//| 动态手数计算                                                      |
//+------------------------------------------------------------------+
double CalculateLotSize(double slPrice)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = equity * (RiskPercent / 100.0);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double slDist = MathAbs(iClose(_Symbol, _Period, 1) - slPrice) / _Point;
   
   if(slDist <= 0 || tickValue <= 0) return 0;
   
   double lot = riskAmount / (slDist * tickValue);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / step) * step;
   
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(lot < minLot) lot = 0; // 风险过小，不建议开仓
   if(lot > maxLot) lot = maxLot;
   
   return lot;
}

//+------------------------------------------------------------------+
//| 交易事务处理（统计连续亏损）                                        |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(HistoryDealSelect(trans.deal))
      {
         long magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
         if(magic == MagicNumber)
         {
            double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT) + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) + HistoryDealGetDouble(trans.deal, DEAL_SWAP);
            if(profit < 0)
            {
               consecLosses++;
               if(consecLosses >= MaxConsecLoss)
               {
                  paused = true;
                  pauseStart = TimeCurrent();
               }
            }
            else consecLosses = 0;
         }
      }
   }
}
