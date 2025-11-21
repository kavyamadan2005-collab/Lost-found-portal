import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

logger = logging.getLogger(__name__)

logger.debug(f"Database URL: {settings.database_url}")

engine = None
SessionLocal = None

try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    logger.info("✓ SQLAlchemy engine created successfully")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✓ SessionLocal factory created successfully")
except ImportError as e:
    logger.warning(f"⚠ Database driver not available yet (psycopg2): {e}")
    logger.warning("  This is normal if PostgreSQL driver is still installing")
    # Create dummy engine that will fail gracefully later
    engine = None
    SessionLocal = None
except Exception as e:
    logger.warning(f"⚠ Database connection issue (will retry on requests): {e}")
    engine = None
    SessionLocal = None

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
