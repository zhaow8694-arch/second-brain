"""亏损原因分析脚本"""
import json

with open('guardian_earth_state_core.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

hist = d['trade_executor']['position_history']

# 分离
closes = [t for t in hist if 'pnl' in t]
opens = [t for t in hist if 'exit_price' not in t]

print(f'总记录: {len(hist)} | 平仓: {len(closes)} | 开仓(未平): {len(opens)}')
print()

# 分类统计
total_pnl = 0
by_reason = {}
win_count = 0
loss_count = 0

for c in closes:
    pnl = c.get('pnl', 0)
    total_pnl += pnl
    reason = c.get('reason', '?')
    if reason not in by_reason:
        by_reason[reason] = {'count': 0, 'pnl': 0, 'wins': 0, 'losses': 0}
    by_reason[reason]['count'] += 1
    by_reason[reason]['pnl'] += pnl
    if pnl >= 0:
        by_reason[reason]['wins'] += 1
        win_count += 1
    else:
        by_reason[reason]['losses'] += 1
        loss_count += 1

total_trades = win_count + loss_count
win_rate = win_count / total_trades * 100 if total_trades > 0 else 0

print(f'总平仓盈亏: {total_pnl:+.2f} USDT')
print(f'盈利笔: {win_count} | 亏损笔: {loss_count} | 胜率: {win_rate:.1f}%')
print()
print('按退出原因统计:')
print(f'  {"原因":25s} | {"笔数":>4s} | {"盈":>3s} | {"亏":>3s} | {"PnL":>8s} | {"均笔":>8s}')
print('  ' + '-' * 65)
for reason, stats in sorted(by_reason.items(), key=lambda x: x[1]['pnl']):
    avg = stats['pnl'] / stats['count']
    print(f'  {reason:25s} | {stats["count"]:4d} | {stats["wins"]:3d} | {stats["losses"]:3d} | {stats["pnl"]:+8.2f} | {avg:+8.2f}')

# 手续费估算
print()
print('费用估算:')
total_value = 0
for c in closes:
    sz = c.get('size', 0)
    # 用exit价格估价值
    ep = c.get('exit_price', c.get('entry_price', 0))
    total_value += abs(float(ep) * float(sz))
# Binance futures 市价单费率: taker 0.03%, maker 0.02%
# 市价开仓+市价平仓 = 0.03% * 2 = 0.06% 每笔完整
est_fees_taker = total_value * 0.0003 * 2
est_fees_limit = total_value * 0.0002 * 2  
print(f'  预估总交易量: {total_value:,.0f} USDT')
print(f'  预估手续费(市价): ~{est_fees_taker:.2f} USDT')
print(f'  预估手续费(限价): ~{est_fees_limit:.2f} USDT')

# 止损细节
print()
print('止损相关平仓详情:')
for c in closes:
    r = c.get('reason', '')
    if '止损' in r:
        ep = c.get('exit_price', 0) or c.get('entry_price', 0) or 0
        print(f'  {c["symbol"]:6s} {c["direction"]:5s} 出场:{ep:.4f} PnL:{c["pnl"]:+.2f}  {r}')

# 累计手续费 vs 实际亏损
print()
print('=== 核心分析 ===')
print(f'累计平仓盈亏: {total_pnl:+.2f} USDT')
print(f'预估手续费(市价): ~{est_fees_taker:.2f} USDT')
print(f'纯交易盈亏(扣除手续费): ~{total_pnl - est_fees_taker:+.2f} USDT')
# 哪类退出亏损最大
if by_reason:
    worst = min(by_reason.items(), key=lambda x: x[1]['pnl'])
    print(f'最大亏损来源: "{worst[0]}" ({worst[1]["count"]}笔, 总亏{worst[1]["pnl"]:+.2f})')
