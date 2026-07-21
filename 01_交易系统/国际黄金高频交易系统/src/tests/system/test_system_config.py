import pytest
import os
import json
from typing import Dict, Any

from src.system.config_manager import SystemConfigManager

@pytest.fixture
def config_manager():
    """创建系统配置管理器实例"""
    return SystemConfigManager(
        config_dir='test_config',
        default_config={
            'system': {
                'name': 'test_system',
                'version': '1.0.0',
                'environment': 'test'
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'test.log',
                'max_size': 1024,
                'backup_count': 5
            },
            'performance': {
                'monitor_interval': 60,
                'metrics': ['cpu', 'memory', 'disk'],
                'alert_thresholds': {
                    'cpu': 80,
                    'memory': 80,
                    'disk': 80
                }
            }
        }
    )

@pytest.fixture
def test_config_file():
    """创建测试配置文件"""
    config = {
        'system': {
            'name': 'test_system',
            'version': '1.0.0',
            'environment': 'test'
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'test.log',
            'max_size': 1024,
            'backup_count': 5
        },
        'performance': {
            'monitor_interval': 60,
            'metrics': ['cpu', 'memory', 'disk'],
            'alert_thresholds': {
                'cpu': 80,
                'memory': 80,
                'disk': 80
            }
        }
    }
    
    # 创建测试配置目录
    os.makedirs('test_config', exist_ok=True)
    
    # 写入配置文件
    with open('test_config/config.json', 'w') as f:
        json.dump(config, f)
        
    return 'test_config/config.json'

class TestSystemConfig:
    """系统配置测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, config_manager):
        """测试配置管理器初始化"""
        assert config_manager.config_dir == 'test_config'
        assert isinstance(config_manager.default_config, dict)
        assert 'system' in config_manager.default_config
        assert 'logging' in config_manager.default_config
        assert 'performance' in config_manager.default_config
        
    @pytest.mark.asyncio
    async def test_load_config(self, config_manager, test_config_file):
        """测试加载配置"""
        # 加载配置
        success = await config_manager.load_config()
        
        # 验证加载结果
        assert success is True
        assert config_manager.get_config() is not None
        assert config_manager.get_config()['system']['name'] == 'test_system'
        
    @pytest.mark.asyncio
    async def test_update_config(self, config_manager, test_config_file):
        """测试更新配置"""
        # 加载配置
        await config_manager.load_config()
        
        # 更新配置
        new_config = {
            'system': {
                'name': 'updated_system',
                'version': '1.0.1',
                'environment': 'test'
            }
        }
        
        success = await config_manager.update_config(new_config)
        
        # 验证更新结果
        assert success is True
        assert config_manager.get_config()['system']['name'] == 'updated_system'
        assert config_manager.get_config()['system']['version'] == '1.0.1'
        
    @pytest.mark.asyncio
    async def test_get_config_value(self, config_manager, test_config_file):
        """测试获取配置值"""
        # 加载配置
        await config_manager.load_config()
        
        # 获取配置值
        system_name = config_manager.get_config_value('system.name')
        log_level = config_manager.get_config_value('logging.level')
        
        # 验证配置值
        assert system_name == 'test_system'
        assert log_level == 'INFO'
        
    @pytest.mark.asyncio
    async def test_set_config_value(self, config_manager, test_config_file):
        """测试设置配置值"""
        # 加载配置
        await config_manager.load_config()
        
        # 设置配置值
        success = await config_manager.set_config_value('system.version', '1.0.2')
        
        # 验证设置结果
        assert success is True
        assert config_manager.get_config_value('system.version') == '1.0.2'
        
    @pytest.mark.asyncio
    async def test_validate_config(self, config_manager, test_config_file):
        """测试配置验证"""
        # 加载配置
        await config_manager.load_config()
        
        # 验证配置
        validation_result = await config_manager.validate_config()
        
        # 验证结果
        assert validation_result['is_valid'] is True
        assert len(validation_result['errors']) == 0
        
    @pytest.mark.asyncio
    async def test_save_config(self, config_manager, test_config_file):
        """测试保存配置"""
        # 加载配置
        await config_manager.load_config()
        
        # 更新配置
        new_config = {
            'system': {
                'name': 'saved_system',
                'version': '1.0.3',
                'environment': 'test'
            }
        }
        await config_manager.update_config(new_config)
        
        # 保存配置
        success = await config_manager.save_config()
        
        # 验证保存结果
        assert success is True
        assert os.path.exists('test_config/config.json')
        
    @pytest.mark.asyncio
    async def test_reset_config(self, config_manager, test_config_file):
        """测试重置配置"""
        # 加载配置
        await config_manager.load_config()
        
        # 更新配置
        new_config = {
            'system': {
                'name': 'modified_system',
                'version': '1.0.4',
                'environment': 'test'
            }
        }
        await config_manager.update_config(new_config)
        
        # 重置配置
        success = await config_manager.reset_config()
        
        # 验证重置结果
        assert success is True
        assert config_manager.get_config_value('system.name') == 'test_system'
        assert config_manager.get_config_value('system.version') == '1.0.0'
        
    @pytest.mark.asyncio
    async def test_error_handling(self, config_manager):
        """测试错误处理"""
        # 测试加载不存在的配置文件
        config_manager.config_dir = 'non_existent_dir'
        success = await config_manager.load_config()
        assert success is False
        
        # 测试更新无效的配置
        with pytest.raises(ValueError):
            await config_manager.update_config('invalid_config')
            
        # 测试获取不存在的配置值
        with pytest.raises(KeyError):
            config_manager.get_config_value('non_existent.key')
            
    @pytest.mark.asyncio
    async def test_config_encryption(self, config_manager, test_config_file):
        """测试配置加密"""
        # 加载配置
        await config_manager.load_config()
        
        # 设置敏感配置
        sensitive_config = {
            'api': {
                'key': 'test_api_key',
                'secret': 'test_api_secret'
            }
        }
        await config_manager.update_config(sensitive_config)
        
        # 保存加密配置
        success = await config_manager.save_config(encrypt=True)
        
        # 验证加密结果
        assert success is True
        assert os.path.exists('test_config/config.encrypted')
        
        # 加载加密配置
        success = await config_manager.load_config(decrypt=True)
        assert success is True
        assert config_manager.get_config_value('api.key') == 'test_api_key'
        assert config_manager.get_config_value('api.secret') == 'test_api_secret' 