import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from alembic.config import Config
from alembic import command
from loguru import logger

def run_migrations():
    """运行数据库迁移"""
    try:
        # 创建 Alembic 配置
        alembic_cfg = Config("alembic.ini")
        
        # 运行迁移
        command.upgrade(alembic_cfg, "head")
        logger.info("数据库迁移成功完成")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        sys.exit(1)

def rollback_migrations(revision: str = "-1"):
    """回滚数据库迁移
    
    Args:
        revision (str): 要回滚到的版本，默认为上一个版本
    """
    try:
        # 创建 Alembic 配置
        alembic_cfg = Config("alembic.ini")
        
        # 运行回滚
        command.downgrade(alembic_cfg, revision)
        logger.info(f"数据库回滚成功完成，回滚到版本: {revision}")
        
    except Exception as e:
        logger.error(f"数据库回滚失败: {str(e)}")
        sys.exit(1)

def create_migration(message: str):
    """创建新的迁移脚本
    
    Args:
        message (str): 迁移描述信息
    """
    try:
        # 创建 Alembic 配置
        alembic_cfg = Config("alembic.ini")
        
        # 创建迁移脚本
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info(f"创建迁移脚本成功: {message}")
        
    except Exception as e:
        logger.error(f"创建迁移脚本失败: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("action", choices=["upgrade", "downgrade", "create"],
                      help="要执行的操作")
    parser.add_argument("--revision", "-r", default="-1",
                      help="回滚到指定版本 (仅用于 downgrade)")
    parser.add_argument("--message", "-m",
                      help="迁移描述信息 (仅用于 create)")
    
    args = parser.parse_args()
    
    if args.action == "upgrade":
        run_migrations()
    elif args.action == "downgrade":
        rollback_migrations(args.revision)
    elif args.action == "create":
        if not args.message:
            logger.error("创建迁移脚本时必须提供描述信息")
            sys.exit(1)
        create_migration(args.message)

if __name__ == "__main__":
    main() 