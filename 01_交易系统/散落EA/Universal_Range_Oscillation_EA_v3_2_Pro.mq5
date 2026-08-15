//+------------------------------------------------------------------+
//|                                        Universal Range Osc EA v3.2 |
//|                                      Copyright 2026, Manus AI      |
//|                                       https://manus.im             |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Manus AI"
#property link      "https://manus.im"
#property version   "3.22"
#property description "Universal Range Oscillation EA based on BB, ADX, RSI, ATR"
#property description "DeepSeek V4 Pro Generated & Manually Verified"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 输入参数
input group "=== 策略参数 ==="
input int      BB_Period = 20;           // 布林带周期
input double   BB_Deviation = 2.0;       // 布林带标准差倍数
input int      ADX_Period = 14;          // ADX周期
input double   ADX_Threshold = 25.0;     // ADX震荡阈值
input int      RSI_Period = 14;          // RSI周期
input double   RSI_Overbought = 70.0;    // RSI超买阈值
input double   RSI_Oversold = 30.0;      // RSI超卖阈值

input group "=== 资金管理 ==="
input double   Risk_Percent = 1.0;       // 每笔风险百分比(%)
input double   Max_Margin_Percent = 75.0; // 最大保证金占用比例(%)

input group "=== ATR风控 ==="
input int      ATR_Period = 14;          // ATR周期
input double   ATR_StopMult = 1.8;       // 止损ATR倍数
input double   ATR_TakeMult = 1.8;       // 止盈ATR倍数
input double   ATR_TrailMult = 0.8;      // 移动止损ATR倍数
input double   ATR_ActivateMult = 1.0;   // 移动止损激活ATR倍数

input group "=== 风控熔断 ==="
input double   DailyMaxDrawdown = 6.0;   // 每日最大回撤(%)
input int      MaxConsecutiveLoss = 3;   // 连续亏损暂停次数
input int      PauseMinutes = 120;       // 暂停时间(分钟)
input double   TotalMaxDrawdown = 10.0;  // 总最大回撤(%)

input group "=== 交易时段 ==="
input int      InpStartHour = 21;        // 交易开始小时 (MT5服务器时间)
input int      InpEndHour = 2;           // 交易结束小时 (MT5服务器时间)

input group "=== 其他 ==="
input int      MagicNumber = 20260502;   // 魔术编号
input double   MaxSpread = 30.0;         // 最大点差(点)

//--- 全局变量
CTrade         m_trade;                  // 交易对象
CPositionInfo  m_position;               // 持仓信息
CAccountInfo   m_account;                // 账户信息
CSymbolInfo    m_symbol;                 // 品种信息

//--- 指标句柄
int h_BB, h_ADX, h_RSI, h_ATR;
double bb_upper[], bb_middle[], bb_lower[], adx_main[], rsi_values[], atr_values[];

//--- 状态变量
datetime       g_lastBarTime = 0;
double         g_dailyStartEquity = 0;
double         g_peakEquity = 0;
int            g_consecLoss = 0;
datetime       g_pauseStart = 0;
bool           g_isPaused = false;
bool           g_isStopped = false;

//+------------------------------------------------------------------+
//| 初始化                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(MagicNumber);
   m_symbol.Name(_Symbol);
   
   h_BB = iBands(_Symbol, _Period, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   h_ADX = iADX(_Symbol, _Period, ADX_Period);
   h_RSI = iRSI(_Symbol, _Period, RSI_Period, PRICE_CLOSE);
   h_ATR = iATR(_Symbol, _Period, ATR_Period);
   
   if(h_BB == INVALID_HANDLE || h_ADX == INVALID_HANDLE || h_RSI == INVALID_HANDLE || h_ATR == INVALID_HANDLE)
      return(INIT_FAILED);

   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_middle, true);
   ArraySetAsSeries(bb_lower, true);
   ArraySetAsSeries(adx_main, true);
   ArraySetAsSeries(rsi_values, true);
   ArraySetAsSeries(atr_values, true);

   g_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_peakEquity = g_dailyStartEquity;

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| 反初始化                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(h_BB);
   IndicatorRelease(h_ADX);
   IndicatorRelease(h_RSI);
   IndicatorRelease(h_ATR);
}

//+------------------------------------------------------------------+
//| 主循环                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   if(g_isStopped) return;
   if(!m_symbol.RefreshRates()) return;

   // 1. 总回撤熔断检查
   double currEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(currEquity > g_peakEquity) g_peakEquity = currEquity;
   if(g_peakEquity > 0 && (g_peakEquity - currEquity) / g_peakEquity * 100.0 >= TotalMaxDrawdown)
   {
      g_isStopped = true;
      Print("系统触发总回撤熔断限制。");
      return;
   }

   // 2. 实时持仓管理（移动止损）
   ManagePositions();

   // 3. K 线闭合信号检测
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   if(currentBarTime == g_lastBarTime) return;
   g_lastBarTime = currentBarTime;

   // 4. 更新指标数据
   if(!UpdateIndicators()) return;

   // 5. 每日回撤检查
   if(!CheckDailyDrawdown()) return;

   // 6. 连续亏损暂停检查
   if(g_isPaused)
   {
      if(TimeCurrent() - g_pauseStart >= PauseMinutes * 60)
      {
         g_isPaused = false;
         g_consecLoss = 0;
         Print("暂停结束，恢复交易。");
      }
      else return;
   }

   // 7. 交易时段检查
   MqlDateTime dt;
   TimeCurrent(dt);
   bool inTime = (InpStartHour < InpEndHour) ? (dt.hour >= InpStartHour && dt.hour < InpEndHour) 
                                             : (dt.hour >= InpStartHour || dt.hour < InpEndHour);
   if(!inTime) return;

   // 8. 点差检查
   if(m_symbol.Spread() > MaxSpread) return;

   // 9. 入场信号检测
   if(PositionsTotal() == 0) CheckEntrySignals();
}

//+------------------------------------------------------------------+
//| 更新指标                                                          |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
   if(CopyBuffer(h_BB, 1, 1, 2, bb_upper) <= 0) return false;
   if(CopyBuffer(h_BB, 0, 1, 2, bb_middle) <= 0) return false;
   if(CopyBuffer(h_BB, 2, 1, 2, bb_lower) <= 0) return false;
   if(CopyBuffer(h_ADX, 0, 1, 2, adx_main) <= 0) return false;
   if(CopyBuffer(h_RSI, 0, 1, 2, rsi_values) <= 0) return false;
   if(CopyBuffer(h_ATR, 0, 1, 2, atr_values) <= 0) return false;
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
      g_dailyStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }
   double dailyDD = (g_dailyStartEquity - AccountInfoDouble(ACCOUNT_EQUITY)) / g_dailyStartEquity * 100.0;
   return (dailyDD < DailyMaxDrawdown);
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

      double atr = atr_values[0];
      double profitDist = atr * ATR_StopMult * ATR_TakeMult;
      double trailTrigger = atr * ATR_ActivateMult;
      double trailDist = atr * ATR_TrailMult;
      
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
         // 中轨平半仓
         if(m_symbol.Bid() <= bb_middle[0] && profit < profitDist * 0.7)
            m_trade.PositionClosePartial(m_position.Ticket(), m_position.Volume() / 2);
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
         if(m_symbol.Ask() >= bb_middle[0] && profit < profitDist * 0.7)
            m_trade.PositionClosePartial(m_position.Ticket(), m_position.Volume() / 2);
      }
   }
}

//+------------------------------------------------------------------+
//| 入场信号                                                          |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
   double rsi = rsi_values[0];
   double adx = adx_main[0];
   double close = iClose(_Symbol, _Period, 1);
   double open = iOpen(_Symbol, _Period, 1);
   
   if(adx >= ADX_Threshold) return;

   if(rsi < RSI_Oversold && close <= bb_lower[0] && close > open)
   {
      double sl_dist = atr_values[0] * ATR_StopMult;
      double lot = CalculateLotSize(sl_dist);
      if(lot > 0)
      {
         double sl = close - sl_dist;
         double tp = close + sl_dist * ATR_TakeMult;
         m_trade.Buy(lot, _Symbol, m_symbol.Ask(), sl, tp, "URO EA Pro");
      }
   }
   else if(rsi > RSI_Overbought && close >= bb_upper[0] && close < open)
   {
      double sl_dist = atr_values[0] * ATR_StopMult;
      double lot = CalculateLotSize(sl_dist);
      if(lot > 0)
      {
         double sl = close + sl_dist;
         double tp = close - sl_dist * ATR_TakeMult;
         m_trade.Sell(lot, _Symbol, m_symbol.Bid(), sl, tp, "URO EA Pro");
      }
   }
}

//+------------------------------------------------------------------+
//| 手数计算                                                          |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_dist_price)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk_amount = equity * (Risk_Percent / 100.0);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double sl_points = sl_dist_price / _Point;
   
   if(sl_points <= 0 || tick_value <= 0) return 0;
   
   double lot = risk_amount / (sl_points * tick_value);
   
   // 保证金检查
   double margin_req = 0;
   OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, 1.0, m_symbol.Ask(), margin_req);
   double max_lot_margin = (AccountInfoDouble(ACCOUNT_FREEMARGIN) * (Max_Margin_Percent / 100.0)) / margin_req;
   lot = MathMin(lot, max_lot_margin);

   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / step) * step;
   
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   return (lot < min_lot) ? 0 : MathMin(lot, max_lot);
}

//+------------------------------------------------------------------+
//| 事务统计                                                          |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(HistoryDealSelect(trans.deal))
      {
         if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) == MagicNumber)
         {
            double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT) + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) + HistoryDealGetDouble(trans.deal, DEAL_SWAP);
            if(profit < 0)
            {
               g_consecLoss++;
               if(g_consecLoss >= MaxConsecutiveLoss)
               {
                  g_isPaused = true;
                  g_pauseStart = TimeCurrent();
               }
            }
            else g_consecLoss = 0;
         }
      }
   }
}
