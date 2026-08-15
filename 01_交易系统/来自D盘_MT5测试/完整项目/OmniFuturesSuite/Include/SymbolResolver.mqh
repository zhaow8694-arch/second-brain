#ifndef SYMBOL_RESOLVER_MQH
#define SYMBOL_RESOLVER_MQH

#include "OmniTypes.mqh"
#include "SymbolProfile.mqh"

class COmniSymbolResolver
{
private:
   string Upper(const string value)
   {
      string result = value;
      StringToUpper(result);
      return result;
   }

   bool IsUsableSymbol(const string symbol)
   {
      if(symbol == "") return false;
      if(!SymbolSelect(symbol, true)) return false;
      long tradeMode = SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
      return (tradeMode != SYMBOL_TRADE_MODE_DISABLED);
   }

   bool CandidateMatches(const ENUM_OMNI_PRODUCT product, const string symbol)
   {
      string upper = Upper(symbol);

      if(product == OMNI_GOLD)
         return (StringFind(upper, "XAUUSD") >= 0 || StringFind(upper, "GOLD") >= 0);

      if(product == OMNI_SPX500)
         return (StringFind(upper, "SPX500") >= 0 || StringFind(upper, "SP500") >= 0 ||
                 StringFind(upper, "US500") >= 0 || StringFind(upper, "USSPX") >= 0);

      if(product == OMNI_A50)
         return (StringFind(upper, "A50") >= 0 || StringFind(upper, "CHINA50") >= 0 ||
                 StringFind(upper, "CN50") >= 0);

      if(product == OMNI_USOIL)
         return (StringFind(upper, "USOIL") >= 0 || StringFind(upper, "WTI") >= 0 ||
                 StringFind(upper, "XTIUSD") >= 0 || StringFind(upper, "OIL") >= 0);

      return false;
   }

   bool AllowsAutoFallback(const string inputSymbol)
   {
      return (inputSymbol == "" || Upper(inputSymbol) == "AUTO");
   }

   string FindByScan(const ENUM_OMNI_PRODUCT product, const bool selectedOnly)
   {
      int total = SymbolsTotal(selectedOnly);
      for(int i = 0; i < total; i++)
      {
         string symbol = SymbolName(i, selectedOnly);
         if(CandidateMatches(product, symbol) && IsUsableSymbol(symbol))
            return symbol;
      }
      return "";
   }

   bool ResolveOne(SOmniSymbol &item, const ENUM_OMNI_PRODUCT product, const string inputSymbol)
   {
      item.product = product;
      item.logicalName = OmniProductName(product);
      item.inputSymbol = inputSymbol;
      item.resolvedSymbol = "";
      item.enabled = false;
      item.disabledReason = "";
      item.profile = BuildOmniProfile(product);
      item.lastH1BarTime = 0;
      item.lastH4BarTime = 0;

      string upperInput = Upper(inputSymbol);
      if(upperInput == "OFF" || upperInput == "NONE" || upperInput == "DISABLED")
      {
         item.disabledReason = "disabled by input";
         return false;
      }

      if(IsUsableSymbol(inputSymbol))
      {
         item.resolvedSymbol = inputSymbol;
         item.enabled = true;
         return true;
      }

      if(CandidateMatches(product, _Symbol) && IsUsableSymbol(_Symbol))
      {
         item.resolvedSymbol = _Symbol;
         item.enabled = true;
         return true;
      }

      string found = FindByScan(product, false);
      if(found == "")
         found = FindByScan(product, true);

      if(found != "")
      {
         item.resolvedSymbol = found;
         item.enabled = true;
         return true;
      }

      item.disabledReason = "Cannot resolve tradable symbol for " + item.logicalName +
                            " from input " + inputSymbol + " or broker symbol scan";
      return false;
   }

public:
   bool ResolveAll(SOmniSymbol &symbols[],
                   const string goldSymbol,
                   const string spxSymbol,
                   const string a50Symbol,
                   const string oilSymbol)
   {
      ArrayResize(symbols, OMNI_PRODUCT_COUNT);
      ResolveOne(symbols[OMNI_GOLD], OMNI_GOLD, goldSymbol);
      ResolveOne(symbols[OMNI_SPX500], OMNI_SPX500, spxSymbol);
      ResolveOne(symbols[OMNI_A50], OMNI_A50, a50Symbol);
      ResolveOne(symbols[OMNI_USOIL], OMNI_USOIL, oilSymbol);

      bool anyEnabled = false;
      for(int i = 0; i < OMNI_PRODUCT_COUNT; i++)
      {
         if(symbols[i].enabled)
            anyEnabled = true;
      }
      return anyEnabled;
   }
};

#endif
