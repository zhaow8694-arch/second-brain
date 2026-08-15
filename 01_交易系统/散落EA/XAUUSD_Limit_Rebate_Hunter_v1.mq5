//+------------------------------------------------------------------+
//|                                  XAUUSD_Limit_Rebate_Hunter_v1 |
//|                                      Copyright 2026, Manus AI   |
//|                                       https://manus.im           |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Manus AI"
#property link      "https://manus.im"
#property version   "1.00"
#property description "XAUUSD 高频剥头皮策略 - 左侧挂单 + 金字塔补仓 + 返佣优化"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 输入参数 ---
input group "=== 核心设置 ==="
input int      InpMagic           = 888888;     // 魔术数字
input string   InpComment         = "LRH_v1";   // 订单注释
input int      InpMaxSpread       = 50;         // 最大允许点差 (Points)

input group "=== 策略参数 (M1周期) ==="
input int      InpMAPeriod        = 60;         // 均线周期 (用于计算Z-Score)
input double   InpZScoreEntry1    = 2.2;        // 第一层挂单 Z-Score 阈值
input double   InpZScoreEntry2    = 3.0;        // 第二层补仓 Z-Score 阈值
input double   InpZScoreEntry3    = 3.8;        // 第三层补仓 Z-Score 阈值
input int      InpMinDistPoints   = 150;        // 层级间最小间距 (1.5美金)

input group "=== 资金管理 (1:200杠杆适配) ==="
input double   InpBaseLot         = 0.05;       // 首单手数 (建议2000刀账户0.05)
input double   InpLotMultiplier   = 2.0;        // 补仓倍数
input double   InpTargetProfit    = 65;         // 目标止盈点数 (Points, 净利约47点)
input double   InpStopLossPercent = 3.0;        // 组订单最大止损 (账户净值的%)

input group "=== 保护机制 ==="
input int      InpMaxConsecutiveSL= 2;          // 连续止损休眠笔数
input int      InpPauseMinutes    = 60;         // 强制休眠分钟数

//--- 全局变量 ---
CTrade         m_trade;
CSymbolInfo    m_symbol;
CPositionInfo  m_position;
CAccountInfo   m_account;

int            m_handle_ma;
int            m_handle_std;
datetime       m_pause_until = 0;
int            m_sl_counter = 0;
double         m_last_equity = 0;

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!m_symbol.Name(_Symbol)) return(INIT_FAILED);
   m_symbol.RefreshRates();
   
   m_trade.SetExpertMagicNumber(InpMagic);
   m_trade.SetTypeFillingBySymbol(_Symbol);
   
   m_handle_ma = iMA(_Symbol, PERIOD_M1, InpMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   m_handle_std = iStdDev(_Symbol, PERIOD_M1, InpMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   
   if(m_handle_ma == INVALID_HANDLE || m_handle_std == INVALID_HANDLE) return(INIT_FAILED);
   
   m_last_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(m_handle_ma);
   IndicatorRelease(m_handle_std);
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!m_symbol.RefreshRates()) return;
   
   // 1. 检查休眠状态
   if(TimeCurrent() < m_pause_until) return;
   
   // 2. 检查点差
   if(m_symbol.Spread() > InpMaxSpread) return;

   // 3. 统计当前持仓与挂单
   int pos_count = 0;
   int order_count = 0;
   double total_volume = 0;
   double avg_price = 0;
   ENUM_POSITION_TYPE pos_type = POSITION_TYPE_BUY;

   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(m_position.SelectByIndex(i) && m_position.Symbol()==_Symbol && m_position.Magic()==InpMagic)
      {
         pos_count++;
         pos_type = m_position.PositionType();
         total_volume += m_position.Volume();
         avg_price += m_position.PriceOpen() * m_position.Volume();
      }
   }
   if(total_volume > 0) avg_price /= total_volume;

   // 4. 管理现有持仓 (止盈/止损)
   if(pos_count > 0)
   {
      ManageCurrentPositions(pos_type, avg_price, total_volume);
      // 如果已经有持仓，尝试放置补仓挂单
      PlaceLimitOrders(pos_type, pos_count, avg_price);
   }
   else
   {
      // 5. 无持仓时，清理旧挂单并放置首单挂单
      DeleteOldLimitOrders();
      PlaceInitialOrders();
   }
}

//+------------------------------------------------------------------+
//| 放置首单挂单                                                     |
//+------------------------------------------------------------------+
void PlaceInitialOrders()
{
   double ma[], std[];
   if(CopyBuffer(m_handle_ma, 0, 0, 1, ma) <= 0 || CopyBuffer(m_handle_std, 0, 0, 1, std) <= 0) return;
   if(std[0] == 0) return;

   double buy_price = ma[0] - InpZScoreEntry1 * std[0];
   double sell_price = ma[0] + InpZScoreEntry1 * std[0];
   
   // 检查挂单是否已存在，不存在则挂
   if(!OrderExists(ORDER_TYPE_BUY_LIMIT))
      m_trade.BuyLimit(InpBaseLot, m_symbol.NormalizePrice(buy_price), _Symbol, 0, 0, ORDER_TIME_GTC, 0, InpComment);
      
   if(!OrderExists(ORDER_TYPE_SELL_LIMIT))
      m_trade.SellLimit(InpBaseLot, m_symbol.NormalizePrice(sell_price), _Symbol, 0, 0, ORDER_TIME_GTC, 0, InpComment);
}

//+------------------------------------------------------------------+
//| 放置补仓挂单                                                     |
//+------------------------------------------------------------------+
void PlaceLimitOrders(ENUM_POSITION_TYPE type, int count, double last_price)
{
   if(count >= 3) return; // 最多3层
   
   double ma[], std[];
   if(CopyBuffer(m_handle_ma, 0, 0, 1, ma) <= 0 || CopyBuffer(m_handle_std, 0, 0, 1, std) <= 0) return;
   
   double target_z = (count == 1) ? InpZScoreEntry2 : InpZScoreEntry3;
   double lot = InpBaseLot * MathPow(InpLotMultiplier, count);
   
   if(type == POSITION_TYPE_BUY)
   {
      double price = ma[0] - target_z * std[0];
      if(price < last_price - InpMinDistPoints * m_symbol.Point() && !OrderExists(ORDER_TYPE_BUY_LIMIT))
         m_trade.BuyLimit(lot, m_symbol.NormalizePrice(price), _Symbol, 0, 0, ORDER_TIME_GTC, 0, InpComment);
   }
   else
   {
      double price = ma[0] + target_z * std[0];
      if(price > last_price + InpMinDistPoints * m_symbol.Point() && !OrderExists(ORDER_TYPE_SELL_LIMIT))
         m_trade.SellLimit(lot, m_symbol.NormalizePrice(price), _Symbol, 0, 0, ORDER_TIME_GTC, 0, InpComment);
   }
}

//+------------------------------------------------------------------+
//| 管理持仓止盈止损                                                 |
//+------------------------------------------------------------------+
void ManageCurrentPositions(ENUM_POSITION_TYPE type, double avg_price, double volume)
{
   double current_price = (type == POSITION_TYPE_BUY) ? m_symbol.Bid() : m_symbol.Ask();
   double profit_points = (type == POSITION_TYPE_BUY) ? (current_price - avg_price) : (avg_price - current_price);
   profit_points /= m_symbol.Point();
   
   // 1. 整体止盈
   if(profit_points >= InpTargetProfit)
   {
      CloseAll();
      Print("目标止盈达成，全平离场。");
      m_sl_counter = 0; // 重置连损计数
      return;
   }
   
   // 2. 整体止损 (基于账户净值百分比)
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(equity < balance * (1.0 - InpStopLossPercent/100.0))
   {
      CloseAll();
      m_sl_counter++;
      PrintFormat("触发整体止损保护。当前连损: %d", m_sl_counter);
      if(m_sl_counter >= InpMaxConsecutiveSL)
      {
         m_pause_until = TimeCurrent() + InpPauseHours * 3600;
         PrintFormat("连续亏损达标，进入冷静期。休眠至: %s", TimeToString(m_pause_until));
      }
   }
}

//+------------------------------------------------------------------+
//| 辅助函数                                                         |
//+------------------------------------------------------------------+
void CloseAll()
{
   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(m_position.SelectByIndex(i) && m_position.Symbol()==_Symbol && m_position.Magic()==InpMagic)
         m_trade.PositionClose(m_position.Ticket());
   }
   DeleteOldLimitOrders();
}

void DeleteOldLimitOrders()
{
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(OrderSelect(ticket) && OrderGetInteger(ORDER_MAGIC)==InpMagic && OrderGetString(ORDER_SYMBOL)==_Symbol)
      {
         ENUM_ORDER_TYPE type = (ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
         if(type == ORDER_TYPE_BUY_LIMIT || type == ORDER_TYPE_SELL_LIMIT)
            m_trade.OrderDelete(ticket);
      }
   }
}

bool OrderExists(ENUM_ORDER_TYPE type)
{
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(OrderSelect(ticket) && OrderGetInteger(ORDER_MAGIC)==InpMagic && 
         OrderGetString(ORDER_SYMBOL)==_Symbol && OrderGetInteger(ORDER_TYPE)==type)
         return true;
   }
   return false;
}
