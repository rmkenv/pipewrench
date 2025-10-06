
"""Database connection management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymongo
import redis
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# PostgreSQL Database
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("PostgreSQL connection configured")
except Exception as e:
    logger.error(f"Failed to configure PostgreSQL: {e}")
    raise

# MongoDB connection for document storage
try:
    mongo_client = pymongo.MongoClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000
    )
    # Test connection
    mongo_client.server_info()
    mongo_db = mongo_client[settings.mongodb_db_name]
    logger.info("MongoDB connection established")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}. Document storage may not work.")
    mongo_client = None
    mongo_db = None

# Redis connection for caching and session management
try:
    redis_client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching may not work.")
    redis_client = None


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_mongo_db():
    """Get MongoDB database instance."""
    if mongo_db is None:
        raise RuntimeError("MongoDB is not available")
    return mongo_db


def get_redis_client():
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis is not available")
    return redis_client


def create_tables():
    """Create all database tables."""
    try:
        from models.database import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
