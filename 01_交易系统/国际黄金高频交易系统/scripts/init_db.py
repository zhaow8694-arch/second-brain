import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.db_manager import db_manager
from src.models.database import CREATE_TABLES_SQL
from loguru import logger

async def init_database():
    """初始化数据库"""
    try:
        # 初始化数据库连接
        await db_manager.initialize()
        
        # 创建表
        async with db_manager.get_pg_connection() as conn:
            await conn.execute(CREATE_TABLES_SQL)
            
        logger.info("数据库初始化成功完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        sys.exit(1)
        
    finally:
        # 关闭数据库连接
        await db_manager.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_database()) 