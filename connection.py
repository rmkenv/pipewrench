from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
import pymongo
import redis

# PostgreSQL Database
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB connection for document storage
mongo_client = pymongo.MongoClient(settings.mongodb_url)
mongo_db = mongo_client[settings.mongodb_db_name]

# Redis connection for caching and session management
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_db():
    return mongo_db

def get_redis_client():
    return redis_client

# Create tables
from models.database import Base

def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)
