#ifndef _MARKETSTATEDETECTOR_MQH_
#define _MARKETSTATEDETECTOR_MQH_

#include "Defines.mqh"

class CMarketStateDetector
{
private:
   int    m_adxHandle;
   int    m_maHandle;
   int    m_atrHandle;
   int    m_adxPeriod;
   int    m_maPeriod;
   int    m_atrPeriod;
   double m_adxTrendThreshold;
   double m_adxRangeThreshold;
   string m_symbol;
   ENUM_TIMEFRAMES m_timeframe;
   bool   m_initialized;

public:
   CMarketStateDetector()
   {
      m_adxHandle         = INVALID_HANDLE;
      m_maHandle          = INVALID_HANDLE;
      m_atrHandle         = INVALID_HANDLE;
      m_adxPeriod         = 14;
      m_maPeriod          = 200;
      m_atrPeriod         = 14;
      m_adxTrendThreshold = 25.0;
      m_adxRangeThreshold = 20.0;
      m_symbol            = "";
      m_timeframe         = PERIOD_CURRENT;
      m_initialized       = false;
   }

   bool Init(string symbol, ENUM_TIMEFRAMES tf,
             int adxPeriod, int maPeriod, int atrPeriod,
             double adxTrendThresh, double adxRangeThresh)
   {
      m_symbol            = symbol;
      m_timeframe         = tf;
      m_adxPeriod         = adxPeriod;
      m_maPeriod          = maPeriod;
      m_atrPeriod         = atrPeriod;
      m_adxTrendThreshold = adxTrendThresh;
      m_adxRangeThreshold = adxRangeThresh;

      m_adxHandle = iADX(m_symbol, m_timeframe, m_adxPeriod);
      m_maHandle  = iMA(m_symbol, m_timeframe, m_maPeriod, 0, MODE_SMA, PRICE_CLOSE);
      m_atrHandle = iATR(m_symbol, m_timeframe, m_atrPeriod);

      if(m_adxHandle == INVALID_HANDLE || m_maHandle == INVALID_HANDLE || m_atrHandle == INVALID_HANDLE)
      {
         Print("MarketStateDetector: Failed to create indicator handles");
         return false;
      }

      m_initialized = true;
      return true;
   }

   void Deinit()
   {
      if(m_adxHandle != INVALID_HANDLE) IndicatorRelease(m_adxHandle);
      if(m_maHandle  != INVALID_HANDLE) IndicatorRelease(m_maHandle);
      if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
      m_adxHandle = INVALID_HANDLE;
      m_maHandle  = INVALID_HANDLE;
      m_atrHandle = INVALID_HANDLE;
      m_initialized = false;
   }

   bool IsInitialized() const { return m_initialized; }

   SStateResult Detect()
   {
      SStateResult result;
      ZeroMemory(result);

      if(!m_initialized)
      {
         result.state      = MARKET_STATE_UNKNOWN;
         result.confidence = 0;
         return result;
      }

      double adx[1], diPlus[1], diMinus[1];
      double ma[1], atr[1];

      if(CopyBuffer(m_adxHandle, 0, 0, 1, adx) <= 0 ||
         CopyBuffer(m_adxHandle, 1, 0, 1, diPlus) <= 0 ||
         CopyBuffer(m_adxHandle, 2, 0, 1, diMinus) <= 0)
         return result;

      if(CopyBuffer(m_maHandle, 0, 0, 1, ma) <= 0 ||
         CopyBuffer(m_atrHandle, 0, 0, 1, atr) <= 0)
         return result;

      double atrBuffer[50];
      ArraySetAsSeries(atrBuffer, true);
      int atrCopied = CopyBuffer(m_atrHandle, 0, 0, 50, atrBuffer);
      if(atrCopied < 50)
      {
         for(int ai = 0; ai < 50; ai++) atrBuffer[ai] = atr[0];
      }

      double atrCurrent = atr[0];
      double atrAvg50   = 0;
      int validCount    = 0;
      for(int i = 0; i < 50; i++)
      {
         if(atrBuffer[i] > 0)
         {
            atrAvg50 += atrBuffer[i];
            validCount++;
         }
      }
      if(validCount > 0) atrAvg50 /= validCount;
      else atrAvg50 = atrCurrent;

      double atrRatio = (atrAvg50 > 0) ? (atrCurrent / atrAvg50) : 1.0;

      double closeBuf[1];
      if(CopyClose(m_symbol, m_timeframe, 1, 1, closeBuf) < 1)
         return result;
      double closePrice = closeBuf[0];
      double maDeviationPercent = (ma[0] > 0) ? (MathAbs(closePrice - ma[0]) / ma[0] * 100.0) : 0;

      double trendScore = 0;
      double rangeScore = 0;

      result.adxValue = adx[0];

      if(adx[0] > m_adxTrendThreshold)
         trendScore += 3.0;
      else if(adx[0] > m_adxRangeThreshold)
         trendScore += 1.5;
      else
         rangeScore += 3.0;

      if(adx[0] > m_adxRangeThreshold)
      {
         double diSpread = MathAbs(diPlus[0] - diMinus[0]);
         if(diSpread > 10)
            trendScore += 2.0;
         else if(diSpread > 5)
            trendScore += 1.0;
         else
            rangeScore += 1.0;
      }

      if(atrRatio > 1.3)
         trendScore += 2.0;
      else if(atrRatio < 0.7)
         rangeScore += 2.0;
      else if(atrRatio >= 0.85 && atrRatio <= 1.15)
         rangeScore += 1.0;

      if(maDeviationPercent > 5.0)
         trendScore += 2.0;
      else if(maDeviationPercent < 1.5)
         rangeScore += 2.0;
      else if(maDeviationPercent >= 1.5 && maDeviationPercent <= 3.0)
         rangeScore += 1.0;

      double diDiff = MathAbs(diPlus[0] - diMinus[0]);
      if(adx[0] > 20 && diDiff > 8)
         trendScore += 1.5;
      else if(diDiff < 4)
         rangeScore += 1.5;

      result.trendScore = trendScore;
      result.rangeScore = rangeScore;

      double totalScore = trendScore + rangeScore;
      if(totalScore < 0.1) totalScore = 1.0;

      if(trendScore > rangeScore)
      {
         result.state      = MARKET_STATE_TRENDING;
         result.confidence = (trendScore / totalScore) * 100.0;
      }
      else
      {
         result.state      = MARKET_STATE_RANGING;
         result.confidence = (rangeScore / totalScore) * 100.0;
      }

      if(result.confidence > 100.0) result.confidence = 100.0;

      double scoreGap = MathAbs(trendScore - rangeScore);
      if(scoreGap < 1.5)
      {
         result.state      = MARKET_STATE_UNKNOWN;
         result.confidence = (scoreGap / 1.5) * 50.0;
      }

      return result;
   }
};

#endif
