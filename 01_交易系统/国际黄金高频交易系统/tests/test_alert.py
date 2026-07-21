import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.core.alert.alert import Alert, AlertLevel, AlertStatus
from src.core.alert.alert_manager import AlertManager
from src.core.alert.alert_rule import AlertRule, AlertRuleType, AlertRuleOperator
from src.core.alert.alert_rule_manager import AlertRuleManager
from src.core.alert.alert_rule_engine import AlertRuleEngine
from src.core.alert.alert_rule_parser import AlertRuleParser
from src.core.alert.alert_rule_validator import AlertRuleValidator

@pytest.fixture
def alert():
    """创建示例告警"""
    return Alert(
        id="test_alert_1",
        level=AlertLevel.WARNING,
        message="Test alert message",
        source="test_source",
        timestamp=datetime.now(),
        status=AlertStatus.ACTIVE
    )

@pytest.fixture
def alert_rule():
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
def alert_rule_parser():
    """创建告警规则解析器实例"""
    return AlertRuleParser()

@pytest.fixture
def alert_rule_validator():
    """创建告警规则验证器实例"""
    return AlertRuleValidator()

class TestAlert:
    """告警测试"""
    
    def test_alert_creation(self, alert):
        """测试告警创建"""
        assert alert.id == "test_alert_1"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert message"
        assert alert.source == "test_source"
        assert alert.status == AlertStatus.ACTIVE
    
    def test_alert_level_enum(self):
        """测试告警级别枚举"""
        assert AlertLevel.INFO.value == "INFO"
        assert AlertLevel.WARNING.value == "WARNING"
        assert AlertLevel.ERROR.value == "ERROR"
        assert AlertLevel.CRITICAL.value == "CRITICAL"
    
    def test_alert_status_enum(self):
        """测试告警状态枚举"""
        assert AlertStatus.ACTIVE.value == "ACTIVE"
        assert AlertStatus.ACKNOWLEDGED.value == "ACKNOWLEDGED"
        assert AlertStatus.RESOLVED.value == "RESOLVED"
        assert AlertStatus.SUPPRESSED.value == "SUPPRESSED"

class TestAlertManager:
    """告警管理器测试"""
    
    def test_add_alert(self, alert_manager, alert):
        """测试添加告警"""
        alert_manager.add_alert(alert)
        assert len(alert_manager.get_active_alerts()) == 1
        assert alert_manager.get_active_alerts()[0] == alert
    
    def test_acknowledge_alert(self, alert_manager, alert):
        """测试确认告警"""
        alert_manager.add_alert(alert)
        alert_manager.acknowledge_alert(alert.id)
        assert alert.status == AlertStatus.ACKNOWLEDGED
    
    def test_resolve_alert(self, alert_manager, alert):
        """测试解决告警"""
        alert_manager.add_alert(alert)
        alert_manager.resolve_alert(alert.id)
        assert alert.status == AlertStatus.RESOLVED
    
    def test_suppress_alert(self, alert_manager, alert):
        """测试抑制告警"""
        alert_manager.add_alert(alert)
        alert_manager.suppress_alert(alert.id)
        assert alert.status == AlertStatus.SUPPRESSED
    
    def test_get_active_alerts(self, alert_manager, alert):
        """测试获取活动告警"""
        alert_manager.add_alert(alert)
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0] == alert
    
    def test_get_alert_by_id(self, alert_manager, alert):
        """测试通过ID获取告警"""
        alert_manager.add_alert(alert)
        retrieved_alert = alert_manager.get_alert_by_id(alert.id)
        assert retrieved_alert == alert

class TestAlertRule:
    """告警规则测试"""
    
    def test_alert_rule_creation(self, alert_rule):
        """测试告警规则创建"""
        assert alert_rule.id == "test_rule_1"
        assert alert_rule.name == "Test Rule"
        assert alert_rule.type == AlertRuleType.PRICE
        assert alert_rule.operator == AlertRuleOperator.GREATER_THAN
        assert alert_rule.threshold == 35000.00
        assert alert_rule.symbol == "BTCUSDT"
        assert alert_rule.level == AlertLevel.WARNING
        assert alert_rule.enabled is True
    
    def test_alert_rule_type_enum(self):
        """测试告警规则类型枚举"""
        assert AlertRuleType.PRICE.value == "PRICE"
        assert AlertRuleType.VOLUME.value == "VOLUME"
        assert AlertRuleType.TECHNICAL.value == "TECHNICAL"
        assert AlertRuleType.SYSTEM.value == "SYSTEM"
    
    def test_alert_rule_operator_enum(self):
        """测试告警规则操作符枚举"""
        assert AlertRuleOperator.EQUALS.value == "EQUALS"
        assert AlertRuleOperator.NOT_EQUALS.value == "NOT_EQUALS"
        assert AlertRuleOperator.GREATER_THAN.value == "GREATER_THAN"
        assert AlertRuleOperator.LESS_THAN.value == "LESS_THAN"
        assert AlertRuleOperator.GREATER_THAN_EQUALS.value == "GREATER_THAN_EQUALS"
        assert AlertRuleOperator.LESS_THAN_EQUALS.value == "LESS_THAN_EQUALS"

class TestAlertRuleManager:
    """告警规则管理器测试"""
    
    def test_add_rule(self, alert_rule_manager, alert_rule):
        """测试添加规则"""
        alert_rule_manager.add_rule(alert_rule)
        assert len(alert_rule_manager.get_rules()) == 1
        assert alert_rule_manager.get_rules()[0] == alert_rule
    
    def test_remove_rule(self, alert_rule_manager, alert_rule):
        """测试移除规则"""
        alert_rule_manager.add_rule(alert_rule)
        alert_rule_manager.remove_rule(alert_rule.id)
        assert len(alert_rule_manager.get_rules()) == 0
    
    def test_get_rule_by_id(self, alert_rule_manager, alert_rule):
        """测试通过ID获取规则"""
        alert_rule_manager.add_rule(alert_rule)
        retrieved_rule = alert_rule_manager.get_rule_by_id(alert_rule.id)
        assert retrieved_rule == alert_rule
    
    def test_enable_rule(self, alert_rule_manager, alert_rule):
        """测试启用规则"""
        alert_rule_manager.add_rule(alert_rule)
        alert_rule.enabled = False
        alert_rule_manager.enable_rule(alert_rule.id)
        assert alert_rule.enabled is True
    
    def test_disable_rule(self, alert_rule_manager, alert_rule):
        """测试禁用规则"""
        alert_rule_manager.add_rule(alert_rule)
        alert_rule_manager.disable_rule(alert_rule.id)
        assert alert_rule.enabled is False

class TestAlertRuleEngine:
    """告警规则引擎测试"""
    
    def test_evaluate_price_rule(self, alert_rule_engine, alert_rule):
        """测试评估价格规则"""
        # 测试大于阈值的情况
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 35000.00
        assert alert_rule_engine.evaluate_rule(alert_rule, 36000.00) is True
        
        # 测试小于阈值的情况
        assert alert_rule_engine.evaluate_rule(alert_rule, 34000.00) is False
    
    def test_evaluate_volume_rule(self, alert_rule_engine, alert_rule):
        """测试评估成交量规则"""
        alert_rule.type = AlertRuleType.VOLUME
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 100.00
        
        # 测试大于阈值的情况
        assert alert_rule_engine.evaluate_rule(alert_rule, 150.00) is True
        
        # 测试小于阈值的情况
        assert alert_rule_engine.evaluate_rule(alert_rule, 50.00) is False
    
    def test_evaluate_technical_rule(self, alert_rule_engine, alert_rule):
        """测试评估技术指标规则"""
        alert_rule.type = AlertRuleType.TECHNICAL
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 0.7
        
        # 测试RSI大于阈值的情况
        assert alert_rule_engine.evaluate_rule(alert_rule, 0.8) is True
        
        # 测试RSI小于阈值的情况
        assert alert_rule_engine.evaluate_rule(alert_rule, 0.6) is False

class TestAlertRuleParser:
    """告警规则解析器测试"""
    
    def test_parse_price_rule(self, alert_rule_parser):
        """测试解析价格规则"""
        rule_str = "PRICE BTCUSDT > 35000.00"
        rule = alert_rule_parser.parse(rule_str)
        assert rule.type == AlertRuleType.PRICE
        assert rule.symbol == "BTCUSDT"
        assert rule.operator == AlertRuleOperator.GREATER_THAN
        assert rule.threshold == 35000.00
    
    def test_parse_volume_rule(self, alert_rule_parser):
        """测试解析成交量规则"""
        rule_str = "VOLUME BTCUSDT > 100.00"
        rule = alert_rule_parser.parse(rule_str)
        assert rule.type == AlertRuleType.VOLUME
        assert rule.symbol == "BTCUSDT"
        assert rule.operator == AlertRuleOperator.GREATER_THAN
        assert rule.threshold == 100.00
    
    def test_parse_technical_rule(self, alert_rule_parser):
        """测试解析技术指标规则"""
        rule_str = "RSI BTCUSDT > 70"
        rule = alert_rule_parser.parse(rule_str)
        assert rule.type == AlertRuleType.TECHNICAL
        assert rule.symbol == "BTCUSDT"
        assert rule.operator == AlertRuleOperator.GREATER_THAN
        assert rule.threshold == 70.00

class TestAlertRuleValidator:
    """告警规则验证器测试"""
    
    def test_validate_price_rule(self, alert_rule_validator, alert_rule):
        """测试验证价格规则"""
        alert_rule.type = AlertRuleType.PRICE
        alert_rule.symbol = "BTCUSDT"
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 35000.00
        
        assert alert_rule_validator.validate(alert_rule) is True
    
    def test_validate_volume_rule(self, alert_rule_validator, alert_rule):
        """测试验证成交量规则"""
        alert_rule.type = AlertRuleType.VOLUME
        alert_rule.symbol = "BTCUSDT"
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 100.00
        
        assert alert_rule_validator.validate(alert_rule) is True
    
    def test_validate_technical_rule(self, alert_rule_validator, alert_rule):
        """测试验证技术指标规则"""
        alert_rule.type = AlertRuleType.TECHNICAL
        alert_rule.symbol = "BTCUSDT"
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = 70.00
        
        assert alert_rule_validator.validate(alert_rule) is True
    
    def test_validate_invalid_rule(self, alert_rule_validator, alert_rule):
        """测试验证无效规则"""
        alert_rule.type = AlertRuleType.PRICE
        alert_rule.symbol = ""  # 无效的符号
        alert_rule.operator = AlertRuleOperator.GREATER_THAN
        alert_rule.threshold = -100.00  # 无效的阈值
        
        assert alert_rule_validator.validate(alert_rule) is False 