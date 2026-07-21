import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from execution.execution_manager import ExecutionManager
from execution.binance_executor import BinanceExecutor
from execution.mt4_executor import MT4Executor
from risk.advanced_risk_controller import AdvancedRiskController
from monitor.trade_monitor import TradeMonitor

async def test_risk_control():
    """测试风险控制"""
    print("\n测试风险控制...")
    
    # 创建风险控制器
    risk_controller = AdvancedRiskController(
        max_position_size=0.5,  # 最大持仓规模为账户50%
        max_drawdown=0.1,  # 最大回撤10%
        risk_per_trade=0.02,  # 每笔交易风险2%
        trailing_stop_multiplier=2.0,  # 追踪止损倍数
        max_positions_per_symbol=3,  # 每个交易对最多3个持仓
        max_total_positions=10  # 总持仓限制10个
    )
    
    # 测试持仓规模计算
    position_size = await risk_controller.calculate_position_size(
        symbol='BTCUSDT',
        account_balance=10000,
        risk_per_trade=0.02,
        current_price=27000
    )
    print(f"\n计算持仓规模: {position_size} BTC")
    
    # 测试止损计算
    stop_loss = await risk_controller.calculate_stop_loss(
        symbol='BTCUSDT',
        direction='buy',
        entry_price=27000,
        atr_value=500
    )
    print(f"计算止损价格: {stop_loss} USDT")
    
    # 测试风险限制检查
    account_info = {
        'balance': 10000,
        'equity': 9500,
        'margin': 2000,
        'free_margin': 7500
    }
    
    new_position = {
        'symbol': 'BTCUSDT',
        'volume': 0.1,
        'entry_price': 27000
    }
    
    risk_check = await risk_controller.check_risk_limits(account_info, new_position)
    print(f"风险限制检查结果: {'通过' if risk_check else '未通过'}")
    
    # 测试风险指标计算
    # 添加一些模拟交易记录
    for i in range(10):
        risk_controller.add_trade_history({
            'symbol': 'BTCUSDT',
            'profit': 100 if i % 2 == 0 else -50,
            'volume': 0.1,
            'entry_price': 27000,
            'exit_price': 27100 if i % 2 == 0 else 26950
        })
        
    risk_metrics = await risk_controller.calculate_risk_metrics()
    print("\n风险指标:")
    for key, value in risk_metrics.items():
        print(f"{key}: {value}")
        
async def test_monitor():
    """测试交易监控"""
    print("\n测试交易监控...")
    
    # 创建执行管理器
    manager = ExecutionManager()
    
    # 添加执行器
    manager.add_executor('binance', BinanceExecutor(
        api_key=os.getenv('BINANCE_API_KEY'),
        api_secret=os.getenv('BINANCE_API_SECRET'),
        test_mode=True
    ))
    
    manager.add_executor('mt4', MT4Executor(
        api_key=os.getenv('MT4_API_KEY'),
        api_secret=os.getenv('MT4_API_SECRET'),
        test_mode=True
    ))
    
    # 创建风险控制器
    risk_controller = AdvancedRiskController(
        max_position_size=0.5,
        max_drawdown=0.1,
        risk_per_trade=0.02,
        trailing_stop_multiplier=2.0
    )
    
    # 创建监控器
    monitor = TradeMonitor(
        execution_manager=manager,
        risk_controller=risk_controller,
        check_interval=1.0
    )
    
    # 启动监控
    print("启动监控...")
    monitor_task = asyncio.create_task(monitor.start())
    
    # 模拟一些交易活动
    try:
        # 等待监控器启动
        await asyncio.sleep(2)
        
        # 模拟开仓
        print("\n模拟开仓...")
        result = await manager.execute_signal({
            'symbol': 'BTCUSDT',
            'direction': 'buy',
            'position_size': 0.1,
            'metadata': {
                'market_data': {
                    'close': 27000
                }
            },
            'stop_loss': 26500,
            'take_profit': 28000,
            'should_lock': False,
            'trading_suggestions': {
                'action': 'open',
                'sub_positions': [{
                    'size': 0.1,
                    'price_offset': 0
                }]
            }
        }, 'binance')
        print(f"开仓结果: {result}")
        
        # 等待一段时间让监控器收集数据
        print("\n等待监控数据收集...")
        await asyncio.sleep(5)
        
        # 模拟市场波动
        print("\n模拟市场波动...")
        # TODO: 实现市场数据模拟
        
        # 等待报告生成
        print("\n等待报告生成...")
        await asyncio.sleep(60)
        
    finally:
        # 停止监控
        print("\n停止监控...")
        await monitor.stop()
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
            
async def main():
    # 加载环境变量
    load_dotenv()
    
    # 运行测试
    await test_risk_control()
    await test_monitor()
    
if __name__ == "__main__":
    asyncio.run(main()) 