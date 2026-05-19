"""
数据库连接管理
"""
import logging

logger = logging.getLogger("reservation")


async def init_db():
    """初始化数据库连接池"""
    logger.info("Database connection pool initialized (mock)")


async def close_db():
    """关闭数据库连接"""
    logger.info("Database connection pool closed (mock)")
