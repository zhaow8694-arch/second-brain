#ifndef ACCOUNT_SCALE_MQH
#define ACCOUNT_SCALE_MQH

#include "OmniTypes.mqh"

class COmniAccountScale
{
private:
   ENUM_OMNI_ACCOUNT_SCALE requestedMode;
   ENUM_OMNI_ACCOUNT_SCALE detectedMode;
   double scale;
   string reason;

   string Upper(const string value)
   {
      string result = value;
      StringToUpper(result);
      return result;
   }

public:
   COmniAccountScale()
   {
      requestedMode = OMNI_SCALE_AUTO;
      detectedMode = OMNI_SCALE_STANDARD;
      scale = 1.0;
      reason = "not initialized";
   }

   bool Init(const ENUM_OMNI_ACCOUNT_SCALE mode, const double customScale)
   {
      requestedMode = mode;
      detectedMode = mode;
      scale = 1.0;
      reason = "standard account";

      if(mode == OMNI_SCALE_STANDARD)
      {
         detectedMode = OMNI_SCALE_STANDARD;
         scale = 1.0;
         reason = "manual standard";
         return true;
      }

      if(mode == OMNI_SCALE_CENT_100X_BALANCE)
      {
         detectedMode = OMNI_SCALE_CENT_100X_BALANCE;
         scale = 100.0;
         reason = "manual CENT_100X balance";
         return true;
      }

      if(mode == OMNI_SCALE_CUSTOM)
      {
         detectedMode = OMNI_SCALE_CUSTOM;
         scale = MathMax(1.0, customScale);
         reason = "manual custom scale";
         return true;
      }

      string currency = Upper(AccountInfoString(ACCOUNT_CURRENCY));
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);

      if(StringFind(currency, "USC") >= 0 || StringFind(currency, "CENT") >= 0)
      {
         detectedMode = OMNI_SCALE_CENT_100X_BALANCE;
         scale = 100.0;
         reason = "currency contains USC/CENT";
         return true;
      }

      if(balance >= 5000.0 && MathMod(balance, 100.0) == 0.0)
      {
         detectedMode = OMNI_SCALE_CENT_100X_BALANCE;
         scale = 100.0;
         reason = "AUTO balance looks cent-scaled";
         return true;
      }

      detectedMode = OMNI_SCALE_STANDARD;
      scale = 1.0;
      reason = "AUTO standard fallback";
      return true;
   }

   double EffectiveBalance()
   {
      return AccountInfoDouble(ACCOUNT_BALANCE) / scale;
   }

   double EffectiveEquity()
   {
      return AccountInfoDouble(ACCOUNT_EQUITY) / scale;
   }

   double ToBrokerMoney(const double effectiveMoney)
   {
      return effectiveMoney * scale;
   }

   double FromBrokerMoney(const double brokerMoney)
   {
      return brokerMoney / scale;
   }

   double Scale()
   {
      return scale;
   }

   bool IsCentLike()
   {
      return (scale > 1.0);
   }

   string Summary()
   {
      return "scale=" + DoubleToString(scale, 2) +
             ", reason=" + reason +
             ", balanceEffective=" + DoubleToString(EffectiveBalance(), 2) +
             ", equityEffective=" + DoubleToString(EffectiveEquity(), 2);
   }
};

#endif
