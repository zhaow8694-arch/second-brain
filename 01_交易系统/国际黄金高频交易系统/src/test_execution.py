import asyncio
import os
from dotenv import load_dotenv
from execution.execution_manager import ExecutionManager
from execution.binance_executor import BinanceExecutor
from execution.mt4_executor import MT4Executor
from signals.advanced_signal_generator import AdvancedSignalGenerator

async def test_binance_execution():
    """测试Binance合约交易执行"""
    print("\n测试Binance合约交易执行...")
    
    # 创建Binance执行器
    binance_executor = BinanceExecutor(
        api_key=os.getenv('BINANCE_API_KEY'),
        api_secret=os.getenv('BINANCE_API_SECRET'),
        test_mode=True  # 使用测试模式
    )
    
    # 获取账户信息
    account_info = await binance_executor.get_account_info()
    print("\nBinance账户信息:")
    print(f"总余额: {account_info['total_balance']} USDT")
    print(f"未实现盈亏: {account_info['unrealized_pnl']} USDT")
    print(f"可用余额: {account_info['available_balance']} USDT")
    
    # 测试开仓
    try:
        print("\n测试开仓...")
        order = await binance_executor.open_position(
            symbol='BTCUSDT',
            direction='buy',
            volume=0.001,
            stop_loss=25000,
            take_profit=28000
        )
        print(f"开仓结果: {order}")
    except Exception as e:
        print(f"开仓失败: {str(e)}")
        
    # 获取持仓
    positions = await binance_executor.get_positions('BTCUSDT')
    print("\n当前持仓:")
    for pos in positions:
        print(pos)
        
    # 如果有持仓，测试修改和平仓
    if positions:
        try:
            # 测试修改持仓
            print("\n测试修改持仓...")
            modify_result = await binance_executor.modify_position(
                position_id=positions[0]['ticket'],
                stop_loss=24000,
                take_profit=29000
            )
            print(f"修改结果: {modify_result}")
            
            # 测试平仓
            print("\n测试平仓...")
            close_result = await binance_executor.close_position(
                position_id=positions[0]['ticket']
            )
            print(f"平仓结果: {close_result}")
        except Exception as e:
            print(f"操作失败: {str(e)}")
            
async def test_mt4_execution():
    """测试MT4交易执行"""
    print("\n测试MT4交易执行...")
    
    # 创建MT4执行器
    mt4_executor = MT4Executor(
        api_key=os.getenv('MT4_API_KEY'),
        api_secret=os.getenv('MT4_API_SECRET'),
        test_mode=True
    )
    
    try:
        # 获取账户信息
        account_info = await mt4_executor.get_account_info()
        print("\nMT4账户信息:")
        print(f"余额: {account_info['balance']}")
        print(f"净值: {account_info['equity']}")
        print(f"可用保证金: {account_info['free_margin']}")
        
        # 测试开仓
        print("\n测试开仓...")
        order = await mt4_executor.open_position(
            symbol='XAUUSD',
            direction='buy',
            volume=0.01,
            stop_loss=1900,
            take_profit=1950
        )
        print(f"开仓结果: {order}")
        
        # 获取持仓
        positions = await mt4_executor.get_positions('XAUUSD')
        print("\n当前持仓:")
        for pos in positions:
            print(pos)
            
        # 如果有持仓，测试修改和平仓
        if positions:
            # 测试修改持仓
            print("\n测试修改持仓...")
            modify_result = await mt4_executor.modify_position(
                position_id=positions[0]['ticket'],
                stop_loss=1890,
                take_profit=1960
            )
            print(f"修改结果: {modify_result}")
            
            # 测试平仓
            print("\n测试平仓...")
            close_result = await mt4_executor.close_position(
                position_id=positions[0]['ticket']
            )
            print(f"平仓结果: {close_result}")
            
    except Exception as e:
        print(f"MT4操作失败: {str(e)}")
        
async def test_execution_manager():
    """测试交易执行管理器"""
    print("\n测试交易执行管理器...")
    
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
    
    # 创建信号生成器
    signal_generator = AdvancedSignalGenerator(os.getenv('DEEPSEEK_API_KEY'))
    
    try:
        # 生成交易信号
        print("\n生成交易信号...")
        signal = await signal_generator.generate_advanced_signal(
            symbol='BTCUSDT',
            account_balance=10000
        )
        
        # 执行交易信号
        print("\n执行交易信号...")
        result = await manager.execute_signal(signal, 'binance')
        print(f"执行结果: {result}")
        
        # 获取所有持仓
        print("\n获取所有持仓...")
        all_positions = await manager.get_all_positions()
        for executor_name, positions in all_positions.items():
            print(f"\n{executor_name}持仓:")
            for pos in positions:
                print(pos)
                
        # 获取所有账户信息
        print("\n获取所有账户信息...")
        all_account_info = await manager.get_all_account_info()
        for executor_name, info in all_account_info.items():
            print(f"\n{executor_name}账户信息:")
            print(info)
            
    except Exception as e:
        print(f"执行管理器测试失败: {str(e)}")
        
async def main():
    # 加载环境变量
    load_dotenv()
    
    # 运行测试
    await test_binance_execution()
    await test_mt4_execution()
    await test_execution_manager()
    
if __name__ == "__main__":
    asyncio.run(main()) 