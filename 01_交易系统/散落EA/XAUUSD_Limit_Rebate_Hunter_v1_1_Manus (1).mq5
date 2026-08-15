//+------------------------------------------------------------------+
//|                                  XAUUSD_Limit_Rebate_Hunter_v1_1 |
//|                                     Manus Autonomous Enhanced    |
//|                                       https://manus.im           |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Manus AI"
#property link      "https://manus.im"
#property version   "1.10"
#property description "XAUUSD 高频剥头皮 - Manus自主加固版"
#property description "新增: 订单有效期管理、物理间距强制约束、自适应成交模式"

#include <Trade\Trade.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- 输入参数 ---
input group "=== 核心设置 ==="
input int      InpMagic           = 888888;     // 魔术数字
input string   InpComment         = "LRH_v1.1_Manus"; 
input int      InpMaxSpread       = 45;         // 最大允许点差 (针对您的43点环境)

input group "=== 策略参数 (M1周期) ==="
input int      InpMAPeriod        = 60;         
input double   InpZScoreEntry1    = 2.2;        
input double   InpZScoreEntry2    = 3.0;        
input double   InpZScoreEntry3    = 3.8;        
input int      InpMinDistPoints   = 250;        // [Manus加固] 强制最小间距 2.5美金

input group "=== 资金管理 (1:200杠杆适配) ==="
input double   InpBaseLot         = 0.05;       
input double   InpLotMultiplier   = 2.0;        
input double   InpTargetProfit    = 65;         
input double   InpStopLossPercent = 3.0;        

input group "=== [Manus加固] 实战防御参数 ==="
input int      InpOrderExpireSec  = 60;         // 挂单有效期(秒)，防止僵尸单
input int      InpMaxConsecutiveSL= 2;          
input int      InpPauseMinutes    = 60;         

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
   
   // [Manus加固] 自适应成交模式探测
   ENUM_SYMBOL_TRADE_EXECUTION exec = (ENUM_SYMBOL_TRADE_EXECUTION)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_EXEMODE);
   if(exec == SYMBOL_TRADE_EXECUTION_MARKET || exec == SYMBOL_TRADE_EXECUTION_INSTANT)
      m_trade.SetTypeFilling(ORDER_FILLING_IOC);
   else
      m_trade.SetTypeFillingBySymbol(_Symbol);
   
   m_handle_ma = iMA(_Symbol, PERIOD_M1, InpMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   m_handle_std = iStdDev(_Symbol, PERIOD_M1, InpMAPeriod, 0, MODE_SMA, PRICE_CLOSE);
   
   if(m_handle_ma == INVALID_HANDLE || m_handle_std == INVALID_HANDLE) return(INIT_FAILED);
   
   m_last_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   ENUM_ORDER_TYPE_FILLING filling = m_trade.GetTypeFilling();
   Print("Manus v1.1 加固版初始化成功. 探测成交模式: ", EnumToString(filling));
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
   
   // 1. 检查冷静期
   if(TimeCurrent() < m_pause_until) return;
   
   // 2. 检查点差
   if(m_symbol.Spread() > InpMaxSpread) return;

   // 3. 统计状态
   int pos_count = 0;
   double total_volume = 0;
   double avg_price = 0;
   double last_open_price = 0;
   ENUM_POSITION_TYPE pos_type = POSITION_TYPE_BUY;

   for(int i=PositionsTotal()-1; i>=0; i--)
   {
      if(m_position.SelectByIndex(i) && m_position.Symbol()==_Symbol && m_position.Magic()==InpMagic)
      {
         pos_count++;
         pos_type = m_position.PositionType();
         total_volume += m_position.Volume();
         avg_price += m_position.PriceOpen() * m_position.Volume();
         last_open_price = m_position.PriceOpen();
      }
   }
   if(total_volume > 0) avg_price /= total_volume;

   // 4. 管理持仓与补仓
   if(pos_count > 0)
   {
      ManageCurrentPositions(pos_type, avg_price, total_volume);
      // [Manus加固] 增加物理间距校验
      PlaceLimitOrders(pos_type, pos_count, last_open_price);
   }
   else
   {
      DeleteOldLimitOrders();
      PlaceInitialOrders();
   }
}

//+------------------------------------------------------------------+
//| 放置首单挂单 (带有效期)                                          |
//+------------------------------------------------------------------+
void PlaceInitialOrders()
{
   double ma[], std[];
   if(CopyBuffer(m_handle_ma, 0, 0, 1, ma) <= 0 || CopyBuffer(m_handle_std, 0, 0, 1, std) <= 0) return;
   if(std[0] <= 0) return;

   double buy_price = ma[0] - InpZScoreEntry1 * std[0];
   double sell_price = ma[0] + InpZScoreEntry1 * std[0];
   
   // [Manus加固] 增加过期时间
   datetime expire = TimeCurrent() + InpOrderExpireSec;

   if(!OrderExists(ORDER_TYPE_BUY_LIMIT))
      m_trade.BuyLimit(InpBaseLot, m_symbol.NormalizePrice(buy_price), _Symbol, 0, 0, ORDER_TIME_SPECIFIED, expire, InpComment);
      
   if(!OrderExists(ORDER_TYPE_SELL_LIMIT))
      m_trade.SellLimit(InpBaseLot, m_symbol.NormalizePrice(sell_price), _Symbol, 0, 0, ORDER_TIME_SPECIFIED, expire, InpComment);
}

//+------------------------------------------------------------------+
//| 放置补仓挂单 (带物理间距锁死)                                     |
//+------------------------------------------------------------------+
void PlaceLimitOrders(ENUM_POSITION_TYPE type, int count, double last_price)
{
   if(count >= 3) { DeleteOldLimitOrders(); return; }
   
   double ma[], std[];
   if(CopyBuffer(m_handle_ma, 0, 0, 1, ma) <= 0 || CopyBuffer(m_handle_std, 0, 0, 1, std) <= 0) return;
   
   double target_z = (count == 1) ? InpZScoreEntry2 : InpZScoreEntry3;
   double lot = InpBaseLot * MathPow(InpLotMultiplier, count);
   datetime expire = TimeCurrent() + InpOrderExpireSec;
   
   if(type == POSITION_TYPE_BUY)
   {
      double price = ma[0] - target_z * std[0];
      // [Manus加固] 物理间距锁死判断
      double min_price = last_price - InpMinDistPoints * m_symbol.Point();
      double final_price = MathMin(price, min_price);
      
      if(!OrderExists(ORDER_TYPE_BUY_LIMIT))
         m_trade.BuyLimit(lot, m_symbol.NormalizePrice(final_price), _Symbol, 0, 0, ORDER_TIME_SPECIFIED, expire, InpComment);
   }
   else
   {
      double price = ma[0] + target_z * std[0];
      // [Manus加固] 物理间距锁死判断
      double max_price = last_price + InpMinDistPoints * m_symbol.Point();
      double final_price = MathMax(price, max_price);
      
      if(!OrderExists(ORDER_TYPE_SELL_LIMIT))
         m_trade.SellLimit(lot, m_symbol.NormalizePrice(final_price), _Symbol, 0, 0, ORDER_TIME_SPECIFIED, expire, InpComment);
   }
}

//+------------------------------------------------------------------+
//| 管理持仓                                                          |
//+------------------------------------------------------------------+
void ManageCurrentPositions(ENUM_POSITION_TYPE type, double avg_price, double volume)
{
   double current_price = (type == POSITION_TYPE_BUY) ? m_symbol.Bid() : m_symbol.Ask();
   double profit_points = (type == POSITION_TYPE_BUY) ? (current_price - avg_price) : (avg_price - current_price);
   profit_points /= m_symbol.Point();
   
   if(profit_points >= InpTargetProfit)
   {
      CloseAll();
      m_sl_counter = 0;
      return;
   }
   
   // 整体止损保护
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(equity < balance * (1.0 - InpStopLossPercent/100.0))
   {
      CloseAll();
      m_sl_counter++;
      if(m_sl_counter >= InpMaxConsecutiveSL)
      {
         m_pause_until = TimeCurrent() + InpPauseMinutes * 60;
         PrintFormat("[Manus防护] 触发连续止损冷静期. 暂停至: %s", TimeToString(m_pause_until));
      }
   }
}

//+------------------------------------------------------------------+
//| 辅助功能                                                          |
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
         m_trade.OrderDelete(ticket);
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
