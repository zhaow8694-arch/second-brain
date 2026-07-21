from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from .metrics_collector import SystemMetrics, DataMetrics, CacheMetrics

Base = declarative_base()

class SystemMetricsModel(Base):
    """系统性能指标数据库模型"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    disk_io_read = Column(Float, nullable=False)
    disk_io_write = Column(Float, nullable=False)
    network_io_sent = Column(Float, nullable=False)
    network_io_recv = Column(Float, nullable=False)

class DataMetricsModel(Base):
    """数据处理性能指标数据库模型"""
    __tablename__ = 'data_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    data_type = Column(String, nullable=False)
    records_processed = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=False)
    error_count = Column(Integer, nullable=False)
    avg_record_size = Column(Float, nullable=False)

class CacheMetricsModel(Base):
    """缓存性能指标数据库模型"""
    __tablename__ = 'cache_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    hit_count = Column(Integer, nullable=False)
    miss_count = Column(Integer, nullable=False)
    hit_rate = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    cache_size = Column(Integer, nullable=False)

class MetricsStorage:
    """性能指标存储管理器"""
    
    def __init__(self, db_url: str):
        """初始化性能指标存储管理器
        
        Args:
            db_url: 数据库连接URL
        """
        self.logger = logger.bind(context="metrics_storage")
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def store_system_metrics(self, metrics: SystemMetrics):
        """存储系统性能指标
        
        Args:
            metrics: 系统性能指标
        """
        try:
            session = self.Session()
            try:
                model = SystemMetricsModel(
                    timestamp=metrics.timestamp,
                    cpu_percent=metrics.cpu_percent,
                    memory_percent=metrics.memory_percent,
                    disk_io_read=metrics.disk_io_read,
                    disk_io_write=metrics.disk_io_write,
                    network_io_sent=metrics.network_io_sent,
                    network_io_recv=metrics.network_io_recv
                )
                session.add(model)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"存储系统性能指标时发生错误: {str(e)}")
            raise
            
    def store_data_metrics(self, metrics: DataMetrics):
        """存储数据处理性能指标
        
        Args:
            metrics: 数据处理性能指标
        """
        try:
            session = self.Session()
            try:
                model = DataMetricsModel(
                    timestamp=metrics.timestamp,
                    data_type=metrics.data_type,
                    records_processed=metrics.records_processed,
                    processing_time=metrics.processing_time,
                    error_count=metrics.error_count,
                    avg_record_size=metrics.avg_record_size
                )
                session.add(model)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"存储数据处理性能指标时发生错误: {str(e)}")
            raise
            
    def store_cache_metrics(self, metrics: CacheMetrics):
        """存储缓存性能指标
        
        Args:
            metrics: 缓存性能指标
        """
        try:
            session = self.Session()
            try:
                model = CacheMetricsModel(
                    timestamp=metrics.timestamp,
                    hit_count=metrics.hit_count,
                    miss_count=metrics.miss_count,
                    hit_rate=metrics.hit_rate,
                    memory_usage=metrics.memory_usage,
                    cache_size=metrics.cache_size
                )
                session.add(model)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"存储缓存性能指标时发生错误: {str(e)}")
            raise
            
    def get_system_metrics(self, time_range: Optional[timedelta] = None) -> List[SystemMetrics]:
        """获取系统性能指标历史记录
        
        Args:
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[SystemMetrics]: 系统性能指标历史记录
        """
        try:
            session = self.Session()
            try:
                query = session.query(SystemMetricsModel)
                if time_range:
                    cutoff_time = datetime.now() - time_range
                    query = query.filter(SystemMetricsModel.timestamp > cutoff_time)
                query = query.order_by(SystemMetricsModel.timestamp.desc())
                
                models = query.all()
                return [
                    SystemMetrics(
                        timestamp=m.timestamp,
                        cpu_percent=m.cpu_percent,
                        memory_percent=m.memory_percent,
                        disk_io_read=m.disk_io_read,
                        disk_io_write=m.disk_io_write,
                        network_io_sent=m.network_io_sent,
                        network_io_recv=m.network_io_recv
                    )
                    for m in models
                ]
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"获取系统性能指标时发生错误: {str(e)}")
            raise
            
    def get_data_metrics(self, data_type: Optional[str] = None,
                        time_range: Optional[timedelta] = None) -> List[DataMetrics]:
        """获取数据处理性能指标历史记录
        
        Args:
            data_type: 数据类型过滤
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[DataMetrics]: 数据处理性能指标历史记录
        """
        try:
            session = self.Session()
            try:
                query = session.query(DataMetricsModel)
                if data_type:
                    query = query.filter(DataMetricsModel.data_type == data_type)
                if time_range:
                    cutoff_time = datetime.now() - time_range
                    query = query.filter(DataMetricsModel.timestamp > cutoff_time)
                query = query.order_by(DataMetricsModel.timestamp.desc())
                
                models = query.all()
                return [
                    DataMetrics(
                        timestamp=m.timestamp,
                        data_type=m.data_type,
                        records_processed=m.records_processed,
                        processing_time=m.processing_time,
                        error_count=m.error_count,
                        avg_record_size=m.avg_record_size
                    )
                    for m in models
                ]
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"获取数据处理性能指标时发生错误: {str(e)}")
            raise
            
    def get_cache_metrics(self, time_range: Optional[timedelta] = None) -> List[CacheMetrics]:
        """获取缓存性能指标历史记录
        
        Args:
            time_range: 时间范围，默认为None（返回所有记录）
            
        Returns:
            List[CacheMetrics]: 缓存性能指标历史记录
        """
        try:
            session = self.Session()
            try:
                query = session.query(CacheMetricsModel)
                if time_range:
                    cutoff_time = datetime.now() - time_range
                    query = query.filter(CacheMetricsModel.timestamp > cutoff_time)
                query = query.order_by(CacheMetricsModel.timestamp.desc())
                
                models = query.all()
                return [
                    CacheMetrics(
                        timestamp=m.timestamp,
                        hit_count=m.hit_count,
                        miss_count=m.miss_count,
                        hit_rate=m.hit_rate,
                        memory_usage=m.memory_usage,
                        cache_size=m.cache_size
                    )
                    for m in models
                ]
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"获取缓存性能指标时发生错误: {str(e)}")
            raise
            
    def cleanup_old_metrics(self, days: int = 30):
        """清理旧的性能指标数据
        
        Args:
            days: 保留天数，默认30天
        """
        try:
            session = self.Session()
            try:
                cutoff_time = datetime.now() - timedelta(days=days)
                
                # 清理系统性能指标
                session.query(SystemMetricsModel).filter(
                    SystemMetricsModel.timestamp < cutoff_time
                ).delete()
                
                # 清理数据处理性能指标
                session.query(DataMetricsModel).filter(
                    DataMetricsModel.timestamp < cutoff_time
                ).delete()
                
                # 清理缓存性能指标
                session.query(CacheMetricsModel).filter(
                    CacheMetricsModel.timestamp < cutoff_time
                ).delete()
                
                session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"清理旧的性能指标数据时发生错误: {str(e)}")
            raise 