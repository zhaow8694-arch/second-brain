import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.core.market.collector.base import DataType, BaseCollector
from src.core.market.collector.binance import BinanceCollector
from src.core.market.collector.mt4 import MT4Collector
from src.core.market.data import MarketData, KlineData, TickData, TradeData
from src.data.market_data_manager import MarketDataManager
from src.execution.execution_manager import ExecutionManager
from src.risk.risk_monitor import RiskMonitor

@pytest.fixture
def config():
    """测试配置"""
    return {
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'data_dir': 'data/mt4'
    }

@pytest.fixture
def mock_client():
    """模拟Binance客户端"""
    mock = AsyncMock()
    mock.get_klines.return_value = [
        [1625097600000, "35000.00", "36000.00", "34000.00", "35500.00", "100.00", 1625097900000, "1000.00", 10, "50.00", "50.00", "0"]
    ]
    mock.get_ticker.return_value = {
        'symbol': 'BTCUSDT',
        'lastPrice': '35500.00',
        'bidPrice': '35400.00',
        'askPrice': '35600.00',
        'volume': '1000.00'
    }
    mock.get_recent_trades.return_value = [
        {
            'id': 123456,
            'price': '35500.00',
            'qty': '1.00',
            'time': 1625097600000,
            'isBuyerMaker': True
        }
    ]
    return mock

@pytest.fixture
def mock_socket_manager():
    """模拟WebSocket管理器"""
    mock = AsyncMock()
    mock.start.return_value = True
    mock.stop.return_value = True
    return mock

@pytest.fixture
def binance_collector(config, mock_client, mock_socket_manager):
    """创建Binance数据采集器实例"""
    with patch('src.core.market.collector.binance.Client', return_value=mock_client), \
         patch('src.core.market.collector.binance.BinanceSocketManager', return_value=mock_socket_manager):
        collector = BinanceCollector(config)
        return collector

@pytest.fixture
def mt4_collector(config):
    """创建MT4数据采集器实例"""
    collector = MT4Collector(config)
    return collector

@pytest.fixture
def sample_data():
    """创建示例数据"""
    return {
        'kline': KlineData(
            symbol='BTCUSDT',
            timestamp=datetime.now(),
            open_price=35000.00,
            high_price=36000.00,
            low_price=34000.00,
            close_price=35500.00,
            volume=100.00,
            interval='1h'
        ),
        'tick': TickData(
            symbol='BTCUSDT',
            timestamp=datetime.now(),
            last_price=35500.00,
            bid_price=35400.00,
            ask_price=35600.00,
            bid_volume=10.00,
            ask_volume=5.00,
            volume_24h=1000.00
        ),
        'trade': TradeData(
            symbol='BTCUSDT',
            timestamp=datetime.now(),
            price=35500.00,
            volume=1.00,
            side='buy',
            order_id='123456'
        )
    }

@pytest.fixture
async def market_data_manager():
    """创建市场数据管理器实例"""
    manager = MarketDataManager()
    await manager.initialize()
    return manager

@pytest.fixture
async def execution_manager():
    """创建执行管理器实例"""
    manager = ExecutionManager()
    await manager.initialize()
    return manager

@pytest.fixture
async def risk_monitor():
    """创建风险监控器实例"""
    monitor = RiskMonitor()
    await monitor.initialize()
    return monitor

class TestBaseCollector:
    """基础采集器测试"""
    
    @pytest.mark.asyncio
    async def test_base_collector_interface(self):
        """测试基础采集器接口"""
        collector = BaseCollector({})
        assert hasattr(collector, 'connect')
        assert hasattr(collector, 'disconnect')
        assert hasattr(collector, 'subscribe')
        assert hasattr(collector, 'unsubscribe')
        assert hasattr(collector, 'get_historical_data')
        assert hasattr(collector, 'add_subscriber')
        assert hasattr(collector, 'remove_subscriber')

class TestBinanceCollector:
    """Binance数据采集器测试"""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, binance_collector):
        """测试成功连接"""
        assert await binance_collector.connect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, config):
        """测试连接失败"""
        with patch('src.core.market.collector.binance.Client', side_effect=Exception("Connection failed")):
            collector = BinanceCollector(config)
            assert not await collector.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, binance_collector):
        """测试成功断开连接"""
        await binance_collector.connect()
        assert await binance_collector.disconnect()
    
    @pytest.mark.asyncio
    async def test_subscribe_kline(self, binance_collector):
        """测试订阅K线数据"""
        await binance_collector.connect()
        assert await binance_collector.subscribe('BTCUSDT', DataType.KLINE)
    
    @pytest.mark.asyncio
    async def test_subscribe_tick(self, binance_collector):
        """测试订阅实时行情数据"""
        await binance_collector.connect()
        assert await binance_collector.subscribe('BTCUSDT', DataType.TICK)
    
    @pytest.mark.asyncio
    async def test_subscribe_trade(self, binance_collector):
        """测试订阅成交记录数据"""
        await binance_collector.connect()
        assert await binance_collector.subscribe('BTCUSDT', DataType.TRADE)
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, binance_collector):
        """测试取消订阅"""
        await binance_collector.connect()
        await binance_collector.subscribe('BTCUSDT', DataType.KLINE)
        assert await binance_collector.unsubscribe('BTCUSDT', DataType.KLINE)
    
    @pytest.mark.asyncio
    async def test_get_historical_klines(self, binance_collector):
        """测试获取历史K线数据"""
        await binance_collector.connect()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        klines = await binance_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        assert len(klines) > 0
        assert isinstance(klines[0], KlineData)
    
    @pytest.mark.asyncio
    async def test_get_historical_trades(self, binance_collector):
        """测试获取历史成交记录"""
        await binance_collector.connect()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        trades = await binance_collector.get_historical_data(
            'BTCUSDT',
            DataType.TRADE,
            start_time,
            end_time
        )
        assert len(trades) > 0
        assert isinstance(trades[0], TradeData)

class TestMT4Collector:
    """MT4数据采集器测试"""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mt4_collector):
        """测试成功连接"""
        assert await mt4_collector.connect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, config):
        """测试连接失败"""
        config['data_dir'] = '/nonexistent/dir'
        collector = MT4Collector(config)
        assert not await collector.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, mt4_collector):
        """测试成功断开连接"""
        await mt4_collector.connect()
        assert await mt4_collector.disconnect()
    
    @pytest.mark.asyncio
    async def test_subscribe_kline(self, mt4_collector, tmp_path):
        """测试订阅K线数据"""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        kline_file = data_dir / 'BTCUSDT_kline.csv'
        kline_file.write_text('timestamp,open,high,low,close,volume,interval\n'
                            '2024-01-01 00:00:00,35000.00,36000.00,34000.00,35500.00,100.00,1h')
        
        await mt4_collector.connect()
        assert await mt4_collector.subscribe('BTCUSDT', DataType.KLINE)
    
    @pytest.mark.asyncio
    async def test_subscribe_tick(self, mt4_collector, tmp_path):
        """测试订阅实时行情数据"""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        tick_file = data_dir / 'BTCUSDT_tick.csv'
        tick_file.write_text('timestamp,last,bid,ask,bid_volume,ask_volume,volume_24h\n'
                           '2024-01-01 00:00:00,35500.00,35400.00,35600.00,10.00,5.00,1000.00')
        
        await mt4_collector.connect()
        assert await mt4_collector.subscribe('BTCUSDT', DataType.TICK)
    
    @pytest.mark.asyncio
    async def test_subscribe_trade(self, mt4_collector, tmp_path):
        """测试订阅成交记录数据"""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        trade_file = data_dir / 'BTCUSDT_trade.csv'
        trade_file.write_text('timestamp,price,volume,side,order_id\n'
                            '2024-01-01 00:00:00,35500.00,1.00,buy,123456')
        
        await mt4_collector.connect()
        assert await mt4_collector.subscribe('BTCUSDT', DataType.TRADE)
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, mt4_collector):
        """测试取消订阅"""
        await mt4_collector.connect()
        await mt4_collector.subscribe('BTCUSDT', DataType.KLINE)
        assert await mt4_collector.unsubscribe('BTCUSDT', DataType.KLINE)
    
    @pytest.mark.asyncio
    async def test_get_historical_klines(self, mt4_collector, tmp_path):
        """测试获取历史K线数据"""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        kline_file = data_dir / 'BTCUSDT_kline.csv'
        kline_file.write_text('timestamp,open,high,low,close,volume,interval\n'
                            '2024-01-01 00:00:00,35000.00,36000.00,34000.00,35500.00,100.00,1h')
        
        await mt4_collector.connect()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        klines = await mt4_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        assert len(klines) > 0
        assert isinstance(klines[0], KlineData)
    
    @pytest.mark.asyncio
    async def test_get_historical_trades(self, mt4_collector, tmp_path):
        """测试获取历史成交记录"""
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        trade_file = data_dir / 'BTCUSDT_trade.csv'
        trade_file.write_text('timestamp,price,volume,side,order_id\n'
                            '2024-01-01 00:00:00,35500.00,1.00,buy,123456')
        
        await mt4_collector.connect()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        trades = await mt4_collector.get_historical_data(
            'BTCUSDT',
            DataType.TRADE,
            start_time,
            end_time
        )
        assert len(trades) > 0
        assert isinstance(trades[0], TradeData)

async def test_market_data_management(market_data_manager):
    """测试市场数据管理"""
    # 订阅数据
    await market_data_manager.subscribe('BTCUSDT')
    
    # 获取历史数据
    data = await market_data_manager.get_historical_data(
        symbol='BTCUSDT',
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now()
    )
    assert len(data) > 0
    
    # 测试实时数据更新
    async def data_callback(data):
        assert data['symbol'] == 'BTCUSDT'
        assert 'price' in data
        assert 'volume' in data
    
    market_data_manager.add_callback(data_callback)
    await asyncio.sleep(1)  # 等待数据更新

async def test_execution_system(execution_manager):
    """测试执行系统"""
    # 测试订单执行
    order = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'type': 'market',
        'quantity': 0.001
    }
    
    result = await execution_manager.execute_order(order)
    assert result['status'] in ['filled', 'partially_filled']
    
    # 测试订单查询
    order_status = await execution_manager.get_order_status(result['order_id'])
    assert order_status['status'] in ['filled', 'partially_filled', 'open']

async def test_risk_monitoring(risk_monitor):
    """测试风险监控"""
    # 测试风险指标计算
    risk_metrics = await risk_monitor.calculate_risk_metrics()
    assert 'position_risk' in risk_metrics
    assert 'market_risk' in risk_metrics
    assert 'liquidity_risk' in risk_metrics
    
    # 测试风险限制检查
    position = {
        'symbol': 'BTCUSDT',
        'size': 0.1,
        'entry_price': 50000
    }
    
    risk_check = await risk_monitor.check_risk_limits(position)
    assert isinstance(risk_check, bool)

async def main():
    """运行所有测试"""
    print("开始运行核心功能测试...")
    
    try:
        # 创建测试实例
        market_manager = await market_data_manager()
        exec_manager = await execution_manager()
        risk_monitor = await risk_monitor()
        
        # 运行测试
        print("\n测试市场数据管理...")
        await test_market_data_management(market_manager)
        print("✓ 市场数据管理测试通过")
        
        print("\n测试执行系统...")
        await test_execution_system(exec_manager)
        print("✓ 执行系统测试通过")
        
        print("\n测试风险监控...")
        await test_risk_monitoring(risk_monitor)
        print("✓ 风险监控测试通过")
        
        print("\n所有核心功能测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 