import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.core.market.collector.base import DataType, BaseCollector
from src.core.market.collector.binance import BinanceCollector
from src.core.market.collector.mt4 import MT4Collector
from src.core.market.data import MarketData, KlineData, TickData, TradeData
from src.core.alert.alert import Alert, AlertLevel, AlertStatus
from src.core.alert.alert_manager import AlertManager
from src.core.alert.alert_rule import AlertRule, AlertRuleType, AlertRuleOperator
from src.core.alert.alert_rule_manager import AlertRuleManager
from src.core.alert.alert_rule_engine import AlertRuleEngine
from src.core.storage.storage import StorageManager
from src.core.storage.database import DatabaseManager
from src.core.storage.cache import CacheManager
from src.core.storage.file import FileManager

@pytest.fixture
def config():
    """测试配置"""
    return {
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'data_dir': 'data/test',
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        },
        'cache': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        }
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
def storage_manager(config):
    """创建存储管理器实例"""
    return StorageManager(config)

@pytest.fixture
def alert_manager():
    """创建告警管理器实例"""
    return AlertManager()

@pytest.fixture
def alert_rule_manager():
    """创建告警规则管理器实例"""
    return AlertRuleManager()

@pytest.fixture
def alert_rule_engine():
    """创建告警规则引擎实例"""
    return AlertRuleEngine()

@pytest.fixture
def sample_market_data():
    """创建示例市场数据"""
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
def sample_alert_rule():
    """创建示例告警规则"""
    return AlertRule(
        id="test_rule_1",
        name="Test Rule",
        description="Test rule description",
        type=AlertRuleType.PRICE,
        operator=AlertRuleOperator.GREATER_THAN,
        threshold=35000.00,
        symbol="BTCUSDT",
        level=AlertLevel.WARNING,
        enabled=True
    )

class TestDataCollectionAndStorage:
    """数据采集和存储集成测试"""
    
    @pytest.mark.asyncio
    async def test_binance_data_collection_and_storage(self, binance_collector, storage_manager):
        """测试Binance数据采集和存储"""
        # 连接数据源
        await binance_collector.connect()
        
        # 订阅数据
        await binance_collector.subscribe('BTCUSDT', DataType.KLINE)
        
        # 获取历史数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        klines = await binance_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        
        # 保存数据
        for kline in klines:
            assert storage_manager.save_market_data(kline)
        
        # 从存储中获取数据
        stored_data = storage_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        
        # 验证数据
        assert len(stored_data) > 0
        assert isinstance(stored_data[0], KlineData)
        assert stored_data[0].symbol == 'BTCUSDT'
    
    @pytest.mark.asyncio
    async def test_mt4_data_collection_and_storage(self, mt4_collector, storage_manager, tmp_path):
        """测试MT4数据采集和存储"""
        # 设置数据目录
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例数据文件
        kline_file = data_dir / 'BTCUSDT_kline.csv'
        kline_file.write_text('timestamp,open,high,low,close,volume,interval\n'
                            '2024-01-01 00:00:00,35000.00,36000.00,34000.00,35500.00,100.00,1h')
        
        # 连接数据源
        await mt4_collector.connect()
        
        # 订阅数据
        await mt4_collector.subscribe('BTCUSDT', DataType.KLINE)
        
        # 获取历史数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        klines = await mt4_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        
        # 保存数据
        for kline in klines:
            assert storage_manager.save_market_data(kline)
        
        # 从存储中获取数据
        stored_data = storage_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        
        # 验证数据
        assert len(stored_data) > 0
        assert isinstance(stored_data[0], KlineData)
        assert stored_data[0].symbol == 'BTCUSDT'

class TestAlertRuleProcessing:
    """告警规则处理集成测试"""
    
    def test_alert_rule_processing(self, alert_rule_manager, alert_rule_engine, storage_manager, sample_alert_rule):
        """测试告警规则处理流程"""
        # 添加告警规则
        alert_rule_manager.add_rule(sample_alert_rule)
        
        # 获取市场数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        market_data = storage_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        
        # 评估规则
        for data in market_data:
            if alert_rule_engine.evaluate_rule(sample_alert_rule, data.close_price):
                # 创建告警
                alert = Alert(
                    id=f"alert_{data.timestamp.timestamp()}",
                    level=sample_alert_rule.level,
                    message=f"Price {data.close_price} {sample_alert_rule.operator.value} {sample_alert_rule.threshold}",
                    source="alert_rule_engine",
                    timestamp=data.timestamp,
                    status=AlertStatus.ACTIVE
                )
                
                # 保存告警
                assert storage_manager.save_alert(alert)
        
        # 获取告警
        alerts = storage_manager.get_alerts(
            start_time=start_time,
            end_time=end_time
        )
        
        # 验证告警
        assert len(alerts) > 0
        assert isinstance(alerts[0], Alert)
        assert alerts[0].level == sample_alert_rule.level

class TestMultiSourceDataIntegration:
    """多数据源集成测试"""
    
    @pytest.mark.asyncio
    async def test_binance_and_mt4_data_integration(self, binance_collector, mt4_collector, storage_manager, tmp_path):
        """测试Binance和MT4数据集成"""
        # 设置MT4数据目录
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        mt4_collector.config['data_dir'] = str(data_dir)
        
        # 创建示例MT4数据文件
        kline_file = data_dir / 'BTCUSDT_kline.csv'
        kline_file.write_text('timestamp,open,high,low,close,volume,interval\n'
                            '2024-01-01 00:00:00,35000.00,36000.00,34000.00,35500.00,100.00,1h')
        
        # 连接数据源
        await binance_collector.connect()
        await mt4_collector.connect()
        
        # 获取Binance数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        binance_klines = await binance_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        
        # 获取MT4数据
        mt4_klines = await mt4_collector.get_historical_data(
            'BTCUSDT',
            DataType.KLINE,
            start_time,
            end_time,
            '1h'
        )
        
        # 保存数据
        for kline in binance_klines:
            assert storage_manager.save_market_data(kline)
        
        for kline in mt4_klines:
            assert storage_manager.save_market_data(kline)
        
        # 从存储中获取数据
        stored_data = storage_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        
        # 验证数据
        assert len(stored_data) > 0
        assert isinstance(stored_data[0], KlineData)
        assert stored_data[0].symbol == 'BTCUSDT'

class TestAlertAndStorageIntegration:
    """告警和存储集成测试"""
    
    def test_alert_and_storage_integration(self, alert_manager, storage_manager, sample_alert):
        """测试告警和存储集成"""
        # 保存告警
        assert storage_manager.save_alert(sample_alert)
        
        # 获取告警
        alerts = storage_manager.get_alerts(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        
        # 验证告警
        assert len(alerts) > 0
        assert isinstance(alerts[0], Alert)
        assert alerts[0].id == sample_alert.id
        
        # 更新告警状态
        alerts[0].status = AlertStatus.ACKNOWLEDGED
        assert storage_manager.save_alert(alerts[0])
        
        # 验证告警状态更新
        updated_alerts = storage_manager.get_alerts(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        assert updated_alerts[0].status == AlertStatus.ACKNOWLEDGED 