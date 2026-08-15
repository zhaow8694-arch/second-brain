//+------------------------------------------------------------------+
//|                                  Universal Range Oscillation EA |
//|                                            v3.2 最终实盘修复版    |
//|                                      Copyright 2026, 资深架构师 |
//|                                       https://manus.im           |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, 资深架构师"
#property link      "https://manus.im"
#property version   "3.21"
#property description "Universal Range Oscillation EA - 稳健型震荡均值回归策略"
#property description "核心逻辑: Bollinger Bands + ADX过滤 + RSI确认"
#property description "风控: 动态1%风险真实预演 + 动态ATR止盈止损 + 移动止损 + 熔断机制"

#include <Trade\Trade.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 输入参数组 ---
input group "=== 策略核心参数 ==="
input int    InpMagicNumber       = 20260302;   // EA魔术数字 (Magic Number)
input string InpTradeComment      = "URO_v3.2_Fixed"; // 订单注释

input group "=== 资金管理与风控 ==="
input double InpRiskPercent       = 1.0;        // 单笔风险百分比 (1.0 = 1%)
input double InpMaxDailyDD        = 6.0;        // 每日最大回撤 (%) - 熔断
input double InpMaxTotalDD        = 10.0;       // 账户最大回撤 (%) - 熔断
input double InpRecoveryDD        = 5.0;        // 回撤恢复阈值 (%) - 恢复交易
input int    InpMaxConsecutiveLoss= 3;          // 连续亏损暂停笔数
input int    InpPauseHours        = 2;          // 连续亏损暂停小时数
input int    InpMaxSpreadPoints   = 30;         // 允许的最大点差 (Points)

input group "=== 指标参数 ==="
input int    InpBandsPeriod       = 20;         // Bollinger Bands 周期
input double InpBandsDeviation    = 2.0;        // Bollinger Bands 标准差
input int    InpAdxPeriod         = 14;         // ADX 周期
input double InpAdxThreshold      = 25.0;       // ADX 震荡过滤阈值 (低于此值开仓)
input int    InpRsiPeriod         = 14;         // RSI 周期
input double InpRsiOverbought     = 70.0;       // RSI 超买阈值
input double InpRsiOversold       = 30.0;       // RSI 超卖阈值
input int    InpAtrPeriod         = 14;         // ATR 周期

input group "=== 止盈止损与离场 ==="
input double InpSlAtrMultiplier   = 1.8;        // 止损 ATR 乘数
input double InpTpToSlRatio       = 1.8;        // 盈亏比 (TP/SL比例)
input double InpTrailStartAtrMult = 1.0;        // 移动止损启动 ATR 乘数
input double InpTrailDistAtrMult  = 0.8;        // 移动止损距离 ATR 乘数
input double InpPartialCloseRatio = 0.5;        // 中轨平仓比例 (0.5 = 50%)
input double InpPartialCloseFilter= 0.7;        // 若浮盈达到总止盈的百分比(0.7=70%)则不平半仓
input double InpMaxEntryDeviation = 0.5;        // 信号触发后允许的最大滑点偏差

input group "=== 交易时段 ==="
input int    InpStartHour         = 21;         // 允许开仓起始小时 (服务器时间)
input int    InpEndHour           = 2;          // 允许开仓结束小时 (服务器时间)
input bool   InpAvoidFridayClose  = true;       // 周五收盘前禁止新开仓

//--- 全局变量与对象 ---
CTrade         m_trade;
CSymbolInfo    m_symbol;
CPositionInfo  m_position;
CAccountInfo   m_account;

// 指标句柄
int            m_handle_bb;
int            m_handle_adx;
int            m_handle_rsi;
int            m_handle_atr;

// 状态变量
double         m_start_day_equity = 0.0;      
double         m_highest_equity   = 0.0;      
int            m_consecutive_loss_count = 0;  
datetime       m_pause_until_time = 0;        
bool           m_is_global_drawdown_paused = false; 

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!m_symbol.Name(_Symbol)) return(INIT_FAILED);
   m_symbol.RefreshRates();

   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetDeviationInPoints(10);
   m_trade.SetTypeFillingBySymbol(_Symbol);

   m_handle_bb = iBands(_Symbol, _Period, InpBandsPeriod, 0, InpBandsDeviation, PRICE_CLOSE);
   m_handle_adx = iADX(_Symbol, _Period, InpAdxPeriod);
   m_handle_rsi = iRSI(_Symbol, _Period, InpRsiPeriod, PRICE_CLOSE);
   m_handle_atr = iATR(_Symbol, _Period, InpAtrPeriod);

   if(m_handle_bb == INVALID_HANDLE || m_handle_adx == INVALID_HANDLE || 
      m_handle_rsi == INVALID_HANDLE || m_handle_atr == INVALID_HANDLE)
      return(INIT_FAILED);

   m_highest_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   m_start_day_equity = m_highest_equity;

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(m_handle_bb);
   IndicatorRelease(m_handle_adx);
   IndicatorRelease(m_handle_rsi);
   IndicatorRelease(m_handle_atr);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!m_symbol.RefreshRates()) return;
   
   double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(current_equity > m_highest_equity) m_highest_equity = current_equity;

   CheckNewDay();
   
   // 执行风控熔断检查
   if(CheckRiskManagement()) return;

   // 检查持仓管理（移动止损/中轨平仓）
   ManagePositions();

   // 只有在没有持仓时才检查开仓
   if(PositionsTotal() > 0) return;
   
   if(!CheckTradingTime()) return;

   // K线闭合触发
   static datetime last_bar_time = 0;
   datetime current_bar_time = iTime(_Symbol, _Period, 0);
   if(current_bar_time == last_bar_time) return;

   // 获取指标数据
   double bb_up[], bb_mid[], bb_low[], adx[], rsi[], atr[];
   ArraySetAsSeries(bb_up, true); ArraySetAsSeries(bb_mid, true); ArraySetAsSeries(bb_low, true);
   ArraySetAsSeries(adx, true); ArraySetAsSeries(rsi, true); ArraySetAsSeries(atr, true);

   if(CopyBuffer(m_handle_bb, 1, 1, 1, bb_up) <= 0 ||
      CopyBuffer(m_handle_bb, 0, 1, 1, bb_mid) <= 0 ||
      CopyBuffer(m_handle_bb, 2, 1, 1, bb_low) <= 0 ||
      CopyBuffer(m_handle_adx, 0, 1, 1, adx) <= 0 ||
      CopyBuffer(m_handle_rsi, 0, 1, 1, rsi) <= 0 ||
      CopyBuffer(m_handle_atr, 0, 1, 1, atr) <= 0) return;

   if(adx[0] >= InpAdxThreshold) { last_bar_time = current_bar_time; return; }
   if(m_symbol.Spread() > InpMaxSpreadPoints) return;

   double close_1 = iClose(_Symbol, _Period, 1);
   double open_1  = iOpen(_Symbol, _Period, 1);

   bool is_buy = (rsi[0] < InpRsiOversold && close_1 <= bb_low[0] && close_1 > open_1);
   bool is_sell = (rsi[0] > InpRsiOverbought && close_1 >= bb_up[0] && close_1 < open_1);

   if(is_buy && MathAbs(m_symbol.Ask() - close_1) <= InpMaxEntryDeviation)
      ExecuteTrade(ORDER_TYPE_BUY, atr[0]);
   else if(is_sell && MathAbs(m_symbol.Bid() - close_1) <= InpMaxEntryDeviation)
      ExecuteTrade(ORDER_TYPE_SELL, atr[0]);

   last_bar_time = current_bar_time;
}

//+------------------------------------------------------------------+
//| 执行交易                                                          |
//+------------------------------------------------------------------+
void ExecuteTrade(ENUM_ORDER_TYPE type, double atr_value)
{
   if(AccountInfoDouble(ACCOUNT_FREEMARGIN) / AccountInfoDouble(ACCOUNT_BALANCE) < 0.35) return;

   double sl_dist = atr_value * InpSlAtrMultiplier;
   double tp_dist = sl_dist * InpTpToSlRatio;
   double price = (type == ORDER_TYPE_BUY) ? m_symbol.Ask() : m_symbol.Bid();
   double sl = (type == ORDER_TYPE_BUY) ? price - sl_dist : price + sl_dist;
   double tp = (type == ORDER_TYPE_BUY) ? price + tp_dist : price - tp_dist;

   // 精准手数计算
   double risk_money = AccountInfoDouble(ACCOUNT_EQUITY) * (InpRiskPercent / 100.0);
   double loss_per_lot = 0;
   if(!OrderCalcProfit(type, _Symbol, 1.0, price, sl, loss_per_lot)) return;
   
   double lot = MathAbs(risk_money / loss_per_lot);
   double step = m_symbol.LotsStep();
   lot = MathFloor(lot / step) * step;
   
   // 保证金安全检查
   double margin = 0;
   if(OrderCalcMargin(type, _Symbol, lot, price, margin) && margin > AccountInfoDouble(ACCOUNT_FREEMARGIN) * 0.75)
      lot = MathFloor((AccountInfoDouble(ACCOUNT_FREEMARGIN) * 0.75 / (margin/lot)) / step) * step;

   if(lot < m_symbol.LotsMin()) return;

   for(int i=0; i<3; i++)
   {
      if(m_trade.Buy(lot, _Symbol, price, sl, tp, InpTradeComment) || 
         m_trade.Sell(lot, _Symbol, price, sl, tp, InpTradeComment)) break;
      Sleep(500); m_symbol.RefreshRates();
      price = (type == ORDER_TYPE_BUY) ? m_symbol.Ask() : m_symbol.Bid();
   }
}

//+------------------------------------------------------------------+
//| 持仓管理                                                          |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!m_position.SelectByIndex(i)) continue;
      if(m_position.Symbol() != _Symbol || m_position.Magic() != InpMagicNumber) continue;

      double atr_val = 0;
      double atr_buf[]; ArraySetAsSeries(atr_buf, true);
      if(CopyBuffer(m_handle_atr, 0, 1, 1, atr_buf) > 0) atr_val = atr_buf[0]; else continue;

      double profit = (m_position.PositionType() == POSITION_TYPE_BUY) ? 
                      (m_symbol.Bid() - m_position.PriceOpen()) : (m_position.PriceOpen() - m_symbol.Ask());

      // 1. 移动止损
      if(profit > atr_val * InpTrailStartAtrMult)
      {
         double new_sl = (m_position.PositionType() == POSITION_TYPE_BUY) ? 
                         (m_symbol.Bid() - atr_val * InpTrailDistAtrMult) : (m_symbol.Ask() + atr_val * InpTrailDistAtrMult);
         if((m_position.PositionType() == POSITION_TYPE_BUY && new_sl > m_position.StopLoss()) ||
            (m_position.PositionType() == POSITION_TYPE_SELL && (new_sl < m_position.StopLoss() || m_position.StopLoss() == 0)))
            m_trade.PositionModify(m_position.Ticket(), new_sl, m_position.TakeProfit());
      }

      // 2. 中轨平仓
      double mid_buf[]; ArraySetAsSeries(mid_buf, true);
      if(CopyBuffer(m_handle_bb, 0, 1, 1, mid_buf) <= 0) continue;
      double close_1 = iClose(_Symbol, _Period, 1), open_1 = iOpen(_Symbol, _Period, 1);
      bool touched = (m_position.PositionType() == POSITION_TYPE_BUY && open_1 < mid_buf[0] && close_1 >= mid_buf[0]) ||
                     (m_position.PositionType() == POSITION_TYPE_SELL && open_1 > mid_buf[0] && close_1 <= mid_buf[0]);

      if(touched && profit < MathAbs(m_position.TakeProfit() - m_position.PriceOpen()) * InpPartialCloseFilter)
      {
         double p_lot = MathFloor((m_position.Volume() * InpPartialCloseRatio) / m_symbol.LotsStep()) * m_symbol.LotsStep();
         if(p_lot >= m_symbol.LotsMin() && p_lot < m_position.Volume())
            m_trade.PositionClosePartial(m_position.Ticket(), p_lot);
      }
   }
}

//+------------------------------------------------------------------+
//| 风控检查                                                          |
//+------------------------------------------------------------------+
bool CheckRiskManagement()
{
   if(TimeCurrent() < m_pause_until_time) return true;
   
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double total_dd = (m_highest_equity - equity) / m_highest_equity * 100.0;
   
   if(m_is_global_drawdown_paused) { if(total_dd < InpRecoveryDD) m_is_global_drawdown_paused = false; else return true; }
   else if(total_dd > InpMaxTotalDD) { m_is_global_drawdown_paused = true; return true; }

   double daily_dd = (m_start_day_equity - equity) / m_start_day_equity * 100.0;
   if(daily_dd > InpMaxDailyDD) return true;

   return false;
}

//+------------------------------------------------------------------+
//| 交易时段检查                                                      |
//+------------------------------------------------------------------+
bool CheckTradingTime()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   if(InpAvoidFridayClose && dt.day_of_week == 5 && dt.hour >= 20) return false;
   return (InpStartHour > InpEndHour) ? (dt.hour >= InpStartHour || dt.hour < InpEndHour) : (dt.hour >= InpStartHour && dt.hour < InpEndHour);
}

//+------------------------------------------------------------------+
//| 连亏处理                                                          |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans, const MqlTradeRequest& req, const MqlTradeResult& res)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(HistoryDealSelect(trans.deal) && HistoryDealGetInteger(trans.deal, DEAL_MAGIC) == InpMagicNumber && HistoryDealGetInteger(trans.deal, DEAL_ENTRY) == DEAL_ENTRY_OUT)
      {
         if(HistoryDealGetDouble(trans.deal, DEAL_PROFIT) + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION) + HistoryDealGetDouble(trans.deal, DEAL_SWAP) < 0)
         {
            m_consecutive_loss_count++;
            if(m_consecutive_loss_count >= InpMaxConsecutiveLoss) m_pause_until_time = TimeCurrent() + InpPauseHours * 3600;
         }
         else m_consecutive_loss_count = 0;
      }
   }
}

void CheckNewDay()
{
   static int last_day = -1;
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   if(dt.day != last_day) { m_start_day_equity = AccountInfoDouble(ACCOUNT_EQUITY); last_day = dt.day; }
}
