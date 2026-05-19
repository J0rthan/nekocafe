"""
数据库连接管理
"""
import logging

logger = logging.getLogger("member")


async def init_db():
    logger.info("Database connection pool initialized (mock)")


async def close_db():
    logger.info("Database connection pool closed (mock)")
