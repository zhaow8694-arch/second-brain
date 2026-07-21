import os
import json
import csv
import gzip
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.system.storage import MonitoringStorage
from src.system.logger import logger

@dataclass
class ExportConfig:
    """导出配置"""
    start_time: Optional[datetime] = None  # 开始时间
    end_time: Optional[datetime] = None  # 结束时间
    export_metrics: bool = True  # 是否导出性能指标
    export_component_status: bool = True  # 是否导出组件状态
    export_status_reports: bool = True  # 是否导出状态报告
    export_alerts: bool = True  # 是否导出告警记录
    compress: bool = True  # 是否压缩
    encrypt: bool = False  # 是否加密
    encryption_key: Optional[str] = None  # 加密密钥

@dataclass
class ImportConfig:
    """导入配置"""
    skip_duplicates: bool = True  # 是否跳过重复数据
    validate_data: bool = True  # 是否验证数据
    clean_data: bool = True  # 是否清洗数据
    merge_strategy: str = "overwrite"  # 合并策略：overwrite/skip/merge

class DataTransfer:
    """数据导出导入管理器"""
    
    def __init__(self, storage: MonitoringStorage):
        """初始化数据导出导入管理器
        
        Args:
            storage: 监控数据存储管理器
        """
        self.storage = storage
    
    def export_data(self, export_path: str, config: ExportConfig) -> bool:
        """导出数据
        
        Args:
            export_path: 导出文件路径
            config: 导出配置
            
        Returns:
            bool: 是否导出成功
        """
        try:
            # 创建导出目录
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # 准备导出数据
            export_data = {
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "start_time": config.start_time.isoformat() if config.start_time else None,
                    "end_time": config.end_time.isoformat() if config.end_time else None,
                    "config": {
                        "export_metrics": config.export_metrics,
                        "export_component_status": config.export_component_status,
                        "export_status_reports": config.export_status_reports,
                        "export_alerts": config.export_alerts
                    }
                },
                "data": {}
            }
            
            # 导出性能指标
            if config.export_metrics:
                metrics = self.storage.get_metrics_by_time_range(
                    config.start_time,
                    config.end_time
                )
                export_data["data"]["metrics"] = [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "cpu_usage": m.cpu_usage,
                        "memory_usage": m.memory_usage,
                        "disk_usage": m.disk_usage,
                        "network_latency": m.network_latency
                    }
                    for m in metrics
                ]
            
            # 导出组件状态
            if config.export_component_status:
                statuses = self.storage.get_component_status_by_time_range(
                    config.start_time,
                    config.end_time
                )
                export_data["data"]["component_status"] = [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "component": s.component,
                        "status": s.status,
                        "details": s.details
                    }
                    for s in statuses
                ]
            
            # 导出状态报告
            if config.export_status_reports:
                reports = self.storage.get_status_reports_by_time_range(
                    config.start_time,
                    config.end_time
                )
                export_data["data"]["status_reports"] = [
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "overall_status": r.overall_status,
                        "components": r.components,
                        "details": r.details
                    }
                    for r in reports
                ]
            
            # 导出告警记录
            if config.export_alerts:
                alerts = self.storage.get_alerts_by_time_range(
                    config.start_time,
                    config.end_time
                )
                export_data["data"]["alerts"] = [
                    {
                        "id": a.id,
                        "level": a.level.name,
                        "title": a.title,
                        "message": a.message,
                        "timestamp": a.timestamp.isoformat(),
                        "source": a.source,
                        "metadata": a.metadata
                    }
                    for a in alerts
                ]
            
            # 导出数据
            if export_path.endswith('.json'):
                if config.compress:
                    with gzip.open(export_path + '.gz', 'wt', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    with open(export_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif export_path.endswith('.csv'):
                # 为每种数据类型创建单独的CSV文件
                base_path = os.path.splitext(export_path)[0]
                
                if config.export_metrics:
                    self._export_to_csv(
                        base_path + '_metrics.csv',
                        export_data["data"]["metrics"],
                        config.compress
                    )
                
                if config.export_component_status:
                    self._export_to_csv(
                        base_path + '_component_status.csv',
                        export_data["data"]["component_status"],
                        config.compress
                    )
                
                if config.export_status_reports:
                    self._export_to_csv(
                        base_path + '_status_reports.csv',
                        export_data["data"]["status_reports"],
                        config.compress
                    )
                
                if config.export_alerts:
                    self._export_to_csv(
                        base_path + '_alerts.csv',
                        export_data["data"]["alerts"],
                        config.compress
                    )
            
            logger.info(f"数据导出成功: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据导出失败: {str(e)}")
            return False
    
    def import_data(self, import_path: str, config: ImportConfig) -> bool:
        """导入数据
        
        Args:
            import_path: 导入文件路径
            config: 导入配置
            
        Returns:
            bool: 是否导入成功
        """
        try:
            # 读取导入数据
            if import_path.endswith('.json.gz'):
                with gzip.open(import_path, 'rt', encoding='utf-8') as f:
                    import_data = json.load(f)
            elif import_path.endswith('.json'):
                with open(import_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
            elif import_path.endswith('.csv'):
                # 处理CSV文件
                base_path = os.path.splitext(import_path)[0]
                import_data = {
                    "data": {
                        "metrics": self._import_from_csv(base_path + '_metrics.csv'),
                        "component_status": self._import_from_csv(base_path + '_component_status.csv'),
                        "status_reports": self._import_from_csv(base_path + '_status_reports.csv'),
                        "alerts": self._import_from_csv(base_path + '_alerts.csv')
                    }
                }
            else:
                raise ValueError(f"不支持的文件格式: {import_path}")
            
            # 验证数据
            if config.validate_data:
                if not self._validate_import_data(import_data):
                    raise ValueError("数据验证失败")
            
            # 清洗数据
            if config.clean_data:
                import_data = self._clean_import_data(import_data)
            
            # 导入数据
            if "metrics" in import_data["data"]:
                for metric in import_data["data"]["metrics"]:
                    if not config.skip_duplicates or not self._is_duplicate_metric(metric):
                        self.storage.save_metrics(metric)
            
            if "component_status" in import_data["data"]:
                for status in import_data["data"]["component_status"]:
                    if not config.skip_duplicates or not self._is_duplicate_status(status):
                        self.storage.save_component_status(status)
            
            if "status_reports" in import_data["data"]:
                for report in import_data["data"]["status_reports"]:
                    if not config.skip_duplicates or not self._is_duplicate_report(report):
                        self.storage.save_status_report(report)
            
            if "alerts" in import_data["data"]:
                for alert in import_data["data"]["alerts"]:
                    if not config.skip_duplicates or not self._is_duplicate_alert(alert):
                        self.storage.save_alert(alert)
            
            logger.info(f"数据导入成功: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据导入失败: {str(e)}")
            return False
    
    def _export_to_csv(self, file_path: str, data: List[Dict[str, Any]], compress: bool) -> None:
        """导出数据到CSV文件
        
        Args:
            file_path: CSV文件路径
            data: 要导出的数据
            compress: 是否压缩
        """
        if not data:
            return
        
        fieldnames = data[0].keys()
        
        if compress:
            with gzip.open(file_path + '.gz', 'wt', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        else:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
    
    def _import_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """从CSV文件导入数据
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            List[Dict[str, Any]]: 导入的数据
        """
        data = []
        
        if not os.path.exists(file_path):
            if os.path.exists(file_path + '.gz'):
                file_path = file_path + '.gz'
            else:
                return data
        
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                data.extend(list(reader))
        else:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                data.extend(list(reader))
        
        return data
    
    def _validate_import_data(self, data: Dict[str, Any]) -> bool:
        """验证导入数据
        
        Args:
            data: 导入数据
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 验证数据结构
            if "data" not in data:
                return False
            
            # 验证各类数据
            if "metrics" in data["data"]:
                for metric in data["data"]["metrics"]:
                    if not self._validate_metric(metric):
                        return False
            
            if "component_status" in data["data"]:
                for status in data["data"]["component_status"]:
                    if not self._validate_component_status(status):
                        return False
            
            if "status_reports" in data["data"]:
                for report in data["data"]["status_reports"]:
                    if not self._validate_status_report(report):
                        return False
            
            if "alerts" in data["data"]:
                for alert in data["data"]["alerts"]:
                    if not self._validate_alert(alert):
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _clean_import_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗导入数据
        
        Args:
            data: 导入数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        # 清洗各类数据
        if "metrics" in data["data"]:
            data["data"]["metrics"] = [
                self._clean_metric(m)
                for m in data["data"]["metrics"]
            ]
        
        if "component_status" in data["data"]:
            data["data"]["component_status"] = [
                self._clean_component_status(s)
                for s in data["data"]["component_status"]
            ]
        
        if "status_reports" in data["data"]:
            data["data"]["status_reports"] = [
                self._clean_status_report(r)
                for r in data["data"]["status_reports"]
            ]
        
        if "alerts" in data["data"]:
            data["data"]["alerts"] = [
                self._clean_alert(a)
                for a in data["data"]["alerts"]
            ]
        
        return data
    
    def _validate_metric(self, metric: Dict[str, Any]) -> bool:
        """验证性能指标数据
        
        Args:
            metric: 性能指标数据
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ["timestamp", "cpu_usage", "memory_usage", "disk_usage", "network_latency"]
        return all(field in metric for field in required_fields)
    
    def _validate_component_status(self, status: Dict[str, Any]) -> bool:
        """验证组件状态数据
        
        Args:
            status: 组件状态数据
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ["timestamp", "component", "status", "details"]
        return all(field in status for field in required_fields)
    
    def _validate_status_report(self, report: Dict[str, Any]) -> bool:
        """验证状态报告数据
        
        Args:
            report: 状态报告数据
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ["timestamp", "overall_status", "components", "details"]
        return all(field in report for field in required_fields)
    
    def _validate_alert(self, alert: Dict[str, Any]) -> bool:
        """验证告警数据
        
        Args:
            alert: 告警数据
            
        Returns:
            bool: 数据是否有效
        """
        required_fields = ["id", "level", "title", "message", "timestamp", "source"]
        return all(field in alert for field in required_fields)
    
    def _clean_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """清洗性能指标数据
        
        Args:
            metric: 性能指标数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        # 转换数值类型
        metric["cpu_usage"] = float(metric["cpu_usage"])
        metric["memory_usage"] = float(metric["memory_usage"])
        metric["disk_usage"] = float(metric["disk_usage"])
        metric["network_latency"] = float(metric["network_latency"])
        return metric
    
    def _clean_component_status(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """清洗组件状态数据
        
        Args:
            status: 组件状态数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        # 清理字符串
        status["component"] = status["component"].strip()
        status["status"] = status["status"].strip()
        return status
    
    def _clean_status_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """清洗状态报告数据
        
        Args:
            report: 状态报告数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        # 清理字符串
        report["overall_status"] = report["overall_status"].strip()
        return report
    
    def _clean_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """清洗告警数据
        
        Args:
            alert: 告警数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        # 清理字符串
        alert["title"] = alert["title"].strip()
        alert["message"] = alert["message"].strip()
        alert["source"] = alert["source"].strip()
        return alert
    
    def _is_duplicate_metric(self, metric: Dict[str, Any]) -> bool:
        """检查性能指标是否重复
        
        Args:
            metric: 性能指标数据
            
        Returns:
            bool: 是否重复
        """
        existing = self.storage.get_metrics_by_time_range(
            datetime.fromisoformat(metric["timestamp"]),
            datetime.fromisoformat(metric["timestamp"])
        )
        return len(existing) > 0
    
    def _is_duplicate_status(self, status: Dict[str, Any]) -> bool:
        """检查组件状态是否重复
        
        Args:
            status: 组件状态数据
            
        Returns:
            bool: 是否重复
        """
        existing = self.storage.get_component_status_by_time_range(
            datetime.fromisoformat(status["timestamp"]),
            datetime.fromisoformat(status["timestamp"])
        )
        return len(existing) > 0
    
    def _is_duplicate_report(self, report: Dict[str, Any]) -> bool:
        """检查状态报告是否重复
        
        Args:
            report: 状态报告数据
            
        Returns:
            bool: 是否重复
        """
        existing = self.storage.get_status_reports_by_time_range(
            datetime.fromisoformat(report["timestamp"]),
            datetime.fromisoformat(report["timestamp"])
        )
        return len(existing) > 0
    
    def _is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """检查告警是否重复
        
        Args:
            alert: 告警数据
            
        Returns:
            bool: 是否重复
        """
        existing = self.storage.get_alerts_by_time_range(
            datetime.fromisoformat(alert["timestamp"]),
            datetime.fromisoformat(alert["timestamp"])
        )
        return any(e.id == alert["id"] for e in existing) 