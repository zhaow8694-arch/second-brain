import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from loguru import logger

from src.config.database import db_settings

class BackupManager:
    """数据库备份管理器"""
    
    def __init__(self, backup_dir: str = "backups"):
        """初始化备份管理器
        
        Args:
            backup_dir: 备份文件存储目录
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_backup_filename(self, prefix: str = "backup") -> str:
        """生成备份文件名
        
        Args:
            prefix: 文件名前缀
            
        Returns:
            备份文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.sql"
    
    def _get_latest_backup(self) -> Optional[Path]:
        """获取最新的备份文件
        
        Returns:
            最新的备份文件路径，如果没有则返回 None
        """
        backup_files = list(self.backup_dir.glob("backup_*.sql"))
        if not backup_files:
            return None
        
        return max(backup_files, key=lambda x: x.stat().st_mtime)
    
    def _get_backup_files(self, days: int = 7) -> List[Path]:
        """获取指定天数内的备份文件
        
        Args:
            days: 天数
            
        Returns:
            备份文件列表
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        return [
            f for f in self.backup_dir.glob("backup_*.sql")
            if f.stat().st_mtime > cutoff_time
        ]
    
    def create_backup(self) -> bool:
        """创建数据库备份
        
        Returns:
            是否备份成功
        """
        try:
            # 生成备份文件名
            backup_file = self.backup_dir / self._get_backup_filename()
            
            # 构建 pg_dump 命令
            cmd = [
                "pg_dump",
                "-h", db_settings.postgres_host,
                "-p", str(db_settings.postgres_port),
                "-U", db_settings.postgres_user,
                "-d", db_settings.postgres_db,
                "-f", str(backup_file)
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.postgres_password
            
            # 执行备份
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"数据库备份失败: {result.stderr}")
                return False
            
            logger.info(f"数据库备份成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            return False
    
    def restore_backup(self, backup_file: Optional[str] = None) -> bool:
        """恢复数据库备份
        
        Args:
            backup_file: 备份文件路径，如果为 None 则使用最新的备份
            
        Returns:
            是否恢复成功
        """
        try:
            # 获取备份文件
            if backup_file is None:
                latest_backup = self._get_latest_backup()
                if latest_backup is None:
                    logger.error("没有找到可用的备份文件")
                    return False
                backup_file = str(latest_backup)
            
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 构建 psql 命令
            cmd = [
                "psql",
                "-h", db_settings.postgres_host,
                "-p", str(db_settings.postgres_port),
                "-U", db_settings.postgres_user,
                "-d", db_settings.postgres_db,
                "-f", backup_file
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.postgres_password
            
            # 执行恢复
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"数据库恢复失败: {result.stderr}")
                return False
            
            logger.info(f"数据库恢复成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"数据库恢复失败: {str(e)}")
            return False
    
    def cleanup_old_backups(self, days: int = 7) -> bool:
        """清理旧的备份文件
        
        Args:
            days: 保留天数
            
        Returns:
            是否清理成功
        """
        try:
            # 获取需要保留的备份文件
            keep_files = self._get_backup_files(days)
            
            # 删除旧文件
            for file in self.backup_dir.glob("backup_*.sql"):
                if file not in keep_files:
                    file.unlink()
                    logger.info(f"删除旧备份文件: {file}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理旧备份文件失败: {str(e)}")
            return False
    
    def list_backups(self) -> List[Path]:
        """列出所有备份文件
        
        Returns:
            备份文件列表
        """
        return list(self.backup_dir.glob("backup_*.sql"))
    
    def get_backup_size(self, backup_file: str) -> Optional[int]:
        """获取备份文件大小
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            文件大小（字节），如果文件不存在则返回 None
        """
        try:
            return os.path.getsize(backup_file)
        except OSError:
            return None
    
    def compress_backup(self, backup_file: str) -> bool:
        """压缩备份文件
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否压缩成功
        """
        try:
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 压缩文件
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, 'rb') as f_in:
                with open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            os.remove(backup_file)
            
            logger.info(f"备份文件压缩成功: {compressed_file}")
            return True
            
        except Exception as e:
            logger.error(f"备份文件压缩失败: {str(e)}")
            return False
    
    def decompress_backup(self, compressed_file: str) -> bool:
        """解压备份文件
        
        Args:
            compressed_file: 压缩的备份文件路径
            
        Returns:
            是否解压成功
        """
        try:
            if not os.path.exists(compressed_file):
                logger.error(f"压缩文件不存在: {compressed_file}")
                return False
            
            # 解压文件
            backup_file = compressed_file[:-3]  # 移除 .gz 后缀
            with open(compressed_file, 'rb') as f_in:
                with open(backup_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除压缩文件
            os.remove(compressed_file)
            
            logger.info(f"备份文件解压成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"备份文件解压失败: {str(e)}")
            return False 