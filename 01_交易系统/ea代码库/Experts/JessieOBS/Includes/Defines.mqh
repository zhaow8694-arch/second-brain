#ifndef _DEFINES_MQH_
#define _DEFINES_MQH_

#define EA_MAGIC_NUMBER 2024050801
#define EA_VERSION     "1.10"

enum ENUM_MARKET_STATE
{
   MARKET_STATE_TRENDING = 0,
   MARKET_STATE_RANGING  = 1,
   MARKET_STATE_UNKNOWN  = 2
};

enum ENUM_TRADE_DIRECTION
{
   TRADE_NONE  = 0,
   TRADE_BUY   = 1,
   TRADE_SELL  = 2
};

enum ENUM_LOG_LEVEL
{
   LOG_INFO  = 0,
   LOG_WARN  = 1,
   LOG_ERROR = 2
};

enum ENUM_CIRCUIT_STATE
{
   CIRCUIT_NORMAL  = 0,
   CIRCUIT_ACTIVE  = 1
};

enum ENUM_STRATEGY_TYPE
{
   STRATEGY_TREND   = 0,
   STRATEGY_RANGING = 1
};

struct STradeSignal
{
   ENUM_TRADE_DIRECTION direction;
   double               entryPrice;
   double               stopLoss;
   double               takeProfit;
   double               lotSize;
   ENUM_STRATEGY_TYPE   sourceStrategy;
   bool                 isValid;
};

struct SStateResult
{
   ENUM_MARKET_STATE state;
   double            confidence;
   double            adxValue;
   double            trendScore;
   double            rangeScore;
};

#endif
