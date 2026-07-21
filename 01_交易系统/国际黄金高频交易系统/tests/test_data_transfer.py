import pytest
import os
import json
import gzip
from datetime import datetime, timedelta
from src.system.data_transfer import (
    ExportConfig,
    ImportConfig,
    DataTransfer
)
from src.system.storage import MonitoringStorage
from src.system.alert import Alert, AlertLevel

@pytest.fixture
def storage(tmp_path):
    """创建测试用的存储管理器"""
    db_path = tmp_path / "test.db"
    return MonitoringStorage(str(db_path))

@pytest.fixture
def data_transfer(storage):
    """创建测试用的数据导出导入管理器"""
    return DataTransfer(storage)

@pytest.fixture
def export_dir(tmp_path):
    """创建测试用的导出目录"""
    return tmp_path / "export"

@pytest.fixture
def sample_data(storage):
    """创建测试用的样本数据"""
    # 创建性能指标数据
    metrics = {
        "timestamp": datetime.now(),
        "cpu_usage": 75.5,
        "memory_usage": 82.3,
        "disk_usage": 65.8,
        "network_latency": 95.2
    }
    storage.save_metrics(metrics)
    
    # 创建组件状态数据
    status = {
        "timestamp": datetime.now(),
        "component": "database",
        "status": "healthy",
        "details": {"connection_pool": 10, "active_connections": 5}
    }
    storage.save_component_status(status)
    
    # 创建状态报告数据
    report = {
        "timestamp": datetime.now(),
        "overall_status": "healthy",
        "components": {"database": "healthy", "cache": "healthy"},
        "details": {"message": "所有组件运行正常"}
    }
    storage.save_status_report(report)
    
    # 创建告警数据
    alert = Alert(
        id="test_alert_1",
        level=AlertLevel.WARNING,
        title="测试告警",
        message="这是一个测试告警消息",
        timestamp=datetime.now(),
        source="test",
        metadata={"test_key": "test_value"}
    )
    storage.save_alert(alert)
    
    return {
        "metrics": metrics,
        "status": status,
        "report": report,
        "alert": alert
    }

def test_export_json(data_transfer, export_dir, sample_data):
    """测试导出JSON格式数据"""
    # 配置导出
    config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1)
    )
    
    # 导出数据
    export_path = export_dir / "export.json"
    success = data_transfer.export_data(str(export_path), config)
    
    # 验证结果
    assert success
    assert os.path.exists(export_path)
    
    # 验证导出的数据
    with open(export_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    
    assert "metadata" in export_data
    assert "data" in export_data
    assert "metrics" in export_data["data"]
    assert "component_status" in export_data["data"]
    assert "status_reports" in export_data["data"]
    assert "alerts" in export_data["data"]

def test_export_json_compressed(data_transfer, export_dir, sample_data):
    """测试导出压缩的JSON格式数据"""
    # 配置导出
    config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1),
        compress=True
    )
    
    # 导出数据
    export_path = export_dir / "export.json"
    success = data_transfer.export_data(str(export_path), config)
    
    # 验证结果
    assert success
    assert os.path.exists(export_path + '.gz')
    
    # 验证导出的数据
    with gzip.open(export_path + '.gz', 'rt', encoding='utf-8') as f:
        export_data = json.load(f)
    
    assert "metadata" in export_data
    assert "data" in export_data

def test_export_csv(data_transfer, export_dir, sample_data):
    """测试导出CSV格式数据"""
    # 配置导出
    config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1),
        compress=False
    )
    
    # 导出数据
    export_path = export_dir / "export.csv"
    success = data_transfer.export_data(str(export_path), config)
    
    # 验证结果
    assert success
    assert os.path.exists(export_dir / "export_metrics.csv")
    assert os.path.exists(export_dir / "export_component_status.csv")
    assert os.path.exists(export_dir / "export_status_reports.csv")
    assert os.path.exists(export_dir / "export_alerts.csv")

def test_import_json(data_transfer, export_dir, sample_data):
    """测试导入JSON格式数据"""
    # 先导出数据
    export_path = export_dir / "export.json"
    export_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1)
    )
    data_transfer.export_data(str(export_path), export_config)
    
    # 清空存储
    data_transfer.storage = MonitoringStorage(str(data_transfer.storage.db_path))
    
    # 导入数据
    import_config = ImportConfig()
    success = data_transfer.import_data(str(export_path), import_config)
    
    # 验证结果
    assert success
    
    # 验证导入的数据
    metrics = data_transfer.storage.get_metrics_by_time_range(
        datetime.now() - timedelta(hours=1),
        datetime.now() + timedelta(hours=1)
    )
    assert len(metrics) > 0
    
    alerts = data_transfer.storage.get_alerts_by_time_range(
        datetime.now() - timedelta(hours=1),
        datetime.now() + timedelta(hours=1)
    )
    assert len(alerts) > 0

def test_import_csv(data_transfer, export_dir, sample_data):
    """测试导入CSV格式数据"""
    # 先导出数据
    export_path = export_dir / "export.csv"
    export_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1)
    )
    data_transfer.export_data(str(export_path), export_config)
    
    # 清空存储
    data_transfer.storage = MonitoringStorage(str(data_transfer.storage.db_path))
    
    # 导入数据
    import_config = ImportConfig()
    success = data_transfer.import_data(str(export_path), import_config)
    
    # 验证结果
    assert success
    
    # 验证导入的数据
    metrics = data_transfer.storage.get_metrics_by_time_range(
        datetime.now() - timedelta(hours=1),
        datetime.now() + timedelta(hours=1)
    )
    assert len(metrics) > 0
    
    alerts = data_transfer.storage.get_alerts_by_time_range(
        datetime.now() - timedelta(hours=1),
        datetime.now() + timedelta(hours=1)
    )
    assert len(alerts) > 0

def test_import_with_validation(data_transfer, export_dir):
    """测试导入时的数据验证"""
    # 创建无效的数据文件
    invalid_data = {
        "data": {
            "metrics": [{
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": "invalid"  # 无效的CPU使用率
            }]
        }
    }
    
    export_path = export_dir / "invalid.json"
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(invalid_data, f)
    
    # 导入数据
    import_config = ImportConfig(validate_data=True)
    success = data_transfer.import_data(str(export_path), import_config)
    
    # 验证结果
    assert not success

def test_import_skip_duplicates(data_transfer, export_dir, sample_data):
    """测试导入时跳过重复数据"""
    # 先导出数据
    export_path = export_dir / "export.json"
    export_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1)
    )
    data_transfer.export_data(str(export_path), export_config)
    
    # 再次导入数据
    import_config = ImportConfig(skip_duplicates=True)
    success = data_transfer.import_data(str(export_path), import_config)
    
    # 验证结果
    assert success
    
    # 验证没有重复数据
    metrics = data_transfer.storage.get_metrics_by_time_range(
        datetime.now() - timedelta(hours=1),
        datetime.now() + timedelta(hours=1)
    )
    assert len(metrics) == 1  # 只有一条记录

def test_export_with_time_range(data_transfer, export_dir, sample_data):
    """测试按时间范围导出数据"""
    # 配置导出
    config = ExportConfig(
        start_time=datetime.now() + timedelta(hours=1),  # 未来时间
        end_time=datetime.now() + timedelta(hours=2)
    )
    
    # 导出数据
    export_path = export_dir / "export.json"
    success = data_transfer.export_data(str(export_path), config)
    
    # 验证结果
    assert success
    
    # 验证导出的数据为空
    with open(export_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    
    assert len(export_data["data"].get("metrics", [])) == 0
    assert len(export_data["data"].get("alerts", [])) == 0

def test_export_partial_data(data_transfer, export_dir, sample_data):
    """测试部分导出数据"""
    # 配置导出
    config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=1),
        export_metrics=True,
        export_component_status=False,
        export_status_reports=False,
        export_alerts=True
    )
    
    # 导出数据
    export_path = export_dir / "export.json"
    success = data_transfer.export_data(str(export_path), config)
    
    # 验证结果
    assert success
    
    # 验证导出的数据
    with open(export_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    
    assert "metrics" in export_data["data"]
    assert "alerts" in export_data["data"]
    assert "component_status" not in export_data["data"]
    assert "status_reports" not in export_data["data"] 