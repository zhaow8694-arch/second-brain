import pytest
import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.core.storage.storage import StorageManager
from src.core.storage.database import DatabaseManager
from src.core.storage.cache import CacheManager
from src.core.storage.file import FileManager
from src.core.market.data import MarketData, KlineData, TickData, TradeData
from src.core.alert.alert import Alert, AlertLevel, AlertStatus

@pytest.fixture
def storage_config():
    """测试存储配置"""
    return {
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
        },
        'file': {
            'base_dir': 'data/test'
        }
    }

@pytest.fixture
def storage_manager(storage_config):
    """创建存储管理器实例"""
    return StorageManager(storage_config)

@pytest.fixture
def database_manager(storage_config):
    """创建数据库管理器实例"""
    return DatabaseManager(storage_config['database'])

@pytest.fixture
def cache_manager(storage_config):
    """创建缓存管理器实例"""
    return CacheManager(storage_config['cache'])

@pytest.fixture
def file_manager(storage_config):
    """创建文件管理器实例"""
    return FileManager(storage_config['file'])

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
def sample_alert():
    """创建示例告警"""
    return Alert(
        id="test_alert_1",
        level=AlertLevel.WARNING,
        message="Test alert message",
        source="test_source",
        timestamp=datetime.now(),
        status=AlertStatus.ACTIVE
    )

class TestStorageManager:
    """存储管理器测试"""
    
    def test_init(self, storage_manager):
        """测试初始化"""
        assert storage_manager.database is not None
        assert storage_manager.cache is not None
        assert storage_manager.file is not None
    
    def test_save_market_data(self, storage_manager, sample_market_data):
        """测试保存市场数据"""
        # 测试保存K线数据
        assert storage_manager.save_market_data(sample_market_data['kline'])
        
        # 测试保存实时行情数据
        assert storage_manager.save_market_data(sample_market_data['tick'])
        
        # 测试保存成交记录数据
        assert storage_manager.save_market_data(sample_market_data['trade'])
    
    def test_get_market_data(self, storage_manager, sample_market_data):
        """测试获取市场数据"""
        # 保存数据
        storage_manager.save_market_data(sample_market_data['kline'])
        
        # 获取数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        data = storage_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        assert len(data) > 0
        assert isinstance(data[0], KlineData)
    
    def test_save_alert(self, storage_manager, sample_alert):
        """测试保存告警"""
        assert storage_manager.save_alert(sample_alert)
    
    def test_get_alerts(self, storage_manager, sample_alert):
        """测试获取告警"""
        # 保存告警
        storage_manager.save_alert(sample_alert)
        
        # 获取告警
        alerts = storage_manager.get_alerts(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        assert len(alerts) > 0
        assert isinstance(alerts[0], Alert)

class TestDatabaseManager:
    """数据库管理器测试"""
    
    def test_init(self, database_manager):
        """测试初始化"""
        assert database_manager.connection is not None
    
    def test_save_market_data(self, database_manager, sample_market_data):
        """测试保存市场数据"""
        # 测试保存K线数据
        assert database_manager.save_market_data(sample_market_data['kline'])
        
        # 测试保存实时行情数据
        assert database_manager.save_market_data(sample_market_data['tick'])
        
        # 测试保存成交记录数据
        assert database_manager.save_market_data(sample_market_data['trade'])
    
    def test_get_market_data(self, database_manager, sample_market_data):
        """测试获取市场数据"""
        # 保存数据
        database_manager.save_market_data(sample_market_data['kline'])
        
        # 获取数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        data = database_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        assert len(data) > 0
        assert isinstance(data[0], KlineData)
    
    def test_save_alert(self, database_manager, sample_alert):
        """测试保存告警"""
        assert database_manager.save_alert(sample_alert)
    
    def test_get_alerts(self, database_manager, sample_alert):
        """测试获取告警"""
        # 保存告警
        database_manager.save_alert(sample_alert)
        
        # 获取告警
        alerts = database_manager.get_alerts(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        assert len(alerts) > 0
        assert isinstance(alerts[0], Alert)

class TestCacheManager:
    """缓存管理器测试"""
    
    def test_init(self, cache_manager):
        """测试初始化"""
        assert cache_manager.client is not None
    
    def test_set_get(self, cache_manager):
        """测试设置和获取缓存"""
        key = "test_key"
        value = "test_value"
        
        # 设置缓存
        assert cache_manager.set(key, value)
        
        # 获取缓存
        assert cache_manager.get(key) == value
    
    def test_delete(self, cache_manager):
        """测试删除缓存"""
        key = "test_key"
        value = "test_value"
        
        # 设置缓存
        cache_manager.set(key, value)
        
        # 删除缓存
        assert cache_manager.delete(key)
        
        # 验证缓存已删除
        assert cache_manager.get(key) is None
    
    def test_exists(self, cache_manager):
        """测试检查缓存是否存在"""
        key = "test_key"
        value = "test_value"
        
        # 设置缓存
        cache_manager.set(key, value)
        
        # 检查缓存是否存在
        assert cache_manager.exists(key)
        
        # 删除缓存
        cache_manager.delete(key)
        
        # 验证缓存不存在
        assert not cache_manager.exists(key)

class TestFileManager:
    """文件管理器测试"""
    
    def test_init(self, file_manager):
        """测试初始化"""
        assert file_manager.base_dir is not None
    
    def test_save_market_data(self, file_manager, sample_market_data, tmp_path):
        """测试保存市场数据"""
        file_manager.base_dir = str(tmp_path)
        
        # 测试保存K线数据
        assert file_manager.save_market_data(sample_market_data['kline'])
        
        # 测试保存实时行情数据
        assert file_manager.save_market_data(sample_market_data['tick'])
        
        # 测试保存成交记录数据
        assert file_manager.save_market_data(sample_market_data['trade'])
    
    def test_get_market_data(self, file_manager, sample_market_data, tmp_path):
        """测试获取市场数据"""
        file_manager.base_dir = str(tmp_path)
        
        # 保存数据
        file_manager.save_market_data(sample_market_data['kline'])
        
        # 获取数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        data = file_manager.get_market_data(
            'BTCUSDT',
            'kline',
            start_time,
            end_time
        )
        assert len(data) > 0
        assert isinstance(data[0], KlineData)
    
    def test_save_alert(self, file_manager, sample_alert, tmp_path):
        """测试保存告警"""
        file_manager.base_dir = str(tmp_path)
        assert file_manager.save_alert(sample_alert)
    
    def test_get_alerts(self, file_manager, sample_alert, tmp_path):
        """测试获取告警"""
        file_manager.base_dir = str(tmp_path)
        
        # 保存告警
        file_manager.save_alert(sample_alert)
        
        # 获取告警
        alerts = file_manager.get_alerts(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )
        assert len(alerts) > 0
        assert isinstance(alerts[0], Alert) 