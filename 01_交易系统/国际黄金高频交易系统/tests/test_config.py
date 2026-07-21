import pytest
import os
import yaml
import json
from src.system.config import (
    MonitoringConfig,
    AlertConfig,
    NotificationConfig,
    StorageConfig,
    SystemConfig,
    ConfigManager
)

@pytest.fixture
def config_dir(tmp_path):
    """创建临时配置目录"""
    return tmp_path / "config"

@pytest.fixture
def yaml_config_path(config_dir):
    """创建临时YAML配置文件路径"""
    return config_dir / "system_config.yaml"

@pytest.fixture
def json_config_path(config_dir):
    """创建临时JSON配置文件路径"""
    return config_dir / "system_config.json"

@pytest.fixture
def sample_config_data():
    """创建示例配置数据"""
    return {
        "monitoring": {
            "collection_interval": 30,
            "retention_days": 60,
            "performance_thresholds": {
                "cpu_usage": 90.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "network_latency": 150.0
            }
        },
        "alert": {
            "enabled": True,
            "min_interval": 600,
            "max_alerts_per_day": 50,
            "alert_levels": {
                "INFO": {"enabled": False},
                "WARNING": {"enabled": True},
                "ERROR": {"enabled": True},
                "CRITICAL": {"enabled": True}
            }
        },
        "notification": {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "username": "test@test.com",
                "password": "test_password",
                "from_email": "test@test.com",
                "to_emails": ["admin@test.com"]
            },
            "webhook": {
                "enabled": True,
                "url": "http://test.com/webhook",
                "headers": {"Authorization": "Bearer test_token"}
            }
        },
        "storage": {
            "db_type": "sqlite",
            "db_path": "data/test.db",
            "backup_enabled": True,
            "backup_interval": 43200,
            "backup_path": "data/test_backups"
        }
    }

def test_monitoring_config_defaults():
    """测试监控配置默认值"""
    config = MonitoringConfig()
    assert config.collection_interval == 60
    assert config.retention_days == 30
    assert config.performance_thresholds["cpu_usage"] == 80.0
    assert config.performance_thresholds["memory_usage"] == 80.0
    assert config.performance_thresholds["disk_usage"] == 85.0
    assert config.performance_thresholds["network_latency"] == 100.0

def test_alert_config_defaults():
    """测试告警配置默认值"""
    config = AlertConfig()
    assert config.enabled is True
    assert config.min_interval == 300
    assert config.max_alerts_per_day == 100
    assert all(level["enabled"] for level in config.alert_levels.values())

def test_notification_config_defaults():
    """测试通知配置默认值"""
    config = NotificationConfig()
    assert config.email["enabled"] is False
    assert config.email["smtp_port"] == 587
    assert config.webhook["enabled"] is False
    assert isinstance(config.webhook["headers"], dict)

def test_storage_config_defaults():
    """测试存储配置默认值"""
    config = StorageConfig()
    assert config.db_type == "sqlite"
    assert config.db_path == "data/monitoring.db"
    assert config.backup_enabled is True
    assert config.backup_interval == 86400
    assert config.backup_path == "data/backups"

def test_system_config_defaults():
    """测试系统配置默认值"""
    config = SystemConfig()
    assert isinstance(config.monitoring, MonitoringConfig)
    assert isinstance(config.alert, AlertConfig)
    assert isinstance(config.notification, NotificationConfig)
    assert isinstance(config.storage, StorageConfig)

def test_config_manager_load_yaml(yaml_config_path, sample_config_data):
    """测试从YAML文件加载配置"""
    # 创建配置文件
    os.makedirs(os.path.dirname(yaml_config_path), exist_ok=True)
    with open(yaml_config_path, 'w') as f:
        yaml.safe_dump(sample_config_data, f)
    
    # 加载配置
    manager = ConfigManager(str(yaml_config_path))
    success = manager.load_config()
    
    # 验证结果
    assert success
    config = manager.get_config()
    assert config.monitoring.collection_interval == 30
    assert config.alert.min_interval == 600
    assert config.notification.email["smtp_server"] == "smtp.test.com"
    assert config.storage.backup_interval == 43200

def test_config_manager_load_json(json_config_path, sample_config_data):
    """测试从JSON文件加载配置"""
    # 创建配置文件
    os.makedirs(os.path.dirname(json_config_path), exist_ok=True)
    with open(json_config_path, 'w') as f:
        json.dump(sample_config_data, f)
    
    # 加载配置
    manager = ConfigManager(str(json_config_path))
    success = manager.load_config()
    
    # 验证结果
    assert success
    config = manager.get_config()
    assert config.monitoring.collection_interval == 30
    assert config.alert.min_interval == 600
    assert config.notification.email["smtp_server"] == "smtp.test.com"
    assert config.storage.backup_interval == 43200

def test_config_manager_save_yaml(yaml_config_path, sample_config_data):
    """测试保存配置到YAML文件"""
    # 创建配置管理器
    manager = ConfigManager(str(yaml_config_path))
    
    # 更新配置
    manager.update_config(sample_config_data)
    
    # 保存配置
    success = manager.save_config()
    assert success
    
    # 验证文件内容
    with open(yaml_config_path, 'r') as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data["monitoring"]["collection_interval"] == 30
    assert loaded_data["alert"]["min_interval"] == 600
    assert loaded_data["notification"]["email"]["smtp_server"] == "smtp.test.com"
    assert loaded_data["storage"]["backup_interval"] == 43200

def test_config_manager_save_json(json_config_path, sample_config_data):
    """测试保存配置到JSON文件"""
    # 创建配置管理器
    manager = ConfigManager(str(json_config_path))
    
    # 更新配置
    manager.update_config(sample_config_data)
    
    # 保存配置
    success = manager.save_config()
    assert success
    
    # 验证文件内容
    with open(json_config_path, 'r') as f:
        loaded_data = json.load(f)
    assert loaded_data["monitoring"]["collection_interval"] == 30
    assert loaded_data["alert"]["min_interval"] == 600
    assert loaded_data["notification"]["email"]["smtp_server"] == "smtp.test.com"
    assert loaded_data["storage"]["backup_interval"] == 43200

def test_config_validation_success(sample_config_data):
    """测试配置验证成功"""
    manager = ConfigManager()
    manager.update_config(sample_config_data)
    assert manager.validate_config()

def test_config_validation_failure():
    """测试配置验证失败"""
    manager = ConfigManager()
    
    # 设置无效的配置
    invalid_config = {
        "monitoring": {"collection_interval": -1},  # 无效的采集间隔
        "alert": {"min_interval": 0},  # 无效的最小告警间隔
        "notification": {
            "email": {
                "enabled": True,
                "smtp_server": "",  # 无效的SMTP服务器
                "username": "",
                "password": "",
                "to_emails": []
            }
        },
        "storage": {
            "backup_enabled": True,
            "backup_interval": -1  # 无效的备份间隔
        }
    }
    
    manager.update_config(invalid_config)
    assert not manager.validate_config()

def test_config_manager_nonexistent_file():
    """测试加载不存在的配置文件"""
    manager = ConfigManager("nonexistent.yaml")
    assert not manager.load_config()

def test_config_manager_invalid_yaml(yaml_config_path):
    """测试加载无效的YAML文件"""
    # 创建无效的YAML文件
    os.makedirs(os.path.dirname(yaml_config_path), exist_ok=True)
    with open(yaml_config_path, 'w') as f:
        f.write("invalid: yaml: content:")
    
    manager = ConfigManager(str(yaml_config_path))
    assert not manager.load_config()

def test_config_manager_update_partial(sample_config_data):
    """测试部分更新配置"""
    manager = ConfigManager()
    
    # 更新部分配置
    partial_config = {
        "monitoring": {"collection_interval": 45},
        "alert": {"max_alerts_per_day": 75}
    }
    
    success = manager.update_config(partial_config)
    assert success
    
    config = manager.get_config()
    assert config.monitoring.collection_interval == 45
    assert config.alert.max_alerts_per_day == 75
    # 其他配置保持默认值
    assert config.monitoring.retention_days == 30
    assert config.alert.min_interval == 300 