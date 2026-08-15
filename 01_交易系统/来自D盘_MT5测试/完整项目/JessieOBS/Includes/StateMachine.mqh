#ifndef _STATEMACHINE_MQH_
#define _STATEMACHINE_MQH_

#include "Defines.mqh"

class CStateMachine
{
private:
   ENUM_MARKET_STATE m_currentState;
   ENUM_MARKET_STATE m_lastConfirmedState;
   datetime          m_stateStartTime;
   datetime          m_lastSwitchTime;
   int               m_minSwitchBars;
   double            m_confidenceReq;
   int               m_barsInCurrentState;
   int               m_pendingSwitchCount;
   ENUM_MARKET_STATE m_pendingState;
   datetime          m_lastBarTime;

public:
   CStateMachine()
   {
      m_currentState       = MARKET_STATE_UNKNOWN;
      m_lastConfirmedState  = MARKET_STATE_UNKNOWN;
      m_stateStartTime     = 0;
      m_lastSwitchTime     = 0;
      m_minSwitchBars      = 8;
      m_confidenceReq      = 75.0;
      m_barsInCurrentState = 0;
      m_pendingSwitchCount = 0;
      m_pendingState       = MARKET_STATE_UNKNOWN;
      m_lastBarTime        = 0;
   }

   void Init(int minBars, double confReq)
   {
      m_minSwitchBars  = minBars;
      m_confidenceReq  = confReq;
      m_currentState   = MARKET_STATE_UNKNOWN;
      m_stateStartTime = TimeCurrent();
      m_lastBarTime    = 0;
   }

   ENUM_MARKET_STATE GetState() const { return m_currentState; }

   bool IsNewBar()
   {
      datetime curBar = iTime(_Symbol, _Period, 0);
      if(curBar != m_lastBarTime && curBar > 0)
      {
         m_lastBarTime = curBar;
         return true;
      }
      return false;
   }

   void UpdateState(SStateResult &detection)
   {
      if(m_currentState == MARKET_STATE_UNKNOWN)
      {
         m_currentState       = detection.state;
         m_lastConfirmedState  = detection.state;
         m_stateStartTime     = TimeCurrent();
         m_lastSwitchTime     = TimeCurrent();
         m_barsInCurrentState = 0;
         m_pendingSwitchCount = 0;
         m_pendingState       = MARKET_STATE_UNKNOWN;
         return;
      }

      m_barsInCurrentState++;

      if(detection.state == m_currentState)
      {
         m_pendingSwitchCount = 0;
         m_pendingState       = MARKET_STATE_UNKNOWN;
         return;
      }

      if(m_pendingState != detection.state)
      {
         m_pendingState       = detection.state;
         m_pendingSwitchCount = 1;
         return;
      }

      m_pendingSwitchCount++;

      if(m_pendingSwitchCount >= m_minSwitchBars && detection.confidence >= m_confidenceReq)
      {
         if(m_barsInCurrentState >= m_minSwitchBars)
         {
            m_lastConfirmedState = m_currentState;
            m_currentState       = detection.state;
            m_stateStartTime     = TimeCurrent();
            m_lastSwitchTime     = TimeCurrent();
            m_barsInCurrentState = 0;
            m_pendingSwitchCount = 0;
            m_pendingState       = MARKET_STATE_UNKNOWN;
         }
      }
   }

   int GetBarsInState() const { return m_barsInCurrentState; }

   datetime GetStateStartTime() const { return m_stateStartTime; }

   datetime GetLastSwitchTime() const { return m_lastSwitchTime; }

   string GetStateName() const
   {
      switch(m_currentState)
      {
         case MARKET_STATE_TRENDING: return "TRENDING";
         case MARKET_STATE_RANGING:  return "RANGING";
         case MARKET_STATE_UNKNOWN:  return "UNKNOWN";
      }
      return "ERROR";
   }
};

#endif
