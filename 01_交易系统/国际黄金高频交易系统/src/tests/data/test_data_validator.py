import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.data.data_validator import DataValidator

@pytest.fixture
def data_validator():
    """创建数据验证器实例"""
    return DataValidator(
        check_missing_values=True,
        check_outliers=True,
        check_duplicates=True,
        check_consistency=True,
        check_timestamps=True
    )

@pytest.fixture
def sample_market_data():
    """生成样本市场数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='1min')
    data = {
        'timestamp': dates,
        'open': np.random.normal(100, 1, len(dates)),
        'high': np.random.normal(101, 1, len(dates)),
        'low': np.random.normal(99, 1, len(dates)),
        'close': np.random.normal(100, 1, len(dates)),
        'volume': np.random.randint(1000, 10000, len(dates)),
        'bid_price': np.random.normal(99.9, 0.1, len(dates)),
        'ask_price': np.random.normal(100.1, 0.1, len(dates)),
        'bid_volume': np.random.randint(100, 1000, len(dates)),
        'ask_volume': np.random.randint(100, 1000, len(dates))
    }
    return pd.DataFrame(data)

class TestDataValidator:
    """数据验证器测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, data_validator):
        """测试数据验证器初始化"""
        assert data_validator.check_missing_values is True
        assert data_validator.check_outliers is True
        assert data_validator.check_duplicates is True
        assert data_validator.check_consistency is True
        assert data_validator.check_timestamps is True
        
    @pytest.mark.asyncio
    async def test_check_missing_values(self, data_validator, sample_market_data):
        """测试缺失值检查"""
        # 添加一些缺失值
        data = sample_market_data.copy()
        data.loc[10:20, 'close'] = np.nan
        
        # 检查缺失值
        validation_result = await data_validator.check_missing_values(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert 'close' in validation_result['missing_columns']
        assert len(validation_result['missing_counts']['close']) == 11
        
    @pytest.mark.asyncio
    async def test_check_outliers(self, data_validator, sample_market_data):
        """测试异常值检查"""
        # 添加一些异常值
        data = sample_market_data.copy()
        data.loc[10, 'close'] = 1000  # 添加一个明显的异常值
        
        # 检查异常值
        validation_result = await data_validator.check_outliers(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert 'close' in validation_result['outlier_columns']
        assert len(validation_result['outlier_counts']['close']) == 1
        
    @pytest.mark.asyncio
    async def test_check_duplicates(self, data_validator, sample_market_data):
        """测试重复值检查"""
        # 添加一些重复值
        data = sample_market_data.copy()
        data.loc[10] = data.loc[0]  # 复制第一行数据
        
        # 检查重复值
        validation_result = await data_validator.check_duplicates(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert len(validation_result['duplicate_rows']) == 1
        
    @pytest.mark.asyncio
    async def test_check_consistency(self, data_validator, sample_market_data):
        """测试数据一致性检查"""
        # 添加一些不一致的数据
        data = sample_market_data.copy()
        data.loc[10, 'high'] = data.loc[10, 'low'] - 1  # 最高价低于最低价
        
        # 检查一致性
        validation_result = await data_validator.check_consistency(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert len(validation_result['inconsistent_rows']) == 1
        
    @pytest.mark.asyncio
    async def test_check_timestamps(self, data_validator, sample_market_data):
        """测试时间戳检查"""
        # 添加一些无效的时间戳
        data = sample_market_data.copy()
        data.loc[10, 'timestamp'] = pd.NaT  # 添加无效时间戳
        
        # 检查时间戳
        validation_result = await data_validator.check_timestamps(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert len(validation_result['invalid_timestamps']) == 1
        
    @pytest.mark.asyncio
    async def test_validate_data(self, data_validator, sample_market_data):
        """测试完整的数据验证流程"""
        # 执行完整的验证流程
        validation_result = await data_validator.validate_data(sample_market_data)
        
        # 验证结果
        assert validation_result['is_valid']
        assert not validation_result['missing_columns']
        assert not validation_result['outlier_columns']
        assert not validation_result['duplicate_rows']
        assert not validation_result['inconsistent_rows']
        assert not validation_result['invalid_timestamps']
        
    @pytest.mark.asyncio
    async def test_validate_data_with_issues(self, data_validator, sample_market_data):
        """测试包含问题的数据验证"""
        # 添加各种问题
        data = sample_market_data.copy()
        data.loc[10, 'close'] = np.nan  # 缺失值
        data.loc[20, 'close'] = 1000  # 异常值
        data.loc[30] = data.loc[0]  # 重复值
        data.loc[40, 'high'] = data.loc[40, 'low'] - 1  # 不一致数据
        data.loc[50, 'timestamp'] = pd.NaT  # 无效时间戳
        
        # 执行验证
        validation_result = await data_validator.validate_data(data)
        
        # 验证结果
        assert not validation_result['is_valid']
        assert 'close' in validation_result['missing_columns']
        assert 'close' in validation_result['outlier_columns']
        assert len(validation_result['duplicate_rows']) == 1
        assert len(validation_result['inconsistent_rows']) == 1
        assert len(validation_result['invalid_timestamps']) == 1
        
    @pytest.mark.asyncio
    async def test_generate_validation_report(self, data_validator, sample_market_data):
        """测试生成验证报告"""
        # 添加一些问题
        data = sample_market_data.copy()
        data.loc[10, 'close'] = np.nan
        data.loc[20, 'close'] = 1000
        
        # 执行验证
        validation_result = await data_validator.validate_data(data)
        
        # 生成报告
        report = await data_validator.generate_validation_report(validation_result)
        
        # 验证报告
        assert isinstance(report, dict)
        assert 'summary' in report
        assert 'details' in report
        assert 'recommendations' in report
        assert not report['summary']['is_valid']
        assert len(report['details']['issues']) > 0
        assert len(report['recommendations']) > 0 