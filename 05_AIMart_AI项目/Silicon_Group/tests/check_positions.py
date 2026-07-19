import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from core.financial_gateway import _FuturesClient
client = _FuturesClient()
balance = client.fetch_balance()
print(f'总钱包余额: {balance["total"].get("USDT", 0)} USDT')
positions = client.fetch_positions()
if positions:
    for p in positions:
        print(f"{p['symbol']}: {p['quantity']} {p['direction']} 入场={p['entry_price']} 未实现盈亏={p['unrealized_pnl']} USDT")
else:
    print('无持仓')
