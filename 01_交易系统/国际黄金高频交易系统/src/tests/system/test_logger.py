import pytest
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from src.system.logger import SystemLogger

@pytest.fixture
def logger():
    """创建系统日志管理器实例"""
    return SystemLogger(
        name='test_logger',
        log_dir='test_logs',
        config={
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': 'test.log',
            'max_size': 1024,
            'backup_count': 5,
            'filters': {
                'level': 'INFO',
                'keywords': ['error', 'warning']
            }
        }
    )

@pytest.fixture
def test_log_file():
    """创建测试日志文件"""
    # 创建日志目录
    os.makedirs('test_logs', exist_ok=True)
    
    # 创建测试日志文件
    log_file = 'test_logs/test.log'
    with open(log_file, 'w') as f:
        f.write('2024-01-01 00:00:00 - test_logger - INFO - Test log message\n')
        f.write('2024-01-01 00:00:01 - test_logger - WARNING - Test warning message\n')
        f.write('2024-01-01 00:00:02 - test_logger - ERROR - Test error message\n')
        
    return log_file

class TestSystemLogger:
    """系统日志测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, logger):
        """测试日志管理器初始化"""
        assert logger.name == 'test_logger'
        assert logger.log_dir == 'test_logs'
        assert logger.config['level'] == 'INFO'
        assert logger.config['max_size'] == 1024
        assert logger.config['backup_count'] == 5
        
    @pytest.mark.asyncio
    async def test_setup_logger(self, logger):
        """测试日志设置"""
        # 设置日志
        success = await logger.setup_logger()
        
        # 验证设置结果
        assert success is True
        assert os.path.exists(logger.config['file_path'])
        assert logging.getLogger(logger.name).level == logging.INFO
        
    @pytest.mark.asyncio
    async def test_log_messages(self, logger):
        """测试日志记录"""
        # 设置日志
        await logger.setup_logger()
        
        # 记录不同级别的日志
        logger.info('Test info message')
        logger.warning('Test warning message')
        logger.error('Test error message')
        
        # 验证日志文件内容
        with open(logger.config['file_path'], 'r') as f:
            log_content = f.read()
            assert 'Test info message' in log_content
            assert 'Test warning message' in log_content
            assert 'Test error message' in log_content
            
    @pytest.mark.asyncio
    async def test_log_rotation(self, logger):
        """测试日志轮转"""
        # 设置日志
        await logger.setup_logger()
        
        # 生成超过大小限制的日志
        large_message = 'x' * 1000
        for _ in range(10):
            logger.info(large_message)
            
        # 验证日志轮转
        assert os.path.exists(f"{logger.config['file_path']}.1")
        
    @pytest.mark.asyncio
    async def test_log_filtering(self, logger):
        """测试日志过滤"""
        # 设置日志
        await logger.setup_logger()
        
        # 记录不同级别的日志
        logger.debug('Test debug message')
        logger.info('Test info message')
        logger.warning('Test warning message')
        logger.error('Test error message')
        
        # 验证日志过滤
        with open(logger.config['file_path'], 'r') as f:
            log_content = f.read()
            assert 'Test debug message' not in log_content
            assert 'Test info message' in log_content
            assert 'Test warning message' in log_content
            assert 'Test error message' in log_content
            
    @pytest.mark.asyncio
    async def test_log_cleanup(self, logger):
        """测试日志清理"""
        # 设置日志
        await logger.setup_logger()
        
        # 创建多个日志文件
        for i in range(10):
            with open(f"{logger.config['file_path']}.{i}", 'w') as f:
                f.write(f'Test log file {i}\n')
                
        # 清理日志
        success = await logger.cleanup_logs()
        
        # 验证清理结果
        assert success is True
        assert len(os.listdir('test_logs')) <= logger.config['backup_count']
        
    @pytest.mark.asyncio
    async def test_log_analysis(self, logger, test_log_file):
        """测试日志分析"""
        # 分析日志
        analysis_result = await logger.analyze_logs(test_log_file)
        
        # 验证分析结果
        assert isinstance(analysis_result, dict)
        assert 'total_messages' in analysis_result
        assert 'error_count' in analysis_result
        assert 'warning_count' in analysis_result
        assert 'info_count' in analysis_result
        assert analysis_result['error_count'] == 1
        assert analysis_result['warning_count'] == 1
        assert analysis_result['info_count'] == 1
        
    @pytest.mark.asyncio
    async def test_log_search(self, logger, test_log_file):
        """测试日志搜索"""
        # 搜索日志
        search_result = await logger.search_logs(
            file_path=test_log_file,
            keyword='error',
            level='ERROR'
        )
        
        # 验证搜索结果
        assert isinstance(search_result, list)
        assert len(search_result) == 1
        assert 'Test error message' in search_result[0]
        
    @pytest.mark.asyncio
    async def test_log_export(self, logger, test_log_file):
        """测试日志导出"""
        # 导出日志
        export_file = 'test_logs/exported_logs.csv'
        success = await logger.export_logs(
            file_path=test_log_file,
            export_path=export_file,
            format='csv'
        )
        
        # 验证导出结果
        assert success is True
        assert os.path.exists(export_file)
        
    @pytest.mark.asyncio
    async def test_error_handling(self, logger):
        """测试错误处理"""
        # 测试无效的日志目录
        logger.log_dir = '/invalid/directory'
        success = await logger.setup_logger()
        assert success is False
        
        # 测试无效的日志级别
        logger.config['level'] = 'INVALID_LEVEL'
        with pytest.raises(ValueError):
            await logger.setup_logger()
            
        # 测试不存在的日志文件
        with pytest.raises(FileNotFoundError):
            await logger.analyze_logs('non_existent.log')
            
    @pytest.mark.asyncio
    async def test_concurrent_logging(self, logger):
        """测试并发日志记录"""
        # 设置日志
        await logger.setup_logger()
        
        # 并发记录日志
        import asyncio
        tasks = []
        for i in range(10):
            tasks.append(logger.info(f'Concurrent log message {i}'))
            
        # 等待所有日志记录完成
        await asyncio.gather(*tasks)
        
        # 验证日志文件
        with open(logger.config['file_path'], 'r') as f:
            log_content = f.read()
            for i in range(10):
                assert f'Concurrent log message {i}' in log_content 