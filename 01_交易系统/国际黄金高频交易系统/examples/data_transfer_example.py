import os
import time
from datetime import datetime, timedelta
from src.system.data_transfer import DataTransfer, ExportConfig, ImportConfig
from src.system.storage import MonitoringStorage
from src.system.alert import Alert, AlertLevel
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data(storage):
    """创建示例数据"""
    # 创建性能指标数据
    for i in range(5):
        metrics = {
            "timestamp": datetime.now() - timedelta(minutes=i*5),
            "cpu_usage": 50 + i * 5,
            "memory_usage": 60 + i * 4,
            "disk_usage": 70 + i * 3,
            "network_latency": 80 + i * 2
        }
        storage.save_metrics(metrics)
        logger.info(f"创建性能指标数据: CPU使用率 {metrics['cpu_usage']}%")
    
    # 创建组件状态数据
    components = ["database", "cache", "api", "order_engine"]
    statuses = ["healthy", "warning", "error"]
    for i, component in enumerate(components):
        status = {
            "timestamp": datetime.now() - timedelta(minutes=i*5),
            "component": component,
            "status": statuses[i % len(statuses)],
            "details": {
                "message": f"{component} 状态检查",
                "check_time": datetime.now().isoformat()
            }
        }
        storage.save_component_status(status)
        logger.info(f"创建组件状态数据: {component} -> {status['status']}")
    
    # 创建状态报告数据
    report = {
        "timestamp": datetime.now(),
        "overall_status": "warning",
        "components": {
            "database": "healthy",
            "cache": "warning",
            "api": "error",
            "order_engine": "healthy"
        },
        "details": {
            "message": "系统状态检查报告",
            "check_time": datetime.now().isoformat()
        }
    }
    storage.save_status_report(report)
    logger.info("创建状态报告数据")
    
    # 创建告警数据
    alert_levels = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
    for i, level in enumerate(alert_levels):
        alert = Alert(
            id=f"alert_{i}",
            level=level,
            title=f"{level.name} 级别告警",
            message=f"这是一个 {level.name} 级别的测试告警消息",
            timestamp=datetime.now() - timedelta(minutes=i*15),
            source="test",
            metadata={
                "test_key": "test_value",
                "alert_number": i
            }
        )
        storage.save_alert(alert)
        logger.info(f"创建告警数据: {level.name}")

def export_example(data_transfer):
    """导出示例"""
    # 创建导出目录
    export_dir = "data/export"
    os.makedirs(export_dir, exist_ok=True)
    
    # 导出JSON格式数据
    logger.info("\n1. 导出JSON格式数据")
    json_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now(),
        compress=False
    )
    json_path = os.path.join(export_dir, "monitoring_data.json")
    success = data_transfer.export_data(json_path, json_config)
    if success:
        logger.info(f"JSON数据导出成功: {json_path}")
    else:
        logger.error("JSON数据导出失败")
    
    # 导出压缩的JSON格式数据
    logger.info("\n2. 导出压缩的JSON格式数据")
    compressed_json_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now(),
        compress=True
    )
    compressed_json_path = os.path.join(export_dir, "monitoring_data_compressed.json")
    success = data_transfer.export_data(compressed_json_path, compressed_json_config)
    if success:
        logger.info(f"压缩JSON数据导出成功: {compressed_json_path}.gz")
    else:
        logger.error("压缩JSON数据导出失败")
    
    # 导出CSV格式数据
    logger.info("\n3. 导出CSV格式数据")
    csv_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now(),
        compress=False
    )
    csv_path = os.path.join(export_dir, "monitoring_data.csv")
    success = data_transfer.export_data(csv_path, csv_config)
    if success:
        logger.info(f"CSV数据导出成功: {csv_path}")
        logger.info("已生成以下CSV文件:")
        logger.info(f"- {csv_path}_metrics.csv")
        logger.info(f"- {csv_path}_component_status.csv")
        logger.info(f"- {csv_path}_status_reports.csv")
        logger.info(f"- {csv_path}_alerts.csv")
    else:
        logger.error("CSV数据导出失败")
    
    # 导出部分数据
    logger.info("\n4. 导出部分数据")
    partial_config = ExportConfig(
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now(),
        export_metrics=True,
        export_component_status=True,
        export_status_reports=False,
        export_alerts=False,
        compress=False
    )
    partial_path = os.path.join(export_dir, "partial_data.json")
    success = data_transfer.export_data(partial_path, partial_config)
    if success:
        logger.info(f"部分数据导出成功: {partial_path}")
    else:
        logger.error("部分数据导出失败")

def import_example(data_transfer):
    """导入示例"""
    export_dir = "data/export"
    
    # 导入JSON格式数据
    logger.info("\n1. 导入JSON格式数据")
    json_path = os.path.join(export_dir, "monitoring_data.json")
    json_config = ImportConfig(
        validate_data=True,
        clean_data=True,
        skip_duplicates=True
    )
    success = data_transfer.import_data(json_path, json_config)
    if success:
        logger.info("JSON数据导入成功")
    else:
        logger.error("JSON数据导入失败")
    
    # 导入压缩的JSON格式数据
    logger.info("\n2. 导入压缩的JSON格式数据")
    compressed_json_path = os.path.join(export_dir, "monitoring_data_compressed.json.gz")
    compressed_config = ImportConfig(
        validate_data=True,
        clean_data=True,
        skip_duplicates=True
    )
    success = data_transfer.import_data(compressed_json_path, compressed_config)
    if success:
        logger.info("压缩JSON数据导入成功")
    else:
        logger.error("压缩JSON数据导入失败")
    
    # 导入CSV格式数据
    logger.info("\n3. 导入CSV格式数据")
    csv_path = os.path.join(export_dir, "monitoring_data.csv")
    csv_config = ImportConfig(
        validate_data=True,
        clean_data=True,
        skip_duplicates=True
    )
    success = data_transfer.import_data(csv_path, csv_config)
    if success:
        logger.info("CSV数据导入成功")
    else:
        logger.error("CSV数据导入失败")

def main():
    """主函数"""
    # 初始化存储管理器
    storage = MonitoringStorage()
    
    # 初始化数据导出导入管理器
    data_transfer = DataTransfer(storage)
    
    try:
        # 创建示例数据
        logger.info("创建示例数据...")
        create_sample_data(storage)
        
        # 等待1秒，确保数据已保存
        time.sleep(1)
        
        # 导出示例
        logger.info("\n执行导出示例...")
        export_example(data_transfer)
        
        # 清空数据库
        logger.info("\n清空数据库...")
        storage = MonitoringStorage()
        data_transfer = DataTransfer(storage)
        
        # 导入示例
        logger.info("\n执行导入示例...")
        import_example(data_transfer)
        
        logger.info("\n数据导出导入演示完成")
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main() 