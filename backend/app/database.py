import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

logger = logging.getLogger(__name__)

logger.debug(f"Database URL: {settings.database_url}")

try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    logger.info("✓ SQLAlchemy engine created successfully")
except Exception as e:
    logger.error(f"✗ Failed to create SQLAlchemy engine: {e}")
    raise

try:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✓ SessionLocal factory created successfully")
except Exception as e:
    logger.error(f"✗ Failed to create SessionLocal: {e}")
    raise

Base = declarative_base()
logger.info("✓ Declarative base created successfully")


def get_db():
    """Get database session with logging"""
    logger.debug("Creating new database session...")
    db = SessionLocal()
    try:
        logger.debug("Database session created successfully")
        yield db
    except Exception as e:
        logger.error(f"✗ Error in database session: {e}")
        db.rollback()
        raise
    finally:
        logger.debug("Closing database session...")
        db.close()
